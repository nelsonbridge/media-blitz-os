from __future__ import annotations

import json
from pathlib import Path

from nks.audit.repository import audit_repository


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_required_views(root: Path) -> None:
    generated = root / "generated"
    generated.mkdir(exist_ok=True)
    for filename, label in (
        ("publication-index.md", "Total publications: 0\n"),
        ("proof-index.md", "Total proof records: 0\n"),
        ("visual-package-index.md", "Total visual packages: 0\n"),
        ("visual-request-index.md", "Total visual requests: 0\n"),
        ("canonical-backlog.md", "Total work items: 0\n"),
        ("canonical-roadmap.md", "Total sprints: 0\n"),
    ):
        (generated / filename).write_text(label, encoding="utf-8")


def _records(root: Path) -> None:
    _write_json(
        root / "records" / "human-observations" / "OBS-1.json",
        {"observation_id": "OBS-1"},
    )
    _write_json(
        root / "records" / "approval-grants" / "APR-1.json",
        {"approval_id": "APR-1"},
    )
    _write_json(
        root / "records" / "reconciliation-findings" / "RF-1.json",
        {
            "finding_id": "RF-1",
            "observation_ids": ["OBS-1"],
            "relationship_ids": ["REL-1"],
        },
    )
    _write_json(
        root / "records" / "disclosure-receipts" / "DISC-1.json",
        {
            "disclosure_id": "DISC-1",
            "requested_finding_ids": ["RF-1"],
            "surfaced_finding_ids": ["RF-1"],
            "deferred_finding_ids": [],
            "withheld_finding_ids": [],
            "decisions": [{"finding_id": "RF-1"}],
        },
    )
    _write_json(
        root / "records" / "governed-transaction-events" / "TX-1_0001.json",
        {"event_id": "TX-1:0001"},
    )
    _write_json(
        root / "records" / "governed-transaction-receipts" / "TX-1.json",
        {"receipt_id": "GTR-TX-1"},
    )


def test_audit_recognizes_enki_record_families(tmp_path: Path) -> None:
    _records(tmp_path)
    _write_required_views(tmp_path)

    result = audit_repository(tmp_path)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.issue_count == 0
    assert payload["record_counts"]["approval-grants"] == 1
    assert payload["record_counts"]["reconciliation-findings"] == 1
    assert payload["record_counts"]["disclosure-receipts"] == 1
    assert payload["record_counts"]["governed-transaction-events"] == 1
    assert payload["record_counts"]["governed-transaction-receipts"] == 1
    assert payload["record_count"] == 6


def test_audit_detects_orphan_disclosure_finding(tmp_path: Path) -> None:
    _records(tmp_path)
    receipt = tmp_path / "records" / "disclosure-receipts" / "DISC-1.json"
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["surfaced_finding_ids"] = ["RF-MISSING"]
    _write_json(receipt, payload)
    _write_required_views(tmp_path)

    result = audit_repository(tmp_path)
    audit = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert any(
        "orphan reference: DISC-1.surfaced_finding_ids -> RF-MISSING" == issue
        for issue in audit["issues"]
    )


def test_audit_detects_decision_for_unrequested_finding(tmp_path: Path) -> None:
    _records(tmp_path)
    _write_json(
        tmp_path / "records" / "reconciliation-findings" / "RF-2.json",
        {
            "finding_id": "RF-2",
            "observation_ids": ["OBS-1"],
            "relationship_ids": ["REL-2"],
        },
    )
    receipt = tmp_path / "records" / "disclosure-receipts" / "DISC-1.json"
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["decisions"] = [{"finding_id": "RF-2"}]
    _write_json(receipt, payload)
    _write_required_views(tmp_path)

    result = audit_repository(tmp_path)
    audit = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert any(
        issue.startswith("disclosure decisions reference unrequested findings: DISC-1")
        for issue in audit["issues"]
    )
