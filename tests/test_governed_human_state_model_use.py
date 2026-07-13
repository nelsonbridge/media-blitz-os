from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

import pytest

from nks.application.governed_human_state_model_use import (
    AuthorizeReservedHumanStateModelUse,
)
from nks.application.human_state_model_use import (
    BuildHumanStateModelUsePackage,
    ResolveHumanStateInterpretation,
)
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    IngestionScope,
    ModelIngestionPolicy,
    TemporalStatus,
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
    return datetime(2026, 7, 14, 2, 0, tzinfo=timezone.utc)


class Repository:
    def __init__(self) -> None:
        self.observation = HumanStateObservation(
            observation_id="OBS-1",
            subject_id="SUBJECT-1",
            content="Prioritize stable income.",
            content_hash=_hash("Prioritize stable income."),
            domain="career",
            state_type="DECLARED_PRIORITY",
            provenance="REAL",
            source_id="SOURCE-1",
            observed_at=_now(),
            effective_from=date(2026, 7, 1),
            expression_strength=ExpressionStrength.EXPLICIT,
            confidence="HIGH",
            temporal_status=TemporalStatus.CURRENT,
        )
        self.policy = ModelIngestionPolicy(
            policy_id="POL-1",
            subject_id="SUBJECT-1",
            domain="career",
            observation_id=self.observation.observation_id,
            observation_hash=self.observation.content_hash,
            approved_scopes={IngestionScope.PERSONALIZATION},
            approved_by="SUBJECT-1",
            approved_at=_now() - timedelta(minutes=5),
            expires_at=_now() + timedelta(hours=1),
        )

    def list_observations(self, subject_id: str, domain: str):
        return [self.observation]

    def list_transitions(self, subject_id: str, domain: str):
        return []

    def get_policy(self, policy_id: str):
        return self.policy if policy_id == self.policy.policy_id else None


def _interpretation_and_envelope(repository: Repository):
    interpretation = ResolveHumanStateInterpretation(repository).execute(
        subject_id="SUBJECT-1",
        domain="career",
        now=_now(),
    )
    envelope = BuildHumanStateModelUsePackage().execute(
        interpretation,
        scope=IngestionScope.PERSONALIZATION,
    )
    return interpretation, envelope


def _evaluation(envelope, status: ApprovalConsumptionStatus):
    transaction_id = "TX-1"
    request = ApprovalRequest(
        execution_context=ExecutionContext.TEST,
        action="model-use:personalization",
        subject_id="SUBJECT-1",
        content_sha256=envelope.payload_hash,
        acceptable_authority_classes={"SUBJECT"},
        transaction_id=transaction_id,
        requested_at=_now(),
    )
    grant = ApprovalGrant(
        approval_id="APR-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={"model-use:personalization"},
        subject_id="SUBJECT-1",
        content_sha256=envelope.payload_hash,
        authorized_by="SUBJECT-1",
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=1),
        expires_at=_now() + timedelta(hours=1),
        consumption_status=status,
        reserved_by_transaction_id=(
            transaction_id if status == ApprovalConsumptionStatus.RESERVED else None
        ),
        consumed_by_transaction_id=(
            transaction_id if status == ApprovalConsumptionStatus.CONSUMED else None
        ),
    )
    return evaluate_approval(grant, request)


def test_available_grant_cannot_cross_model_use_execution_boundary() -> None:
    repository = Repository()
    interpretation, envelope = _interpretation_and_envelope(repository)

    with pytest.raises(PermissionError, match="not reserved for execution"):
        AuthorizeReservedHumanStateModelUse(repository).execute(
            interpretation,
            envelope,
            policy_id="POL-1",
            approval=_evaluation(envelope, ApprovalConsumptionStatus.AVAILABLE),
            now=_now(),
        )


def test_transaction_owned_reservation_authorizes_model_use() -> None:
    repository = Repository()
    interpretation, envelope = _interpretation_and_envelope(repository)

    authorized = AuthorizeReservedHumanStateModelUse(repository).execute(
        interpretation,
        envelope,
        policy_id="POL-1",
        approval=_evaluation(envelope, ApprovalConsumptionStatus.RESERVED),
        now=_now(),
    )

    assert authorized.approval_id == "APR-1"
    assert authorized.transaction_id == "TX-1"
    assert authorized.exact_retry is False


def test_exact_retry_of_consumed_grant_remains_authorized() -> None:
    repository = Repository()
    interpretation, envelope = _interpretation_and_envelope(repository)

    authorized = AuthorizeReservedHumanStateModelUse(repository).execute(
        interpretation,
        envelope,
        policy_id="POL-1",
        approval=_evaluation(envelope, ApprovalConsumptionStatus.CONSUMED),
        now=_now(),
    )

    assert authorized.exact_retry is True
