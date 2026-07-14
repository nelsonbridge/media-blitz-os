"""Execution-safe wrapper for the decomposed human-state model-use path."""

from __future__ import annotations

from datetime import datetime

from nks.application.human_state_model_use import (
    AuthorizedHumanStateModelUse,
    AuthorizeHumanStateModelUse,
    HumanStateInterpretation,
    HumanStateModelUseEnvelope,
    HumanStateModelUseReader,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalEvaluation,
)


class AuthorizeReservedHumanStateModelUse:
    """Authorize model use only after the transaction owns the grant.

    ``AuthorizeHumanStateModelUse`` remains the lower-level compatibility
    validator for policy, scope, subject, and content. This wrapper is the
    side-effect boundary and additionally requires either a reservation owned
    by the current transaction or the same transaction's exact retry.
    """

    def __init__(self, repository: HumanStateModelUseReader) -> None:
        self._delegate = AuthorizeHumanStateModelUse(repository)

    def execute(
        self,
        interpretation: HumanStateInterpretation,
        envelope: HumanStateModelUseEnvelope,
        *,
        policy_id: str,
        approval: ApprovalEvaluation,
        now: datetime | None = None,
    ) -> AuthorizedHumanStateModelUse:
        request = approval.request
        reservation_owned = (
            approval.consumption_status == ApprovalConsumptionStatus.RESERVED
            and approval.reserved_by_transaction_id == request.transaction_id
        )
        retry_owned = (
            approval.consumption_status == ApprovalConsumptionStatus.CONSUMED
            and approval.exact_retry
            and approval.consumed_by_transaction_id == request.transaction_id
        )
        if not reservation_owned and not retry_owned:
            raise PermissionError("model-use approval is not reserved for execution")

        return self._delegate.execute(
            interpretation,
            envelope,
            policy_id=policy_id,
            approval=approval,
            now=now,
        )
