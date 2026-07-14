from __future__ import annotations

from datetime import datetime, timezone

import pytest

from nks.application.forensic_reconstruction import (
    ForensicRecord,
    ReconstructionRequest,
    ReconstructionStatus,
    reconstruct_operation,
)
from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext


NOW = datetime(2026, 7, 14, 14, 0, tzinfo=timezone.utc)
FAMILIES = [
    "state-write",
    "migration",
    "reconciliation",
    "disclosure",
    "transition",
    "model-use",
    "feedback",
    "promotion",
    "work-control-amendment",
]


def _record(
    record_id: str,
    record_type: str,
    *,
    family: str = "state-write",
    operation_id: str = "OP-1",
    transaction_id: str = "TX-1",
    context: ExecutionContext = ExecutionContext.TEST,
    authority: str = "HUMAN_ORIGIN_AUTHORITY",
    payload: dict[str, object] | None = None,
) -> ForensicRecord:
    return ForensicRecord.create(
        record_id=record_id,
        record_type=record_type,
        operation_family=family,
        operation_id=operation_id,
        transaction_id=transaction_id,
        execution_context=context,
        authority_class=authority,
        payload=payload or {"record": record_type, "plan_sha256": canonical_sha256("plan")},
        recorded_at=NOW,
    )


def _request(
    *,
    family: str = "state-write",
    required: set[str] | None = None,
    repairable: set[str] | None = None,
    context: ExecutionContext = ExecutionContext.TEST,
) -> ReconstructionRequest:
    return ReconstructionRequest(
        operation_family=family,
        operation_id="OP-1",
        transaction_id="TX-1",
        execution_context=context,
        required_record_types=required or {"plan", "approval", "effect", "transaction-receipt"},
        repairable_record_types=repairable or set(),
        acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
        expected_plan_sha256=canonical_sha256("plan"),
        expected_output_sha256=canonical_sha256("output"),
    )


def _complete_records(family: str = "state-write") -> list[ForensicRecord]:
    common = {"plan_sha256": canonical_sha256("plan")}
    return [
        _record("R-PLAN", "plan", family=family, payload=common),
        _record("R-APPROVAL", "approval", family=family, payload=common),
        _record("R-EFFECT", "effect", family=family, payload=common),
        _record(
            "R-RECEIPT",
            "transaction-receipt",
            family=family,
            payload={
                **common,
                "terminal_state": "COMMITTED",
                "output_sha256": canonical_sha256("output"),
            },
        ),
    ]


@pytest.mark.parametrize("family", FAMILIES)
def test_common_reconstructor_covers_every_governed_operation_family(family: str) -> None:
    result = reconstruct_operation(_request(family=family), _complete_records(family))
    assert result.status == ReconstructionStatus.COMPLETE
    assert result.output_sha256 == canonical_sha256("output")


def test_incomplete_when_required_evidence_has_not_been_produced() -> None:
    result = reconstruct_operation(_request(), [_record("R-PLAN", "plan")])
    assert result.status == ReconstructionStatus.INCOMPLETE
    assert "transaction-receipt" in result.missing_record_types


def test_repairable_when_consumed_authority_or_committed_source_can_rebuild_projection() -> None:
    request = _request(
        required={"plan", "approval-consumed", "transaction-receipt", "projection"},
        repairable={"projection"},
    )
    records = [
        _record("R-PLAN", "plan"),
        _record("R-CONSUMED", "approval-consumed"),
        _record(
            "R-RECEIPT",
            "transaction-receipt",
            payload={
                "plan_sha256": canonical_sha256("plan"),
                "terminal_state": "RECOVERED",
                "output_sha256": canonical_sha256("output"),
            },
        ),
    ]
    result = reconstruct_operation(request, records)
    assert result.status == ReconstructionStatus.REPAIRABLE
    assert result.repair_actions == ["rebuild:projection"]


def test_consumed_without_terminal_receipt_requires_exact_retry() -> None:
    result = reconstruct_operation(_request(), [_record("R-CONSUMED", "approval-consumed")])
    assert result.status == ReconstructionStatus.REPAIRABLE
    assert "exact-retry" in result.repair_actions


def test_rolled_back_terminal_receipt_is_distinct_from_failure() -> None:
    record = _record(
        "R-RECEIPT",
        "transaction-receipt",
        payload={"plan_sha256": canonical_sha256("plan"), "terminal_state": "ROLLED_BACK"},
    )
    result = reconstruct_operation(_request(), [record])
    assert result.status == ReconstructionStatus.ROLLED_BACK


@pytest.mark.parametrize(
    ("mutation", "conflict"),
    [
        ("payload-hash", "record payload hash mismatch"),
        ("context", "execution context mismatch"),
        ("authority", "authority class is not accepted"),
        ("plan", "plan hash mismatch"),
    ],
)
def test_corrupt_cross_context_stale_or_unauthorized_evidence_fails_closed(
    mutation: str,
    conflict: str,
) -> None:
    record = _record("R-PLAN", "plan")
    if mutation == "payload-hash":
        record = record.model_copy(update={"payload": {"tampered": True}})
    elif mutation == "context":
        record = record.model_copy(update={"execution_context": ExecutionContext.PRODUCTION})
    elif mutation == "authority":
        record = record.model_copy(update={"authority_class": "UNTRUSTED"})
    else:
        record = record.model_copy(
            update={
                "payload": {"plan_sha256": canonical_sha256("stale")},
                "content_sha256": canonical_sha256({"plan_sha256": canonical_sha256("stale")}),
            }
        )
    result = reconstruct_operation(_request(), [record])
    assert result.status == ReconstructionStatus.CONFLICT
    assert any(conflict in message for message in result.conflicts)


def test_conflicting_immutable_record_id_is_detected() -> None:
    first = _record("R-1", "plan")
    second = first.model_copy(
        update={
            "payload": {"different": True},
            "content_sha256": canonical_sha256({"different": True}),
        }
    )
    result = reconstruct_operation(_request(), [first, second])
    assert result.status == ReconstructionStatus.CONFLICT
    assert any("conflicting immutable content" in item for item in result.conflicts)
