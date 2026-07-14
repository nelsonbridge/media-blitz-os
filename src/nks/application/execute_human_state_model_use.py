"""Recoverable execution workflow for governed human-state model use."""

from __future__ import annotations

from datetime import datetime

from nks.application.approval_lifecycle import (
    ApprovalGrantRepository,
    ConsumeApproval,
    ReleaseApprovalReservation,
    ReserveApproval,
)
from nks.application.governed_human_state_model_use import (
    AuthorizeReservedHumanStateModelUse,
)
from nks.application.human_state_model_use import (
    GovernedHumanStateModelUseReceipt,
    HumanStateInterpretation,
    HumanStateModelUseEnvelope,
    HumanStateModelUseReader,
    HumanStateModelUseWriter,
    RecordHumanStateModelUse,
)
from nks.application.model_use_journal import (
    ModelUseEventStage,
    ModelUseJournal,
    WorkflowEventWriter,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalRequest,
    evaluate_approval,
)


class ExecuteGovernedHumanStateModelUse:
    """Execute one model-use transaction with recoverable authority semantics.

    Sequence:

    1. reserve exact approval authority;
    2. evaluate the reserved grant and purpose policy;
    3. consume the grant before persistence or external dispatch;
    4. persist deterministic package and receipt output;
    5. journal every boundary using append-only transaction-stage events.

    If persistence or journal completion fails after consumption, the same
    transaction can rerun through exact-retry semantics and reproduce the same
    receipt and stage events. If authorization fails before consumption, the
    reservation is released and that release is journaled.
    """

    def __init__(
        self,
        *,
        model_use_reader: HumanStateModelUseReader,
        model_use_writer: HumanStateModelUseWriter,
        approval_repository: ApprovalGrantRepository,
        event_writer: WorkflowEventWriter | None = None,
        publisher_version: str = "0.1.0",
    ) -> None:
        self._approval_repository = approval_repository
        self._reserve = ReserveApproval(approval_repository)
        self._consume = ConsumeApproval(approval_repository)
        self._release = ReleaseApprovalReservation(approval_repository)
        self._authorize = AuthorizeReservedHumanStateModelUse(model_use_reader)
        self._record = RecordHumanStateModelUse(
            model_use_writer,
            publisher_version=publisher_version,
        )
        self._journal = ModelUseJournal(event_writer)

    def execute(
        self,
        interpretation: HumanStateInterpretation,
        envelope: HumanStateModelUseEnvelope,
        *,
        policy_id: str,
        approval_id: str,
        request: ApprovalRequest,
        now: datetime | None = None,
    ) -> GovernedHumanStateModelUseReceipt:
        def journal(
            stage: ModelUseEventStage,
            *,
            failure_type: str | None = None,
        ) -> None:
            self._journal.record(
                stage,
                occurred_at=request.requested_at,
                transaction_id=request.transaction_id,
                subject_id=request.subject_id,
                approval_id=approval_id,
                policy_id=policy_id,
                payload_hash=envelope.payload_hash,
                execution_context=request.execution_context.value,
                failure_type=failure_type,
            )

        reserved = self._reserve.execute(approval_id, request, now=now)
        already_consumed = (
            reserved.consumption_status == ApprovalConsumptionStatus.CONSUMED
        )
        journal(ModelUseEventStage.APPROVAL_RESERVED)

        try:
            approval = evaluate_approval(reserved, request, now=now)
            authorized = self._authorize.execute(
                interpretation,
                envelope,
                policy_id=policy_id,
                approval=approval,
                now=now,
            )
            journal(ModelUseEventStage.AUTHORIZED)

            self._consume.execute(approval_id, request, now=now)
            journal(ModelUseEventStage.APPROVAL_CONSUMED)

            # The canonical receipt describes the transaction, not the current
            # execution attempt. Retry state remains in ApprovalEvaluation so an
            # exact retry reproduces byte-identical receipt content.
            stable_authorized = authorized.model_copy(
                update={
                    "authorized_at": request.requested_at,
                    "exact_retry": False,
                }
            )
            receipt = self._record.execute(
                stable_authorized,
                recorded_at=request.requested_at,
            )
            journal(ModelUseEventStage.PERSISTED)
            if already_consumed:
                journal(ModelUseEventStage.RECOVERED)
            return receipt
        except Exception as exc:
            if not already_consumed:
                current = self._approval_repository.get_approval(approval_id)
                if (
                    current is not None
                    and current.consumption_status == ApprovalConsumptionStatus.RESERVED
                    and current.reserved_by_transaction_id == request.transaction_id
                ):
                    self._release.execute(approval_id, request.transaction_id)
                    journal(ModelUseEventStage.RESERVATION_RELEASED)
            journal(ModelUseEventStage.FAILED, failure_type=type(exc).__name__)
            raise
