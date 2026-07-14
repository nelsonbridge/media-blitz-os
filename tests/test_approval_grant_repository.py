from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from nks.adapters.approval_grants import (
    ApprovalGrantConflictError,
    JsonApprovalGrantRepository,
)
from nks.application.approval_lifecycle import ConsumeApproval, ReserveApproval
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
    return datetime(2026, 7, 14, 4, 0, tzinfo=timezone.utc)


def _grant(*, authorized_by: str = "SUBJECT-1") -> ApprovalGrant:
    return ApprovalGrant(
        approval_id="APR-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={"model-use:personalization", "surface-finding"},
        subject_id="SUBJECT-1",
        content_sha256=_hash("payload"),
        authorized_by=authorized_by,
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=5),
        expires_at=_now() + timedelta(hours=1),
    )


def _request() -> ApprovalRequest:
    return ApprovalRequest(
        execution_context=ExecutionContext.TEST,
        action="model-use:personalization",
        subject_id="SUBJECT-1",
        content_sha256=_hash("payload"),
        acceptable_authority_classes={"SUBJECT"},
        transaction_id="TX-1",
        requested_at=_now(),
    )


def test_save_new_is_durable_deterministic_and_idempotent(tmp_path: Path) -> None:
    repository = JsonApprovalGrantRepository(tmp_path)
    grant = _grant()

    repository.save_new(grant)
    repository.save_new(grant)

    assert repository.get_approval("APR-1") == grant
    assert repository.list_approvals() == [grant]
    text = (tmp_path / "records" / "approval-grants" / "APR-1.json").read_text(
        encoding="utf-8"
    )
    assert text.index("model-use:personalization") < text.index("surface-finding")


def test_existing_identity_with_different_content_fails(tmp_path: Path) -> None:
    repository = JsonApprovalGrantRepository(tmp_path)
    repository.save_new(_grant())

    with pytest.raises(ApprovalGrantConflictError, match="different content"):
        repository.save_new(_grant(authorized_by="OTHER-SUBJECT"))


def test_repository_supports_atomic_reservation_and_consumption(tmp_path: Path) -> None:
    repository = JsonApprovalGrantRepository(tmp_path)
    repository.save_new(_grant())

    reserved = ReserveApproval(repository).execute("APR-1", _request(), now=_now())
    consumed = ConsumeApproval(repository).execute("APR-1", _request(), now=_now())

    assert reserved.consumption_status == ApprovalConsumptionStatus.RESERVED
    assert consumed.consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert repository.get_approval("APR-1") == consumed


def test_compare_and_swap_rejects_stale_expected_state(tmp_path: Path) -> None:
    repository = JsonApprovalGrantRepository(tmp_path)
    original = repository.save_new(_grant())
    reserved = original.model_copy(
        update={
            "consumption_status": ApprovalConsumptionStatus.RESERVED,
            "reserved_by_transaction_id": "TX-1",
        }
    )
    assert repository.compare_and_swap_approval(original, reserved) is True

    conflicting = original.model_copy(
        update={
            "consumption_status": ApprovalConsumptionStatus.RESERVED,
            "reserved_by_transaction_id": "TX-2",
        }
    )
    assert repository.compare_and_swap_approval(original, conflicting) is False
    assert repository.get_approval("APR-1") == reserved


def test_lock_contention_fails_without_mutating_state(tmp_path: Path) -> None:
    repository = JsonApprovalGrantRepository(tmp_path)
    original = repository.save_new(_grant())
    lock = tmp_path / "records" / "approval-grants" / ".APR-1.lock"
    lock.write_text("held", encoding="utf-8")
    replacement = original.model_copy(
        update={
            "consumption_status": ApprovalConsumptionStatus.RESERVED,
            "reserved_by_transaction_id": "TX-1",
        }
    )

    assert repository.compare_and_swap_approval(original, replacement) is False
    assert repository.get_approval("APR-1") == original
