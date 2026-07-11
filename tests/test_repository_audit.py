from __future__ import annotations

import json
from pathlib import Path

from nks.audit.repository import audit_repository


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_empty_generated_views(root: Path, visual_request_count: int = 0) -> None:
    generated = root / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "publication-index.md").write_text(
        "Total publications: 0\n", encoding="utf-8"
    )
    (generated / "proof-index.md").write_text(
        "Total proof records: 0\n", encoding="utf-8"
    )
    (generated / "visual-package-index.md").write_text(
        "Total visual packages: 0\n", encoding="utf-8"
    )
    (generated / "visual-request-index.md").write_text(
        f"Total visual requests: {visual_request_count}\n", encoding="utf-8"
    )


def test_audit_generates_deterministic_census_and_integrity_report(tmp_path: Path):
    _write_json(
        tmp_path / "records" / "sources" / "NKS-SRC-000001.json",
        {
            "id": "NKS-SRC-000001",
            "title": "Source",
            "status": "approved",
            "source_type": "fixture",
            "source_location": "fixture.md",
        },
    )
    _write_json(
        tmp_path / "records" / "artifacts" / "NKS-ART-000001.json",
        {
            "id": "NKS-ART-000001",
            "title": "Artifact",
            "status": "review",
            "source_ids": ["NKS-SRC-000001"],
        },
    )
    _write_json(
        tmp_path / "records" / "publications" / "NKS-PUB-000001.json",
        {
            "id": "NKS-PUB-000001",
            "title": "Publication",
            "status": "review",
            "artifact_id": "NKS-ART-000001",
            "editorial_status": "ready",
            "user_approval": "needed",
        },
    )
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "publication-index.md").write_text(
        "Total publications: 1\n", encoding="utf-8"
    )
    (generated / "proof-index.md").write_text(
        "Total proof records: 0\n", encoding="utf-8"
    )
    (generated / "visual-package-index.md").write_text(
        "Total visual packages: 0\n", encoding="utf-8"
    )
    (generated / "visual-request-index.md").write_text(
        "Total visual requests: 0\n", encoding="utf-8"
    )

    first = audit_repository(tmp_path)
    first_json = first.json_path.read_text(encoding="utf-8")
    first_markdown = first.report_path.read_text(encoding="utf-8")
    second = audit_repository(tmp_path)

    assert second.json_path.read_text(encoding="utf-8") == first_json
    assert second.report_path.read_text(encoding="utf-8") == first_markdown
    assert first.file_count >= 7
    assert first.issue_count == 0
    assert "Canonical records: 3" in first_markdown
    assert "approval:needed" in first_markdown


def test_audit_accepts_collection_specific_request_identifiers(tmp_path: Path):
    _write_json(
        tmp_path / "records" / "visual-requests" / "NKS-VRQ-000001.json",
        {
            "request_id": "NKS-VRQ-000001",
            "asset_type": "diagram",
        },
    )
    _write_json(
        tmp_path / "records" / "social-requests" / "NKS-SOC-REQ-000001.json",
        {
            "request_id": "NKS-SOC-REQ-000001",
            "channel": "linkedin",
        },
    )
    _write_empty_generated_views(tmp_path, visual_request_count=1)

    result = audit_repository(tmp_path)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.issue_count == 0
    assert payload["record_count"] == 2
    assert "record missing identifier" not in result.report_path.read_text(
        encoding="utf-8"
    )


def test_audit_detects_duplicate_collection_specific_identifier(tmp_path: Path):
    _write_json(
        tmp_path / "records" / "visual-requests" / "first.json",
        {"request_id": "NKS-VRQ-000001"},
    )
    _write_json(
        tmp_path / "records" / "visual-requests" / "second.json",
        {"request_id": "NKS-VRQ-000001"},
    )
    _write_empty_generated_views(tmp_path, visual_request_count=1)

    result = audit_repository(tmp_path)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert any(
        issue == "duplicate record id: NKS-VRQ-000001"
        for issue in payload["issues"]
    )


def test_audit_detects_orphan_reference_and_stale_view(tmp_path: Path):
    _write_json(
        tmp_path / "records" / "publications" / "NKS-PUB-000001.json",
        {
            "id": "NKS-PUB-000001",
            "title": "Publication",
            "status": "review",
            "artifact_id": "NKS-ART-MISSING",
            "editorial_status": "needed",
            "user_approval": "needed",
        },
    )
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "publication-index.md").write_text(
        "Total publications: 99\n", encoding="utf-8"
    )

    result = audit_repository(tmp_path)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.issue_count >= 4
    assert any("orphan reference" in issue for issue in payload["issues"])
    assert any("may be stale" in issue for issue in payload["issues"])
    assert any("generated view missing" in issue for issue in payload["issues"])
