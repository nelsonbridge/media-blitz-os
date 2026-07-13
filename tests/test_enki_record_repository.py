from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from nks.adapters.enki_records import JsonEnkiRecordRepository, RecordConflictError
from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    DisclosureAction,
    DisclosureDecision,
    FindingKind,
    ReconciliationFinding,
    SubjectRef,
)
from nks.enki.disclosure import DisclosureAudience, DisclosureReceipt


def _now() -> datetime:
    return datetime(2026, 7, 14, 3, 0, tzinfo=timezone.utc)


def _finding(summary: str = "A recorded divergence exists.") -> ReconciliationFinding:
    return ReconciliationFinding(
        finding_id="RF-1",
        subject=SubjectRef(subject_id="SUBJECT-1", subject_type="PERSON"),
        domain="career",
        finding_kind=FindingKind.DIVERGENCE,
        summary=summary,
        observation_ids=["OBS-1"],
        relationship_ids=["REL-1"],
        evidence_ids=["E-1"],
        objective_refs=["OBJ-1"],
        priority_refs=["PRI-1"],
        confidence=ConfidenceAssertion(
            level=ConfidenceLevel.HIGH,
            rationale="Supported by attributable evidence.",
            evidence_ids=["E-1"],
        ),
        created_at=_now(),
        interpretation_version="enki-test/v1",
    )


def _receipt() -> DisclosureReceipt:
    return DisclosureReceipt(
        disclosure_id="DISC-1",
        subject=SubjectRef(subject_id="SUBJECT-1", subject_type="PERSON"),
        domain="career",
        audience=DisclosureAudience.SUBJECT,
        purpose="answer the subject's question",
        requested_finding_ids=["RF-1"],
        surfaced_finding_ids=["RF-1"],
        deferred_finding_ids=[],
        withheld_finding_ids=[],
        decisions=[
            DisclosureDecision(
                finding_id="RF-1",
                action=DisclosureAction.SURFACE,
                reasons=["requested and attributable"],
                decided_at=_now(),
                policy_version="disclosure-test/v1",
            )
        ],
        content_sha256="sha256:" + "1" * 64,
        policy_version="disclosure-test/v1",
    )


def test_findings_are_append_only_and_idempotent(tmp_path: Path) -> None:
    repository = JsonEnkiRecordRepository(tmp_path)
    finding = _finding()

    repository.append_findings([finding])
    repository.append_findings([finding])

    assert repository.get_finding("RF-1") == finding
    assert repository.list_findings() == [finding]
    assert len(list((tmp_path / "records" / "reconciliation-findings").glob("*.json"))) == 1


def test_different_content_under_existing_finding_id_fails(tmp_path: Path) -> None:
    repository = JsonEnkiRecordRepository(tmp_path)
    repository.append_findings([_finding()])

    with pytest.raises(RecordConflictError, match="immutable record id"):
        repository.append_findings([_finding("A materially different finding.")])


def test_disclosure_receipts_are_append_only_and_readable(tmp_path: Path) -> None:
    repository = JsonEnkiRecordRepository(tmp_path)
    receipt = _receipt()

    repository.append_disclosure_receipt(receipt)
    repository.append_disclosure_receipt(receipt)

    assert repository.get_disclosure_receipt("DISC-1") == receipt
    assert repository.list_disclosure_receipts() == [receipt]


def test_safe_identifier_cannot_escape_collection(tmp_path: Path) -> None:
    repository = JsonEnkiRecordRepository(tmp_path)
    finding = _finding().model_copy(update={"finding_id": "../RF-1"})

    repository.append_findings([finding])

    assert (tmp_path / "records" / "reconciliation-findings" / ".._RF-1.json").exists()
    assert not (tmp_path / "records" / "RF-1.json").exists()
