from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.enki_model_use import JsonEnkiModelUseRepository
from nks.adapters.governed_transactions import JsonGovernedTransactionRepository
from nks.application.enki_model_use_execution import (
    build_model_use_operation_plan,
    execute_governed_enki_model_use,
)
from nks.application.enki_model_use_policy import (
    NoEffectTestModelDispatcher,
    build_enki_model_use_package,
)
from nks.application.governed_transactions import (
    GovernedTransactionExecutor,
    TransactionStage,
    TransactionTerminalState,
)
from nks.enki.contracts import ConfidenceAssertion, ConfidenceLevel, SubjectRef
from nks.enki.model_use_contracts import (
    EnkiModelUseDirective,
    EnkiModelUseItem,
    EnkiModelUseRequest,
    ModelUseAudience,
    ModelUseConsentState,
    ModelUseDirectiveAction,
    ModelUseItemKind,
    ModelUseSensitivity,
    ModelUseTemporalState,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


def _package_and_request():
    subject = SubjectRef(subject_id="PROJECT-1", subject_type="PROJECT")
    item = EnkiModelUseItem(
        item_id="FINDING-1",
        item_kind=ModelUseItemKind.FINDING,
        subject=subject,
        domain="delivery",
        content_sha256=_hash("finding"),
        context=["release-candidate"],
        temporal_state=ModelUseTemporalState.CURRENT,
        confidence=ConfidenceAssertion(
            level=ConfidenceLevel.HIGH,
            rationale="TEST evidence supports the finding.",
            evidence_ids=["EVIDENCE-1"],
        ),
        sensitivity=ModelUseSensitivity.INTERNAL,
        consent_state=ModelUseConsentState.NOT_REQUIRED,
        allowed_purposes={"internal-validation"},
        provenance_classification="SYNTHETIC",
    )
    directive = EnkiModelUseDirective(
        directive_id="DIRECTIVE-1",
        action=ModelUseDirectiveAction.INCLUDE,
        item_id=item.item_id,
        item_kind=item.item_kind,
        subject=subject,
        domain=item.domain,
        purpose="internal-validation",
        audience=ModelUseAudience.INTERNAL_MODEL,
        required_context={"release-candidate"},
        rationale="Use the exact finding for internal validation.",
        issued_by="HUMAN-ORIGIN-AUTHORITY",
        authority_class="HUMAN_ORIGIN_AUTHORITY",
        issued_at=_now() - timedelta(minutes=5),
    )
    request = EnkiModelUseRequest(
        package_id="PACKAGE-1",
        subject=subject,
        domain=item.domain,
        purpose="internal-validation",
        audience=ModelUseAudience.INTERNAL_MODEL,
        context={"release-candidate"},
        execution_context=ExecutionContext.TEST,
        items=[item],
        directives=[directive],
        requested_at=_now(),
        package_version="enki-model-use/v1",
    )
    return build_enki_model_use_package(request), request


def _grant(package, transaction_id: str) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id="APPROVAL-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={"enki:model-use"},
        subject_id=package.subject.subject_id,
        content_sha256=package.package_sha256,
        authorized_by="HUMAN-ORIGIN-AUTHORITY",
        authority_class="HUMAN_ORIGIN_AUTHORITY",
        issued_at=_now() - timedelta(minutes=10),
        expires_at=_now() + timedelta(hours=1),
        metadata={"transaction_id": transaction_id},
    )


def _executor(tmp_path):
    approvals = JsonApprovalGrantRepository(tmp_path)
    transactions = JsonGovernedTransactionRepository(tmp_path)
    return approvals, transactions, GovernedTransactionExecutor(
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )


def test_operation_plan_binds_exact_package_and_context() -> None:
    package, _request = _package_and_request()
    plan = build_model_use_operation_plan(
        package,
        transaction_id="TX-1",
        acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
    )
    assert plan.action == "enki:model-use"
    assert plan.subject_id == package.subject.subject_id
    assert plan.content_sha256 == package.package_sha256
    assert plan.execution_context == ExecutionContext.TEST
    assert plan.metadata["context_sha256"] == package.context_sha256


def test_governed_model_use_consumes_authority_and_commits_no_effect_receipt(tmp_path) -> None:
    package, request = _package_and_request()
    approvals, transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(package, "TX-1"))
    repository = JsonEnkiModelUseRepository(tmp_path)

    result = execute_governed_enki_model_use(
        package,
        request=request,
        transaction_id="TX-1",
        approval_id="APPROVAL-1",
        acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
        transaction_executor=executor,
        dispatcher=NoEffectTestModelDispatcher(),
        repository=repository,
        revocation_repository=repository,
        now=_now(),
    )

    assert result.transaction_receipt.terminal_state == TransactionTerminalState.COMMITTED
    assert result.effect.external_effect is False
    assert approvals.get_approval("APPROVAL-1").consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert repository.get_package(package.package_id) == package
    assert transactions.get_receipt("TX-1") == result.transaction_receipt


