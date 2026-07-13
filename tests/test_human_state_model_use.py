from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

import pytest

from nks.application.human_state_model_use import (
    AuthorizeHumanStateModelUse,
    BuildHumanStateModelUsePackage,
    RecordHumanStateModelUse,
    ResolveHumanStateInterpretation,
)
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    HumanStateTransition,
    IngestionScope,
    ModelIngestionPolicy,
    TemporalStatus,
    TransitionOrigin,
    TransitionType,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ApprovalRequest,
    ExecutionContext,
    evaluate_approval,
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 0, 0, tzinfo=timezone.utc)


def _observation(
    observation_id: str,
    content: str,
    *,
    effective_from: date,
    status: TemporalStatus,
) -> HumanStateObservation:
    return HumanStateObservation(
        observation_id=observation_id,
        subject_id="SUBJECT-1",
        content=content,
        content_hash=_hash(content),
        domain="career",
        state_type="DECLARED_OBJECTIVE",
        provenance="REAL",
        source_id=f"SOURCE-{observation_id}",
        observed_at=_now(),
        effective_from=effective_from,
        expression_strength=ExpressionStrength.EXPLICIT,
        confidence="HIGH",
        temporal_status=status,
    )


class MemoryRepository:
    def __init__(self) -> None:
        historical = _observation(
            "OBS-1",
            "Seek a promotion.",
            effective_from=date(2026, 1, 1),
            status=TemporalStatus.HISTORICAL,
        )
        current = _observation(
            "OBS-2",
            "Prioritize stable income over title.",
            effective_from=date(2026, 6, 1),
            status=TemporalStatus.CURRENT,
        )
        transition = HumanStateTransition(
            transition_id="TR-1",
            subject_id="SUBJECT-1",
            domain="career",
            from_observation_id=historical.observation_id,
            to_observation_id=current.observation_id,
            transition_type=TransitionType.REFINEMENT,
            origin=TransitionOrigin.SUBJECT_DECLARED,
            detected_at=_now(),
            durability="UNKNOWN",
            reversibility="REVERSIBLE",
            confidence="HIGH",
            approved_for_model_feedback=True,
            approved_by="LEGACY-APPROVER",
        )
        policy = ModelIngestionPolicy(
            policy_id="POL-1",
            subject_id="SUBJECT-1",
            domain="career",
            observation_id=current.observation_id,
            observation_hash=current.content_hash,
            approved_scopes={IngestionScope.PERSONALIZATION},
            denied_scopes=set(),
            approved_by="SUBJECT-1",
            approved_at=_now() - timedelta(minutes=5),
            expires_at=_now() + timedelta(hours=1),
        )
        self.observations = [historical, current]
        self.transitions = [transition]
        self.policy = policy

    def list_observations(self, subject_id: str, domain: str):
        return [
            item
            for item in self.observations
            if item.subject_id == subject_id and item.domain == domain
        ]

    def list_transitions(self, subject_id: str, domain: str):
        return [
            item
            for item in self.transitions
            if item.subject_id == subject_id and item.domain == domain
        ]

    def get_policy(self, policy_id: str):
        return self.policy if policy_id == self.policy.policy_id else None


class MemoryWriter:
    def __init__(self) -> None:
        self.saved = []

    def save_model_use(self, package, receipt) -> None:
        self.saved.append((package, receipt))


def _approval(envelope, *, content_hash: str | None = None, consumed: bool = False):
    action = "model-use:personalization"
    transaction_id = "TX-MODEL-1"
    request = ApprovalRequest(
        execution_context=ExecutionContext.TEST,
        action=action,
        subject_id="SUBJECT-1",
        content_sha256=content_hash or envelope.payload_hash,
        acceptable_authority_classes={"SUBJECT"},
        transaction_id=transaction_id,
        requested_at=_now(),
    )
    grant = ApprovalGrant(
        approval_id="APR-MODEL-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={action},
        subject_id="SUBJECT-1",
        content_sha256=content_hash or envelope.payload_hash,
        authorized_by="SUBJECT-1",
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=1),
        expires_at=_now() + timedelta(hours=1),
        consumption_status=(
            ApprovalConsumptionStatus.CONSUMED
            if consumed
            else ApprovalConsumptionStatus.AVAILABLE
        ),
        consumed_by_transaction_id=transaction_id if consumed else None,
    )
    return evaluate_approval(grant, request)


