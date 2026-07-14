from __future__ import annotations

from datetime import datetime, timezone

import pytest

from nks.adapters.forensic_evidence import ForensicEvidenceConflictError, JsonForensicEvidenceStore
from nks.application.forensic_reconstruction import ForensicRecord, build_portable_package, recover_portable_package
from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext


NOW = datetime(2026, 7, 14, 15, 0, tzinfo=timezone.utc)


def _record(record_id: str, payload: dict[str, object] | None = None) -> ForensicRecord:
    return ForensicRecord.create(
        record_id=record_id,
        record_type="transaction-receipt",
        operation_family="model-use",
        operation_id="OP-1",
        transaction_id="TX-1",
        execution_context=ExecutionContext.TEST,
        authority_class="HUMAN_ORIGIN_AUTHORITY",
        payload=payload or {
            "terminal_state": "COMMITTED",
            "output_sha256": canonical_sha256("output"),
        },
        recorded_at=NOW,
        lineage_ids=["SOURCE-1"],
    )


def test_clean_room_export_import_preserves_exact_authority_context_hashes_and_lineage(tmp_path) -> None:
    records = [_record("R-1"), _record("R-2", {"lineage": ["R-1"]})]
    package = build_portable_package(
        package_id="PKG-RECOVERY-1",
        execution_context=ExecutionContext.TEST,
        records=records,
        exported_at=NOW,
    )
    destination = JsonForensicEvidenceStore(tmp_path)
    receipt = recover_portable_package(
        package,
        destination=destination,
        destination_context=ExecutionContext.TEST,
        recovered_at=NOW,
    )
    assert receipt.record_count == 2
    assert receipt.exact_retry is False
    assert destination.list_records() == sorted(records, key=lambda item: item.record_id)
    assert destination.get("R-1").authority_class == "HUMAN_ORIGIN_AUTHORITY"
    assert destination.get("R-1").execution_context == ExecutionContext.TEST
    assert destination.get("R-1").lineage_ids == ["SOURCE-1"]


def test_disaster_recovery_exact_retry_is_idempotent(tmp_path) -> None:
    package = build_portable_package(
        package_id="PKG-RECOVERY-1",
        execution_context=ExecutionContext.TEST,
        records=[_record("R-1")],
        exported_at=NOW,
    )
    destination = JsonForensicEvidenceStore(tmp_path)
    first = recover_portable_package(
        package,
        destination=destination,
        destination_context=ExecutionContext.TEST,
        recovered_at=NOW,
    )
    retry = recover_portable_package(
        package,
        destination=destination,
        destination_context=ExecutionContext.TEST,
        recovered_at=NOW,
    )
    assert first.exact_retry is False
    assert retry.exact_retry is True
    assert retry.destination_evidence_sha256 == first.destination_evidence_sha256


def test_test_evidence_cannot_be_imported_as_production(tmp_path) -> None:
    package = build_portable_package(
        package_id="PKG-RECOVERY-1",
        execution_context=ExecutionContext.TEST,
        records=[_record("R-1")],
        exported_at=NOW,
    )
    with pytest.raises(PermissionError, match="cannot change execution context"):
        recover_portable_package(
            package,
            destination=JsonForensicEvidenceStore(tmp_path),
            destination_context=ExecutionContext.PRODUCTION,
            recovered_at=NOW,
        )


def test_conflicting_import_fails_closed(tmp_path) -> None:
    destination = JsonForensicEvidenceStore(tmp_path)
    original = _record("R-1")
    destination.append(original)
    conflicting = original.model_copy(
        update={
            "payload": {"tampered": True},
            "content_sha256": canonical_sha256({"tampered": True}),
        }
    )
    package = build_portable_package(
        package_id="PKG-CONFLICT",
        execution_context=ExecutionContext.TEST,
        records=[conflicting],
        exported_at=NOW,
    )
    with pytest.raises(ForensicEvidenceConflictError):
        recover_portable_package(
            package,
            destination=destination,
            destination_context=ExecutionContext.TEST,
            recovered_at=NOW,
        )
