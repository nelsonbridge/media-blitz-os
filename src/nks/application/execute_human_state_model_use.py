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
    4. persist deterministic package and receipt output.

    If persistence fails after consumption, the same transaction can rerun via
    exact-retry semantics and recreate the same deterministic receipt. If
    authorization fails before consumption, the reservation is released.
    """

    def __init__(
        self,
        *,
        model_use_reader: HumanStateModelUseReader,
        model_use_writer: HumanStateModelUseWriter,
        approval_repository: ApprovalGrantRepository,
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
        reserved = self._reserve.execute(approval_id, request, now=now)
        already_consumed = (
            reserved.consumption_status == ApprovalConsumptionStatus.CONSUMED
        )

        try:
            approval = evaluate_approval(reserved, request, now=now)
            authorized = self._authorize.execute(
                interpretation,
                envelope,
                policy_id=policy_id,
                approval=approval,
                now=now,
            )
            self._consume.execute(approval_id, request, now=now)
            return self._record.execute(authorized, recorded_at=now)
        except Exception:
            if not already_consumed:
                current = self._approval_repository.get_approval(approval_id)
                if (
                    current is not None
                    and current.consumption_status == ApprovalConsumptionStatus.RESERVED
                    and current.reserved_by_transaction_id == request.transaction_id
                ):
                    self._release.execute(approval_id, request.transaction_id)
            raise
