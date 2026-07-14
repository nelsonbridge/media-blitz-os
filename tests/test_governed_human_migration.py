from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.enki_state import JsonEnkiStateRepository
from nks.adapters.governed_transactions import JsonGovernedTransactionRepository
from nks.application.governed_human_migration import (
    ConsentState,
    ExecuteGovernedHumanMigration,
    GovernedHumanMigrationPlan,
    HumanMigrationProtectionPolicy,
    HumanMigrationSource,
    PrivacyClassification,
)
from nks.application.governed_transactions import TransactionTerminalState
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    HumanStateTransition,
    TemporalStatus,
    TransitionOrigin,
    TransitionType,
)
from nks.enki.contracts import ExpressionOrigin
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc)


def _observation(
    observation_id: str,
    content: str,
    *,
    status: TemporalStatus = TemporalStatus.CURRENT,
) -> HumanStateObservation:
    return HumanStateObservation(
        observation_id=observation_id,
        subject_id="PERSON-1",
        content=content,
        content_hash=_hash(content),
        domain="career",
        state_type="objective",
        provenance="REAL",
        source_id=f"SOURCE-{observation_id}",
        observed_at=_now(),
        effective_from=date(2026, 7, 14),
        context=["current-role"],
        expression_strength=ExpressionStrength.EXPLICIT,
        confidence="HIGH",
        temporal_status=status,
    )


def _transition() -> HumanStateTransition:
    return HumanStateTransition(
        transition_id="HTR-1",
        subject_id="PERSON-1",
        domain="career",
        from_observation_id="HOBS-1",
        to_observation_id="HOBS-2",
        transition_type=TransitionType.REFINEMENT,
        origin=TransitionOrigin.HUMAN_REVIEWED,
        detected_at=_now(),
        stated_reason="The objective was clarified.",
        durability="persistent",
        reversibility="revisable",
        confidence="HIGH",
        approved_for_model_feedback=True,
        approved_by="LEGACY-STEWARD",
    )


def _source() -> HumanMigrationSource:
    return HumanMigrationSource(
        observations=[
            _observation("HOBS-1", "I intend to pursue promotion."),
            _observation("HOBS-2", "I intend to pursue an operations role."),
        ],
        transitions=[_transition()],
        expression_origins={
            "HOBS-1": ExpressionOrigin.SELF_DECLARED,
            "HOBS-2": ExpressionOrigin.SELF_DECLARED,
        },
    )


