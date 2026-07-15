from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.governed_transactions import JsonGovernedTransactionRepository
from nks.adapters.policy_lifecycle import JsonPolicyRepository, PolicyRecordConflict
from nks.application.governed_transactions import GovernedTransactionExecutor, canonical_sha256
from nks.application.policy_lifecycle import (
    ExecutePolicyLifecycle,
    PolicyBundle,
    PolicyEffect,
    PolicyEvaluationCase,
    PolicyLifecycleAction,
    PolicyOperator,
    PolicyRule,
    attribute_historical_decision,
    compare_policies,
    evaluate_policy,
    simulate_policy,
)
from nks.governance.approvals import ApprovalDecision, ApprovalGrant, ExecutionContext
from nks.governance.boundaries import BoundaryContext


def _now() -> datetime:
    return datetime(2026, 7, 15, 4, 0, tzinfo=timezone.utc)


def _boundary(context: ExecutionContext = ExecutionContext.TEST) -> BoundaryContext:
    return BoundaryContext(
        namespace_id="NKS-TEST",
        tenant_id="TENANT-A",
        subject_id="POLICY-SUBJECT",
        domain="governance",
        audience="internal",
        execution_context=context,
    )


def _rule(
    rule_id: str,
    *,
    attribute: str,
    expected: object,
    effect: PolicyEffect,
    priority: int,
) -> PolicyRule:
    return PolicyRule(
        rule_id=rule_id,
        attribute=attribute,
        operator=PolicyOperator.EQUALS,
        expected=expected,
        effect=effect,
        priority=priority,
    )


def _bundle(
    version: int,
    *,
    previous: PolicyBundle | None = None,
    boundary: BoundaryContext | None = None,
    public_effect: PolicyEffect = PolicyEffect.DENY,
) -> PolicyBundle:
    return PolicyBundle.create(
        policy_id="POLICY-1",
        version=version,
        boundary=boundary or _boundary(),
        authored_by="TEST-GOVERNOR",
        authored_at=_now() + timedelta(minutes=version),
        previous_bundle_sha256=previous.bundle_sha256 if previous else None,
        rules=[
            _rule(
                "DENY-PUBLIC",
                attribute="audience",
                expected="public",
                effect=public_effect,
                priority=10,
            ),
            _rule(
                "ALLOW-INTERNAL",
                attribute="audience",
                expected="internal",
                effect=PolicyEffect.ALLOW,
                priority=20,
            ),
        ],
        default_effect=PolicyEffect.REQUIRE_REVIEW,
    )


def _service(tmp_path):
    approvals = JsonApprovalGrantRepository(tmp_path)
    transactions = JsonGovernedTransactionRepository(tmp_path)
    policies = JsonPolicyRepository(tmp_path)
    executor = GovernedTransactionExecutor(
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )
    return ExecutePolicyLifecycle(executor, policies), approvals, policies, transactions


def _save_approval(
    approvals: JsonApprovalGrantRepository,
    *,
    action: PolicyLifecycleAction,
    bundle: PolicyBundle | None,
    transaction_id: str,
) -> str:
    boundary = bundle.boundary if bundle else _boundary()
    policy_id = bundle.policy_id if bundle else "POLICY-1"
    content = {
        "action": action,
        "policy_id": policy_id,
        "boundary": boundary,
        "bundle_sha256": bundle.bundle_sha256 if bundle else None,
    }
    approval_id = f"APR-{transaction_id}"
    approvals.save_new(
        ApprovalGrant(
            approval_id=approval_id,
            decision=ApprovalDecision.APPROVED,
            execution_context=ExecutionContext.TEST,
            permitted_actions={f"policy:{action.value.lower()}"},
            subject_id=policy_id,
            content_sha256=canonical_sha256(content),
            authorized_by="TEST-GOVERNOR",
            authority_class="POLICY-GOVERNOR",
            issued_at=_now() - timedelta(minutes=1),
            expires_at=_now() + timedelta(hours=1),
        )
    )
    return approval_id


def _execute(service, approvals, action, bundle, transaction_id):
    approval_id = _save_approval(
        approvals,
        action=action,
        bundle=bundle,
        transaction_id=transaction_id,
    )
    return service.execute(
        action=action,
        policy_id="POLICY-1",
        boundary=bundle.boundary if bundle else _boundary(),
        approval_id=approval_id,
        transaction_id=transaction_id,
        requested_at=_now(),
        acceptable_authority_classes={"POLICY-GOVERNOR"},
        bundle=bundle,
    )


def test_policy_bundles_are_immutable_hash_bound_and_version_linked() -> None:
    first = _bundle(1)
    second = _bundle(2, previous=first, public_effect=PolicyEffect.REQUIRE_REVIEW)

    assert first.previous_bundle_sha256 is None
    assert second.previous_bundle_sha256 == first.bundle_sha256
    assert first.bundle_sha256 != second.bundle_sha256

    with pytest.raises(ValidationError, match="predecessor"):
        _bundle(2)
    with pytest.raises(ValidationError, match="policy bundle hash is invalid"):
        PolicyBundle.model_validate(
            second.model_dump(mode="python") | {"bundle_sha256": "sha256:" + "0" * 64}
        )


