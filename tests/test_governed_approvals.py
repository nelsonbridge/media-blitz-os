from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

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
    return datetime(2026, 7, 13, 21, 0, tzinfo=timezone.utc)


def _grant(**overrides: object) -> ApprovalGrant:
    values: dict[str, object] = {
        "approval_id": "APR-1",
        "decision": ApprovalDecision.APPROVED,
        "execution_context": ExecutionContext.TEST,
        "permitted_actions": {"surface-finding"},
        "subject_id": "SUBJECT-1",
        "content_sha256": _hash("payload"),
        "authorized_by": "STEWARD-1",
        "authority_class": "SUBJECT",
        "issued_at": _now() - timedelta(minutes=5),
        "expires_at": _now() + timedelta(hours=1),
    }
    values.update(overrides)
    return ApprovalGrant(**values)


def _request(**overrides: object) -> ApprovalRequest:
    values: dict[str, object] = {
        "execution_context": ExecutionContext.TEST,
        "action": "surface-finding",
        "subject_id": "SUBJECT-1",
        "content_sha256": _hash("payload"),
        "acceptable_authority_classes": {"SUBJECT", "ANU"},
        "transaction_id": "TX-1",
        "requested_at": _now(),
    }
    values.update(overrides)
    return ApprovalRequest(**values)


def test_matching_grant_authorizes_exact_operation() -> None:
    result = evaluate_approval(_grant(), _request())

    assert result.authorized is True
    assert result.exact_retry is False
    assert result.reasons == []


@pytest.mark.parametrize(
    ("grant_override", "request_override", "reason"),
    [
        ({"decision": ApprovalDecision.DENIED}, {}, "grant decision"),
        ({"execution_context": ExecutionContext.PRODUCTION}, {}, "execution context"),
        ({"permitted_actions": {"other-action"}}, {}, "requested action"),
        ({"subject_id": "SUBJECT-2"}, {}, "subject does not match"),
        ({"content_sha256": _hash("different")}, {}, "content hash"),
        ({"authority_class": "OBSERVER"}, {}, "authority class"),
    ],
)
def test_mismatched_dimension_fails_closed(
    grant_override: dict[str, object],
    request_override: dict[str, object],
    reason: str,
) -> None:
    result = evaluate_approval(_grant(**grant_override), _request(**request_override))

    assert result.authorized is False
    assert any(reason in item for item in result.reasons)


def test_expired_or_revoked_grant_fails_closed() -> None:
    expired = evaluate_approval(
        _grant(expires_at=_now()),
        _request(),
    )
    revoked = evaluate_approval(
        _grant(revoked_at=_now() - timedelta(seconds=1)),
        _request(),
    )

    assert expired.authorized is False
    assert "grant is expired" in expired.reasons
    assert revoked.authorized is False
    assert "grant is revoked" in revoked.reasons


def test_consumed_grant_allows_only_exact_retry() -> None:
    grant = _grant(
        consumption_status=ApprovalConsumptionStatus.CONSUMED,
        consumed_by_transaction_id="TX-1",
    )

    retry = evaluate_approval(grant, _request(transaction_id="TX-1"))
    other = evaluate_approval(grant, _request(transaction_id="TX-2"))

    assert retry.authorized is True
    assert retry.exact_retry is True
    assert other.authorized is False
    assert "grant was consumed by another transaction" in other.reasons


def test_consumed_status_requires_transaction_id() -> None:
    with pytest.raises(ValueError, match="consumed approvals require"):
        _grant(consumption_status=ApprovalConsumptionStatus.CONSUMED)
