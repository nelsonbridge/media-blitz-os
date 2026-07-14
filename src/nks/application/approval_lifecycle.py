"""Application services for atomic approval reservation and consumption."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalGrant,
    ApprovalRequest,
    evaluate_approval,
)


class ApprovalGrantRepository(Protocol):
    """Persistence port requiring optimistic compare-and-swap semantics."""

    def get_approval(self, approval_id: str) -> ApprovalGrant | None: ...

    def compare_and_swap_approval(
        self,
        expected: ApprovalGrant,
        replacement: ApprovalGrant,
    ) -> bool: ...


class ReserveApproval:
    def __init__(self, repository: ApprovalGrantRepository) -> None:
        self._repository = repository

    def execute(
        self,
        approval_id: str,
        request: ApprovalRequest,
        *,
        now: datetime | None = None,
    ) -> ApprovalGrant:
        grant = self._require_grant(approval_id)
        evaluation = evaluate_approval(grant, request, now=now)
        if not evaluation.authorized:
            raise PermissionError("; ".join(evaluation.reasons))

        if grant.consumption_status == ApprovalConsumptionStatus.CONSUMED:
            return grant
        if grant.consumption_status == ApprovalConsumptionStatus.RESERVED:
            return grant
        if grant.consumption_status != ApprovalConsumptionStatus.AVAILABLE:
            raise PermissionError("approval is not available for reservation")

        replacement = grant.model_copy(
            update={
                "consumption_status": ApprovalConsumptionStatus.RESERVED,
                "reserved_by_transaction_id": request.transaction_id,
                "consumed_by_transaction_id": None,
            }
        )
        if not self._repository.compare_and_swap_approval(grant, replacement):
            raise RuntimeError("approval state changed during reservation")
        return replacement

    def _require_grant(self, approval_id: str) -> ApprovalGrant:
        grant = self._repository.get_approval(approval_id)
        if grant is None:
            raise ValueError("approval grant does not exist")
        return grant


class ConsumeApproval:
    def __init__(self, repository: ApprovalGrantRepository) -> None:
        self._repository = repository

    def execute(
        self,
        approval_id: str,
        request: ApprovalRequest,
        *,
        now: datetime | None = None,
    ) -> ApprovalGrant:
        grant = self._require_grant(approval_id)
        evaluation = evaluate_approval(grant, request, now=now)
        if not evaluation.authorized:
            raise PermissionError("; ".join(evaluation.reasons))

        if grant.consumption_status == ApprovalConsumptionStatus.CONSUMED:
            return grant
        if grant.consumption_status != ApprovalConsumptionStatus.RESERVED:
            raise PermissionError("approval must be reserved before consumption")
        if grant.reserved_by_transaction_id != request.transaction_id:
            raise PermissionError("approval reservation belongs to another transaction")

        replacement = grant.model_copy(
            update={
                "consumption_status": ApprovalConsumptionStatus.CONSUMED,
                "reserved_by_transaction_id": None,
                "consumed_by_transaction_id": request.transaction_id,
            }
        )
        if not self._repository.compare_and_swap_approval(grant, replacement):
            raise RuntimeError("approval state changed during consumption")
        return replacement

    def _require_grant(self, approval_id: str) -> ApprovalGrant:
        grant = self._repository.get_approval(approval_id)
        if grant is None:
            raise ValueError("approval grant does not exist")
        return grant


class ReleaseApprovalReservation:
    """Release an unconsumed reservation after rollback or abandoned work."""

    def __init__(self, repository: ApprovalGrantRepository) -> None:
        self._repository = repository

    def execute(self, approval_id: str, transaction_id: str) -> ApprovalGrant:
        grant = self._repository.get_approval(approval_id)
        if grant is None:
            raise ValueError("approval grant does not exist")
        if grant.consumption_status == ApprovalConsumptionStatus.AVAILABLE:
            return grant
        if grant.consumption_status != ApprovalConsumptionStatus.RESERVED:
            raise PermissionError("only an unconsumed reservation may be released")
        if grant.reserved_by_transaction_id != transaction_id:
            raise PermissionError("approval reservation belongs to another transaction")

        replacement = grant.model_copy(
            update={
                "consumption_status": ApprovalConsumptionStatus.AVAILABLE,
                "reserved_by_transaction_id": None,
                "consumed_by_transaction_id": None,
            }
        )
        if not self._repository.compare_and_swap_approval(grant, replacement):
            raise RuntimeError("approval state changed during reservation release")
        return replacement
