from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from nks.application.approval_lifecycle import (
    ConsumeApproval,
    ReleaseApprovalReservation,
    ReserveApproval,
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
    return datetime(2026, 7, 14, 1, 0, tzinfo=timezone.utc)


def _grant() -> ApprovalGrant:
    return ApprovalGrant(
        approval_id="APR-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={"model-use:personalization"},
        subject_id="SUBJECT-1",
        content_sha256=_hash("payload"),
        authorized_by="SUBJECT-1",
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=5),
        expires_at=_now() + timedelta(hours=1),
    )


def _request(transaction_id: str = "TX-1") -> ApprovalRequest:
    return ApprovalRequest(
        execution_context=ExecutionContext.TEST,
        action="model-use:personalization",
        subject_id="SUBJECT-1",
        content_sha256=_hash("payload"),
        acceptable_authority_classes={"SUBJECT"},
        transaction_id=transaction_id,
        requested_at=_now(),
    )


class MemoryApprovalRepository:
    def __init__(self, grant: ApprovalGrant) -> None:
        self.current = grant
        self.fail_next_compare_and_swap = False

    def get_approval(self, approval_id: str) -> ApprovalGrant | None:
        return self.current if self.current.approval_id == approval_id else None

    def compare_and_swap_approval(
        self,
        expected: ApprovalGrant,
        replacement: ApprovalGrant,
    ) -> bool:
        if self.fail_next_compare_and_swap:
            self.fail_next_compare_and_swap = False
            return False
        if self.current != expected:
            return False
        self.current = replacement
        return True


def test_approval_must_be_reserved_then_consumed() -> None:
    repository = MemoryApprovalRepository(_grant())

    reserved = ReserveApproval(repository).execute("APR-1", _request(), now=_now())
    consumed = ConsumeApproval(repository).execute("APR-1", _request(), now=_now())

    assert reserved.consumption_status == ApprovalConsumptionStatus.RESERVED
    assert reserved.reserved_by_transaction_id == "TX-1"
    assert consumed.consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert consumed.reserved_by_transaction_id is None
    assert consumed.consumed_by_transaction_id == "TX-1"


def test_other_transaction_cannot_use_reservation() -> None:
    repository = MemoryApprovalRepository(_grant())
    ReserveApproval(repository).execute("APR-1", _request("TX-1"), now=_now())

    with pytest.raises(PermissionError, match="reserved by another transaction"):
        ReserveApproval(repository).execute("APR-1", _request("TX-2"), now=_now())

    with pytest.raises(PermissionError, match="reserved by another transaction"):
        ConsumeApproval(repository).execute("APR-1", _request("TX-2"), now=_now())


def test_exact_retry_is_idempotent_after_consumption() -> None:
    repository = MemoryApprovalRepository(_grant())
    request = _request()
    ReserveApproval(repository).execute("APR-1", request, now=_now())
    first = ConsumeApproval(repository).execute("APR-1", request, now=_now())
    second = ConsumeApproval(repository).execute("APR-1", request, now=_now())

    assert first == second
    assert second.consumed_by_transaction_id == request.transaction_id


def test_reservation_can_be_released_before_consumption() -> None:
    repository = MemoryApprovalRepository(_grant())
    ReserveApproval(repository).execute("APR-1", _request(), now=_now())

    released = ReleaseApprovalReservation(repository).execute("APR-1", "TX-1")

    assert released.consumption_status == ApprovalConsumptionStatus.AVAILABLE
    assert released.reserved_by_transaction_id is None


def test_available_approval_cannot_be_consumed_without_reservation() -> None:
    repository = MemoryApprovalRepository(_grant())

    with pytest.raises(PermissionError, match="must be reserved"):
        ConsumeApproval(repository).execute("APR-1", _request(), now=_now())


def test_compare_and_swap_conflict_fails_without_claiming_authority() -> None:
    repository = MemoryApprovalRepository(_grant())
    repository.fail_next_compare_and_swap = True

    with pytest.raises(RuntimeError, match="state changed during reservation"):
        ReserveApproval(repository).execute("APR-1", _request(), now=_now())

    assert repository.current.consumption_status == ApprovalConsumptionStatus.AVAILABLE
