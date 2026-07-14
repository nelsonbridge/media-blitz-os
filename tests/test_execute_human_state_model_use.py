from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

import pytest

from nks.application.execute_human_state_model_use import (
    ExecuteGovernedHumanStateModelUse,
)
from nks.application.human_state_model_use import (
    BuildHumanStateModelUsePackage,
    ResolveHumanStateInterpretation,
)
from nks.application.model_use_journal import ModelUseEventStage
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
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 5, 0, tzinfo=timezone.utc)


class Repository:
    def __init__(self, *, scope: IngestionScope = IngestionScope.PERSONALIZATION) -> None:
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
            approved_scopes={scope},
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


class ApprovalMemory:
    def __init__(self, grant: ApprovalGrant) -> None:
        self.current = grant

    def get_approval(self, approval_id: str):
        return self.current if self.current.approval_id == approval_id else None

    def compare_and_swap_approval(self, expected, replacement) -> bool:
        if self.current != expected:
            return False
        self.current = replacement
        return True


class Writer:
    def __init__(self, *, fail_once: bool = False) -> None:
        self.fail_once = fail_once
        self.saved = []

    def save_model_use(self, package, receipt) -> None:
        if self.fail_once:
            self.fail_once = False
            raise OSError("simulated durable write failure")
        existing = [item for item in self.saved if item[1].receipt_id == receipt.receipt_id]
        if existing:
            assert existing[0] == (package, receipt)
            return
        self.saved.append((package, receipt))


class EventMemory:
    def __init__(self) -> None:
        self.events = {}

    def append(self, event) -> None:
        current = self.events.get(event.event_id)
        if current is not None:
            assert current == event
            return
        self.events[event.event_id] = event

    def stages(self) -> list[str]:
        return [event.payload["stage"] for event in self.events.values()]


def _setup(*, policy_scope: IngestionScope = IngestionScope.PERSONALIZATION):
    repository = Repository(scope=policy_scope)
    interpretation = ResolveHumanStateInterpretation(repository).execute(
        subject_id="SUBJECT-1",
        domain="career",
        now=_now(),
    )
    envelope = BuildHumanStateModelUsePackage().execute(
        interpretation,
        scope=IngestionScope.PERSONALIZATION,
    )
    action = "model-use:personalization"
    approval = ApprovalMemory(
        ApprovalGrant(
            approval_id="APR-1",
            decision=ApprovalDecision.APPROVED,
            execution_context=ExecutionContext.TEST,
            permitted_actions={action},
            subject_id="SUBJECT-1",
            content_sha256=envelope.payload_hash,
            authorized_by="SUBJECT-1",
            authority_class="SUBJECT",
            issued_at=_now() - timedelta(minutes=1),
            expires_at=_now() + timedelta(hours=1),
        )
    )
    request = ApprovalRequest(
        execution_context=ExecutionContext.TEST,
        action=action,
        subject_id="SUBJECT-1",
        content_sha256=envelope.payload_hash,
        acceptable_authority_classes={"SUBJECT"},
        transaction_id="TX-1",
        requested_at=_now(),
    )
    return repository, interpretation, envelope, approval, request


def test_success_consumes_authority_before_recording() -> None:
    repository, interpretation, envelope, approvals, request = _setup()
    writer = Writer()
    events = EventMemory()
    workflow = ExecuteGovernedHumanStateModelUse(
        model_use_reader=repository,
        model_use_writer=writer,
        approval_repository=approvals,
        event_writer=events,
        publisher_version="test/v1",
    )

    receipt = workflow.execute(
        interpretation,
        envelope,
        policy_id="POL-1",
        approval_id="APR-1",
        request=request,
        now=_now(),
    )

    assert approvals.current.consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert approvals.current.consumed_by_transaction_id == "TX-1"
    assert receipt.exact_retry is False
    assert receipt.authorized_at == request.requested_at
    assert receipt.recorded_at == request.requested_at
    assert writer.saved == [(envelope.package, receipt)]
    assert events.stages() == [
        ModelUseEventStage.APPROVAL_RESERVED.value,
        ModelUseEventStage.AUTHORIZED.value,
        ModelUseEventStage.APPROVAL_CONSUMED.value,
        ModelUseEventStage.PERSISTED.value,
    ]


def test_failed_persistence_leaves_consumed_authority_for_exact_retry() -> None:
    repository, interpretation, envelope, approvals, request = _setup()
    events = EventMemory()
    failing_writer = Writer(fail_once=True)
    workflow = ExecuteGovernedHumanStateModelUse(
        model_use_reader=repository,
        model_use_writer=failing_writer,
        approval_repository=approvals,
        event_writer=events,
        publisher_version="test/v1",
    )

    with pytest.raises(OSError, match="durable write failure"):
        workflow.execute(
            interpretation,
            envelope,
            policy_id="POL-1",
            approval_id="APR-1",
            request=request,
            now=_now(),
        )

    assert approvals.current.consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert ModelUseEventStage.FAILED.value in events.stages()
    assert ModelUseEventStage.PERSISTED.value not in events.stages()

    recovery_writer = Writer()
    recovery = ExecuteGovernedHumanStateModelUse(
        model_use_reader=repository,
        model_use_writer=recovery_writer,
        approval_repository=approvals,
        event_writer=events,
        publisher_version="test/v1",
    )
    receipt = recovery.execute(
        interpretation,
        envelope,
        policy_id="POL-1",
        approval_id="APR-1",
        request=request,
        now=_now() + timedelta(seconds=1),
    )

    assert receipt.exact_retry is False
    assert receipt.authorized_at == request.requested_at
    assert receipt.recorded_at == request.requested_at
    assert len(recovery_writer.saved) == 1
    assert ModelUseEventStage.PERSISTED.value in events.stages()
    assert ModelUseEventStage.RECOVERED.value in events.stages()


def test_authorization_failure_releases_unconsumed_reservation() -> None:
    repository, interpretation, envelope, approvals, request = _setup(
        policy_scope=IngestionScope.RETRIEVAL
    )
    events = EventMemory()
    workflow = ExecuteGovernedHumanStateModelUse(
        model_use_reader=repository,
        model_use_writer=Writer(),
        approval_repository=approvals,
        event_writer=events,
        publisher_version="test/v1",
    )

    with pytest.raises(ValueError, match="scope is not approved"):
        workflow.execute(
            interpretation,
            envelope,
            policy_id="POL-1",
            approval_id="APR-1",
            request=request,
            now=_now(),
        )

    assert approvals.current.consumption_status == ApprovalConsumptionStatus.AVAILABLE
    assert approvals.current.reserved_by_transaction_id is None
    assert events.stages() == [
        ModelUseEventStage.APPROVAL_RESERVED.value,
        ModelUseEventStage.RESERVATION_RELEASED.value,
        ModelUseEventStage.FAILED.value,
    ]