def _policy(
    *,
    consent: ConsentState = ConsentState.GRANTED,
    purposes: set[str] | None = None,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> HumanMigrationProtectionPolicy:
    return HumanMigrationProtectionPolicy(
        policy_id="HMP-1",
        subject_id="PERSON-1",
        consent_state=consent,
        allowed_purposes=purposes or {"canonical-migration"},
        privacy_classification=PrivacyClassification.PRIVATE,
        approved_by="PERSON-1",
        approved_at=_now() - timedelta(minutes=10),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def _plan(
    *,
    policy: HumanMigrationProtectionPolicy | None = None,
    source: HumanMigrationSource | None = None,
) -> GovernedHumanMigrationPlan:
    return GovernedHumanMigrationPlan.create(
        migration_id="MIG-1",
        transaction_id="TX-MIG-1",
        purpose="canonical-migration",
        policy=policy or _policy(),
        source=source or _source(),
        execution_context=ExecutionContext.TEST,
        acceptable_authority_classes={"SUBJECT"},
        requested_at=_now(),
    )


def _grant(plan: GovernedHumanMigrationPlan) -> ApprovalGrant:
    operation = plan.state_write_plan.operation
    return ApprovalGrant(
        approval_id="APR-MIG-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={operation.action},
        subject_id=operation.subject_id,
        content_sha256=operation.content_sha256,
        authorized_by="PERSON-1",
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=5),
        expires_at=_now() + timedelta(hours=1),
    )


def _service(tmp_path, plan: GovernedHumanMigrationPlan):
    approvals = JsonApprovalGrantRepository(tmp_path)
    approvals.save_new(_grant(plan))
    transactions = JsonGovernedTransactionRepository(tmp_path)
    state = JsonEnkiStateRepository(tmp_path)
    service = ExecuteGovernedHumanMigration(
        state_writer=state,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )
    return service, approvals, transactions, state


def test_human_migration_preserves_semantics_and_excludes_legacy_authority(
    tmp_path,
) -> None:
    plan = _plan()
    plan.assert_semantic_parity()
    service, approvals, transactions, state = _service(tmp_path, plan)

    receipt = service.execute(plan, approval_id="APR-MIG-1", now=_now())

    assert receipt.terminal_state == TransactionTerminalState.COMMITTED
    assert receipt.operation_id == "human-state-migration"
    assert approvals.get_approval(
        "APR-MIG-1"
    ).consumption_status == ApprovalConsumptionStatus.CONSUMED
    observation = state.get_observation("HOBS-1")
    assert observation is not None
    assert observation.statement == "I intend to pursue promotion."
    assert observation.expression_origin == ExpressionOrigin.SELF_DECLARED
    assert observation.metadata["privacy_classification"] == "PRIVATE"
    relationship = state.get_relationship("HTR-1")
    assert relationship is not None
    assert "approved_for_model_feedback" not in relationship.metadata
    assert "approved_by" not in relationship.metadata
    assert transactions.get_receipt("TX-MIG-1") == receipt


def test_human_migration_partial_write_recovers_exactly(tmp_path) -> None:
    plan = _plan()
    service, approvals, _, state = _service(tmp_path, plan)

    def fail(boundary: str) -> None:
        if boundary == "after-observations":
            raise OSError("migration interrupted")

    with pytest.raises(OSError, match="migration interrupted"):
        service.execute(
            plan,
            approval_id="APR-MIG-1",
            now=_now(),
            state_write_failure_hook=fail,
        )

    assert state.get_observation("HOBS-1") is not None
    assert state.get_relationship("HTR-1") is None
    assert approvals.get_approval(
        "APR-MIG-1"
    ).consumption_status == ApprovalConsumptionStatus.CONSUMED

    recovered = service.execute(plan, approval_id="APR-MIG-1", now=_now())

    assert recovered.terminal_state == TransactionTerminalState.RECOVERED
    assert recovered.exact_retry is True
    assert state.get_relationship("HTR-1") is not None


@pytest.mark.parametrize(
    ("policy", "message"),
    [
        (_policy(consent=ConsentState.DENIED), "consent state is DENIED"),
        (_policy(consent=ConsentState.UNKNOWN), "consent state is UNKNOWN"),
        (_policy(purposes={"evaluation-only"}), "purpose is not allowed"),
        (
            _policy(expires_at=_now() - timedelta(seconds=1)),
            "policy is expired",
        ),
        (
            _policy(revoked_at=_now() - timedelta(seconds=1)),
            "policy is revoked",
        ),
    ],
)
def test_human_migration_policy_fails_closed(
    policy: HumanMigrationProtectionPolicy,
    message: str,
) -> None:
    with pytest.raises(PermissionError, match=message):
        _plan(policy=policy)


def test_migration_requires_explicit_origin_for_every_observation() -> None:
    with pytest.raises(ValidationError, match="missing expression origins: HOBS-2"):
        HumanMigrationSource(
            observations=_source().observations,
            transitions=_source().transitions,
            expression_origins={"HOBS-1": ExpressionOrigin.SELF_DECLARED},
        )


def test_migration_rejects_unknown_transition_endpoint() -> None:
    bad_transition = _transition().model_copy(
        update={"to_observation_id": "MISSING"}
    )
    with pytest.raises(ValidationError, match="unknown target observation"):
        HumanMigrationSource(
            observations=_source().observations,
            transitions=[bad_transition],
            expression_origins=_source().expression_origins,
        )


def test_semantic_parity_detects_projection_tampering() -> None:
    plan = _plan()
    tampered_observation = plan.state_write_plan.payload.observations[0].model_copy(
        update={"statement": "Altered historical meaning"}
    )
    tampered_payload = plan.state_write_plan.payload.model_copy(
        update={
            "observations": [
                tampered_observation,
                plan.state_write_plan.payload.observations[1],
            ]
        }
    )
    tampered_write_plan = plan.state_write_plan.model_copy(
        update={"payload": tampered_payload}
    )
    tampered = plan.model_copy(update={"state_write_plan": tampered_write_plan})

    with pytest.raises(RuntimeError, match="semantic parity failed.*content"):
        tampered.assert_semantic_parity()