def test_comparison_and_simulation_are_deterministic_and_side_effect_free() -> None:
    first = _bundle(1)
    second = _bundle(2, previous=first, public_effect=PolicyEffect.REQUIRE_REVIEW)
    comparison = compare_policies(first, second)
    cases = [
        PolicyEvaluationCase(case_id="PUBLIC", attributes={"audience": "public"}),
        PolicyEvaluationCase(case_id="INTERNAL", attributes={"audience": "internal"}),
        PolicyEvaluationCase(case_id="UNKNOWN", attributes={"audience": "partner"}),
    ]
    report = simulate_policy(second, cases, baseline=first)

    assert comparison.changed_rule_ids == ["DENY-PUBLIC"]
    assert comparison.added_rule_ids == []
    assert comparison.removed_rule_ids == []
    assert report.changed_case_ids == ["PUBLIC"]
    assert report.canonical_state_mutated is False
    assert report.execution_context == ExecutionContext.TEST
    assert report == simulate_policy(second, cases, baseline=first)


def test_policy_evaluation_is_priority_ordered_and_defaults_explicitly() -> None:
    bundle = _bundle(1)
    assert evaluate_policy(
        bundle,
        PolicyEvaluationCase(case_id="I", attributes={"audience": "internal"}),
    ).effect == PolicyEffect.ALLOW
    assert evaluate_policy(
        bundle,
        PolicyEvaluationCase(case_id="P", attributes={"audience": "public"}),
    ).effect == PolicyEffect.DENY
    assert evaluate_policy(
        bundle,
        PolicyEvaluationCase(case_id="U", attributes={}),
    ).effect == PolicyEffect.REQUIRE_REVIEW


def test_approval_bound_activation_rollback_retirement_and_historical_attribution(tmp_path) -> None:
    service, approvals, policies, transactions = _service(tmp_path)
    first = _bundle(1)
    second = _bundle(2, previous=first, public_effect=PolicyEffect.REQUIRE_REVIEW)

    activated_first = _execute(
        service, approvals, PolicyLifecycleAction.ACTIVATE, first, "TX-POL-1"
    )
    activated_second = _execute(
        service, approvals, PolicyLifecycleAction.ACTIVATE, second, "TX-POL-2"
    )
    rolled_back = _execute(
        service, approvals, PolicyLifecycleAction.ROLLBACK, first, "TX-POL-3"
    )

    assert activated_first.output_sha256
    assert activated_second.output_sha256
    assert rolled_back.output_sha256
    assert policies.get_active_bundle("POLICY-1", _boundary()) == first
    activations = policies.list_activations("POLICY-1")
    historical = attribute_historical_decision(
        policies,
        policy_id="POLICY-1",
        activation_id=activations[1].activation_id,
    )
    assert historical == second
    assert transactions.get_receipt("TX-POL-3") == rolled_back

    retired = _execute(
        service, approvals, PolicyLifecycleAction.RETIRE, None, "TX-POL-4"
    )
    assert retired.output_sha256
    assert policies.get_active_bundle("POLICY-1", _boundary()) is None
    assert len(policies.list_bundles("POLICY-1")) == 2


def test_exact_retry_reuses_receipt_and_does_not_duplicate_activation(tmp_path) -> None:
    service, approvals, policies, _ = _service(tmp_path)
    bundle = _bundle(1)
    approval_id = _save_approval(
        approvals,
        action=PolicyLifecycleAction.ACTIVATE,
        bundle=bundle,
        transaction_id="TX-RETRY",
    )
    arguments = dict(
        action=PolicyLifecycleAction.ACTIVATE,
        policy_id="POLICY-1",
        boundary=_boundary(),
        approval_id=approval_id,
        transaction_id="TX-RETRY",
        requested_at=_now(),
        acceptable_authority_classes={"POLICY-GOVERNOR"},
        bundle=bundle,
    )
    first = service.execute(**arguments)
    retried = service.execute(**arguments)

    assert retried.receipt_id == first.receipt_id
    assert retried.exact_retry is True
    assert len(policies.list_activations("POLICY-1")) == 1


def test_test_simulation_and_lifecycle_cannot_activate_production_policy(tmp_path) -> None:
    production = _bundle(1, boundary=_boundary(ExecutionContext.PRODUCTION))
    cases = [PolicyEvaluationCase(case_id="P", attributes={"audience": "public"})]
    with pytest.raises(ValueError, match="TEST simulation"):
        simulate_policy(production, cases)

    service, approvals, _, _ = _service(tmp_path)
    approval_id = _save_approval(
        approvals,
        action=PolicyLifecycleAction.ACTIVATE,
        bundle=production,
        transaction_id="TX-PROD",
    )
    with pytest.raises(ValueError, match="TEST-only"):
        service.execute(
            action=PolicyLifecycleAction.ACTIVATE,
            policy_id="POLICY-1",
            boundary=production.boundary,
            approval_id=approval_id,
            transaction_id="TX-PROD",
            requested_at=_now(),
            acceptable_authority_classes={"POLICY-GOVERNOR"},
            bundle=production,
        )


def test_append_only_repository_rejects_divergent_identity_conflicts(tmp_path) -> None:
    policies = JsonPolicyRepository(tmp_path)
    bundle = _bundle(1)
    policies.append_bundle(bundle)
    policies.append_bundle(bundle)

    path = next((tmp_path / "records" / "policy-bundles").glob("*.json"))
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(PolicyRecordConflict):
        policies.append_bundle(bundle)