def test_interpretation_and_package_building_do_not_imply_authority() -> None:
    repository = MemoryRepository()
    interpretation = ResolveHumanStateInterpretation(repository).execute(
        subject_id="SUBJECT-1",
        domain="career",
        now=_now(),
    )

    envelope = BuildHumanStateModelUsePackage().execute(
        interpretation,
        scope=IngestionScope.PERSONALIZATION,
    )

    assert interpretation.current_observation.observation_id == "OBS-2"
    assert [item.observation_id for item in interpretation.historical_observations] == ["OBS-1"]
    assert envelope.package.transitions == []
    assert repository.transitions[0].approved_for_model_feedback is True


def test_transition_inclusion_is_explicit_not_legacy_boolean_authority() -> None:
    repository = MemoryRepository()
    interpretation = ResolveHumanStateInterpretation(repository).execute(
        subject_id="SUBJECT-1",
        domain="career",
        now=_now(),
    )

    envelope = BuildHumanStateModelUsePackage().execute(
        interpretation,
        scope=IngestionScope.PERSONALIZATION,
        included_transition_ids=["TR-1"],
    )

    assert [item.transition_id for item in envelope.package.transitions] == ["TR-1"]


def test_governed_authority_binds_exact_package_before_recording() -> None:
    repository = MemoryRepository()
    interpretation = ResolveHumanStateInterpretation(repository).execute(
        subject_id="SUBJECT-1",
        domain="career",
        now=_now(),
    )
    envelope = BuildHumanStateModelUsePackage().execute(
        interpretation,
        scope=IngestionScope.PERSONALIZATION,
        included_transition_ids=["TR-1"],
    )
    authorized = AuthorizeHumanStateModelUse(repository).execute(
        interpretation,
        envelope,
        policy_id="POL-1",
        approval=_approval(envelope),
        now=_now(),
    )
    writer = MemoryWriter()

    receipt = RecordHumanStateModelUse(writer, publisher_version="test/v1").execute(
        authorized,
        recorded_at=_now(),
    )

    assert receipt.approval_id == "APR-MODEL-1"
    assert receipt.execution_context == ExecutionContext.TEST
    assert receipt.payload_hash == envelope.payload_hash
    assert receipt.transition_ids == ["TR-1"]
    assert writer.saved == [(envelope.package, receipt)]


def test_wrong_package_hash_fails_before_persistence() -> None:
    repository = MemoryRepository()
    interpretation = ResolveHumanStateInterpretation(repository).execute(
        subject_id="SUBJECT-1",
        domain="career",
        now=_now(),
    )
    envelope = BuildHumanStateModelUsePackage().execute(
        interpretation,
        scope=IngestionScope.PERSONALIZATION,
    )
    wrong_hash = _hash("other payload")

    with pytest.raises(PermissionError, match="content hash"):
        AuthorizeHumanStateModelUse(repository).execute(
            interpretation,
            envelope,
            policy_id="POL-1",
            approval=_approval(envelope, content_hash=wrong_hash),
            now=_now(),
        )


def test_exact_retry_produces_same_deterministic_receipt_id() -> None:
    repository = MemoryRepository()
    interpretation = ResolveHumanStateInterpretation(repository).execute(
        subject_id="SUBJECT-1",
        domain="career",
        now=_now(),
    )
    envelope = BuildHumanStateModelUsePackage().execute(
        interpretation,
        scope=IngestionScope.PERSONALIZATION,
    )
    authorization = AuthorizeHumanStateModelUse(repository).execute(
        interpretation,
        envelope,
        policy_id="POL-1",
        approval=_approval(envelope, consumed=True),
        now=_now(),
    )
    writer = MemoryWriter()
    recorder = RecordHumanStateModelUse(writer, publisher_version="test/v1")

    first = recorder.execute(authorization, recorded_at=_now())
    second = recorder.execute(authorization, recorded_at=_now() + timedelta(seconds=1))

    assert authorization.exact_retry is True
    assert first.receipt_id == second.receipt_id
