from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.enki_state import JsonEnkiStateRepository
from nks.adapters.governed_transactions import JsonGovernedTransactionRepository
from nks.application.governed_state_write import (
    ExecuteGovernedStateWrite,
    GovernedStateWritePlan,
)
from nks.application.governed_transactions import TransactionTerminalState
from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    EvidenceRef,
    ExpressionOrigin,
    Observation,
    ReferenceKind,
    RelationshipAssertion,
    SubjectRef,
    TemporalApplicability,
    TemporalStatus,
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
    return datetime(2026, 7, 14, 7, 0, tzinfo=timezone.utc)


def _observation(
    observation_id: str,
    subject: SubjectRef,
    *,
    statement: str | None = None,
) -> Observation:
    content = statement or f"statement {observation_id}"
    evidence_id = f"E-{observation_id}"
    return Observation(
        observation_id=observation_id,
        subject=subject,
        domain="operations",
        statement=content,
        content_hash=_hash(content),
        evidence=[
            EvidenceRef(
                evidence_id=evidence_id,
                source_id=f"S-{observation_id}",
                content_hash=_hash(f"source {observation_id}"),
                observed_at=_now(),
                provenance_classification="REAL",
            )
        ],
        observed_at=_now(),
        applicability=TemporalApplicability(effective_from=date(2026, 7, 14)),
        expression_origin=ExpressionOrigin.OBSERVED,
        confidence=ConfidenceAssertion(
            level=ConfidenceLevel.HIGH,
            rationale="test evidence",
            evidence_ids=[evidence_id],
        ),
        temporal_status=TemporalStatus.CURRENT,
    )


def _relationship(subject: SubjectRef) -> RelationshipAssertion:
    return RelationshipAssertion(
        relationship_id="REL-1",
        subject=subject,
        domain="operations",
        source_kind=ReferenceKind.OBSERVATION,
        source_id="OBS-1",
        target_kind=ReferenceKind.OBSERVATION,
        target_id="OBS-2",
        relationship_type="SUPPORTS",
        confidence=ConfidenceAssertion(
            level=ConfidenceLevel.MODERATE,
            rationale="test relationship",
        ),
        observed_at=_now(),
        applicability=TemporalApplicability(effective_from=date(2026, 7, 14)),
    )


def _plan(subject_type: str, transaction_id: str = "TX-STATE-1") -> GovernedStateWritePlan:
    subject = SubjectRef(subject_id=f"{subject_type}-1", subject_type=subject_type)
    return GovernedStateWritePlan.create(
        transaction_id=transaction_id,
        subject=subject,
        domain="operations",
        observations=[
            _observation("OBS-1", subject),
            _observation("OBS-2", subject),
        ],
        relationships=[_relationship(subject)],
        known_observation_ids=set(),
        execution_context=ExecutionContext.TEST,
        acceptable_authority_classes={"SUBJECT"},
        requested_at=_now(),
    )


def _grant(plan: GovernedStateWritePlan) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id=f"APR-{plan.operation.transaction_id}",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={plan.operation.action},
        subject_id=plan.operation.subject_id,
        content_sha256=plan.operation.content_sha256,
        authorized_by=plan.operation.subject_id,
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=1),
        expires_at=_now() + timedelta(hours=1),
    )


def _service(tmp_path, plan: GovernedStateWritePlan):
    approval_repository = JsonApprovalGrantRepository(tmp_path)
    approval_repository.save_new(_grant(plan))
    transaction_repository = JsonGovernedTransactionRepository(tmp_path)
    state_repository = JsonEnkiStateRepository(tmp_path)
    service = ExecuteGovernedStateWrite(
        state_writer=state_repository,
        approval_repository=approval_repository,
        journal=transaction_repository,
        receipt_repository=transaction_repository,
    )
    return service, approval_repository, transaction_repository, state_repository


@pytest.mark.parametrize("subject_type", ["PERSON", "ORGANIZATION", "PROJECT"])
def test_governed_state_write_reuses_identical_contracts_across_subjects(
    tmp_path,
    subject_type: str,
) -> None:
    plan = _plan(subject_type)
    service, approvals, transactions, state = _service(tmp_path, plan)

    receipt = service.execute(
        plan,
        approval_id=f"APR-{plan.operation.transaction_id}",
        now=_now(),
    )

    assert receipt.terminal_state == TransactionTerminalState.COMMITTED
    assert approvals.get_approval(
        f"APR-{plan.operation.transaction_id}"
    ).consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert state.get_observation("OBS-1") == plan.payload.observations[0]
    assert state.get_relationship("REL-1") == plan.payload.relationships[0]
    assert transactions.get_receipt(plan.operation.transaction_id) == receipt


def test_partial_state_write_recovers_through_exact_retry(tmp_path) -> None:
    plan = _plan("PERSON")
    service, approvals, _, state = _service(tmp_path, plan)

    def fail(boundary: str) -> None:
        if boundary == "after-observations":
            raise OSError("injected partial write")

    with pytest.raises(OSError, match="partial write"):
        service.execute(
            plan,
            approval_id=f"APR-{plan.operation.transaction_id}",
            now=_now(),
            state_write_failure_hook=fail,
        )

    assert state.get_observation("OBS-1") is not None
    assert state.get_relationship("REL-1") is None
    assert approvals.get_approval(
        f"APR-{plan.operation.transaction_id}"
    ).consumption_status == ApprovalConsumptionStatus.CONSUMED

    recovered = service.execute(
        plan,
        approval_id=f"APR-{plan.operation.transaction_id}",
        now=_now(),
    )

    assert recovered.terminal_state == TransactionTerminalState.RECOVERED
    assert state.get_relationship("REL-1") == plan.payload.relationships[0]


def test_state_write_preflight_rejects_unknown_observation_reference() -> None:
    subject = SubjectRef(subject_id="PERSON-1", subject_type="PERSON")
    relationship = _relationship(subject).model_copy(
        update={"target_id": "MISSING"}
    )

    with pytest.raises(ValidationError, match="unknown relationship target"):
        GovernedStateWritePlan.create(
            transaction_id="TX-BAD",
            subject=subject,
            domain="operations",
            observations=[_observation("OBS-1", subject)],
            relationships=[relationship],
            known_observation_ids=set(),
            execution_context=ExecutionContext.TEST,
            acceptable_authority_classes={"SUBJECT"},
            requested_at=_now(),
        )


def test_state_write_preflight_rejects_subject_leakage() -> None:
    subject = SubjectRef(subject_id="PERSON-1", subject_type="PERSON")
    other = SubjectRef(subject_id="PERSON-2", subject_type="PERSON")

    with pytest.raises(ValidationError, match="observation subject does not match"):
        GovernedStateWritePlan.create(
            transaction_id="TX-BAD",
            subject=subject,
            domain="operations",
            observations=[_observation("OBS-1", other)],
            relationships=[],
            known_observation_ids=set(),
            execution_context=ExecutionContext.TEST,
            acceptable_authority_classes={"SUBJECT"},
            requested_at=_now(),
        )


def test_state_write_plan_rejects_content_hash_tampering() -> None:
    plan = _plan("PERSON")
    tampered_operation = plan.operation.model_copy(
        update={"content_sha256": _hash("tampered")}
    )

    with pytest.raises(ValidationError, match="content hash does not match"):
        GovernedStateWritePlan(
            operation=tampered_operation,
            payload=plan.payload,
        )
