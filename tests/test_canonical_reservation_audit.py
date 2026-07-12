import json
from pathlib import Path

from nks.audit.repository import audit_repository


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_empty_views(root: Path) -> None:
    generated = root / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    for name, label in {
        "publication-index.md": "Total publications: 0",
        "proof-index.md": "Total proof records: 0",
        "visual-package-index.md": "Total visual packages: 0",
        "visual-request-index.md": "Total visual render requests: 0",
        "canonical-backlog.md": "Total work items: 0",
        "canonical-roadmap.md": "Total sprints: 0",
    }.items():
        (generated / name).write_text(label + "\n", encoding="utf-8")


def governed_source(content_hash: str = "a" * 64) -> dict:
    return {
        "id": "NKS-SRC-000004",
        "title": "Feedback source",
        "status": "review",
        "source_type": "external-feedback",
        "source_location": "records/feedback/NKS-FDB-000001.json",
        "limitations": ["Observation, not verified proof."],
        "metadata": {
            "feedback_id": "NKS-FDB-000001",
            "feedback_sha256": content_hash,
            "content_sha256": content_hash,
            "authorization_id": "NKS-AUTH-000001",
            "proof_review_id": "NKS-PRV-000001",
            "promotion_idempotency_key": "b" * 64,
            "canonical_reservation_id": "canonical-reservation:NKS-SRC-000004",
            "canonical_writer": "RestrictedCanonicalSourceWriter",
        },
    }


def committed_reservation(content_hash: str = "a" * 64) -> dict:
    return {
        "reservation_id": "canonical-reservation:NKS-SRC-000004",
        "target_source_id": "NKS-SRC-000004",
        "idempotency_key": "b" * 64,
        "authorization_id": "NKS-AUTH-000001",
        "subject_id": "NKS-FDB-000001",
        "content_sha256": content_hash,
        "mode": "NORMAL",
        "status": "COMMITTED",
        "reserved_at": "2026-07-12T20:40:00Z",
        "committed_at": "2026-07-12T20:40:01Z",
    }


def test_audit_reconstructs_committed_canonical_source(tmp_path: Path):
    write_json(
        tmp_path / "records" / "sources" / "NKS-SRC-000004.json",
        governed_source(),
    )
    write_json(
        tmp_path
        / "records"
        / "canonical-reservations"
        / "NKS-SRC-000004.json",
        committed_reservation(),
    )
    write_empty_views(tmp_path)

    result = audit_repository(tmp_path)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.issue_count == 0
    assert payload["record_counts"]["canonical-reservations"] == 1


def test_audit_detects_reservation_content_mismatch(tmp_path: Path):
    write_json(
        tmp_path / "records" / "sources" / "NKS-SRC-000004.json",
        governed_source("c" * 64),
    )
    write_json(
        tmp_path
        / "records"
        / "canonical-reservations"
        / "NKS-SRC-000004.json",
        committed_reservation("a" * 64),
    )
    write_empty_views(tmp_path)

    result = audit_repository(tmp_path)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert any(
        "source content hash mismatch" in issue for issue in payload["issues"]
    )