def test_exact_retry_returns_same_effect_without_duplicate_dispatch(tmp_path) -> None:
    package, request = _package_and_request()
    approvals, _transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(package, "TX-1"))
    repository = JsonEnkiModelUseRepository(tmp_path)

    first = execute_governed_enki_model_use(
        package,
        request=request,
        transaction_id="TX-1",
        approval_id="APPROVAL-1",
        acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
        transaction_executor=executor,
        dispatcher=NoEffectTestModelDispatcher(),
        repository=repository,
        revocation_repository=repository,
        now=_now(),
    )
    retry = execute_governed_enki_model_use(
        package,
        request=request,
        transaction_id="TX-1",
        approval_id="APPROVAL-1",
        acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
        transaction_executor=executor,
        dispatcher=NoEffectTestModelDispatcher(),
        repository=repository,
        revocation_repository=repository,
        now=_now(),
    )

    assert retry.effect == first.effect
    assert retry.transaction_receipt.exact_retry is True
    assert len(list((tmp_path / "records" / "enki-model-use-effects").glob("*.json"))) == 1


def test_failure_before_consumption_releases_reservation_and_rolls_back(tmp_path) -> None:
    package, request = _package_and_request()
    approvals, transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(package, "TX-1"))
    repository = JsonEnkiModelUseRepository(tmp_path)

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.APPROVAL_RESERVED:
            raise RuntimeError("injected-before-consumption")

    with pytest.raises(RuntimeError, match="injected-before-consumption"):
        execute_governed_enki_model_use(
            package,
            request=request,
            transaction_id="TX-1",
            approval_id="APPROVAL-1",
            acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
            transaction_executor=executor,
            dispatcher=NoEffectTestModelDispatcher(),
            repository=repository,
            revocation_repository=repository,
            now=_now(),
            failure_hook=fail,
        )

    assert approvals.get_approval("APPROVAL-1").consumption_status == ApprovalConsumptionStatus.AVAILABLE
    assert transactions.get_receipt("TX-1").terminal_state == TransactionTerminalState.ROLLED_BACK
    assert repository.get_package(package.package_id) is None


def test_failure_after_consumption_recovers_by_exact_retry(tmp_path) -> None:
    package, request = _package_and_request()
    approvals, transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(package, "TX-1"))
    repository = JsonEnkiModelUseRepository(tmp_path)

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.APPROVAL_CONSUMED:
            raise RuntimeError("injected-after-consumption")

    with pytest.raises(RuntimeError, match="injected-after-consumption"):
        execute_governed_enki_model_use(
            package,
            request=request,
            transaction_id="TX-1",
            approval_id="APPROVAL-1",
            acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
            transaction_executor=executor,
            dispatcher=NoEffectTestModelDispatcher(),
            repository=repository,
            revocation_repository=repository,
            now=_now(),
            failure_hook=fail,
        )

    assert approvals.get_approval("APPROVAL-1").consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert transactions.get_receipt("TX-1") is None

    recovered = execute_governed_enki_model_use(
        package,
        request=request,
        transaction_id="TX-1",
        approval_id="APPROVAL-1",
        acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
        transaction_executor=executor,
        dispatcher=NoEffectTestModelDispatcher(),
        repository=repository,
        revocation_repository=repository,
        now=_now(),
    )
    assert recovered.transaction_receipt.terminal_state == TransactionTerminalState.RECOVERED
    assert recovered.transaction_receipt.exact_retry is True
    assert recovered.effect.external_effect is False


def test_mismatched_approval_hash_fails_closed_without_effect(tmp_path) -> None:
    package, request = _package_and_request()
    approvals, _transactions, executor = _executor(tmp_path)
    grant = _grant(package, "TX-1").model_copy(update={"content_sha256": _hash("wrong")})
    approvals.save_new(grant)
    repository = JsonEnkiModelUseRepository(tmp_path)

    with pytest.raises(PermissionError):
        execute_governed_enki_model_use(
            package,
            request=request,
            transaction_id="TX-1",
            approval_id="APPROVAL-1",
            acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
            transaction_executor=executor,
            dispatcher=NoEffectTestModelDispatcher(),
            repository=repository,
            revocation_repository=repository,
            now=_now(),
        )
    assert repository.get_package(package.package_id) is None
    assert repository.get_effect("EFFECT-TX-1") is None
