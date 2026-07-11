import json
from pathlib import Path

from nks.application.runtime import build_runtime_status
from nks.domain.models import WorkflowEvent
from nks.views.markdown import render_audit_report, render_graph_index


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def test_runtime_status_report_counts(tmp_path: Path):
    records = tmp_path / "records"
    write_json(
        records / "sources" / "NKS-SRC-000001.json",
        {
            "id": "NKS-SRC-000001",
            "title": "Source Record",
            "status": "approved",
            "metadata": {},
            "source_type": "external",
            "source_location": "source.md",
            "limitations": [],
        },
    )
    write_json(
        records / "artifacts" / "NKS-ART-000001.json",
        {
            "id": "NKS-ART-000001",
            "title": "Artifact Record",
            "status": "review",
            "metadata": {},
            "source_ids": ["NKS-SRC-000001"],
            "proof_status": "needed",
            "narrative_status": "needed",
            "visual_status": "needed",
        },
    )
    write_json(
        records / "publications" / "NKS-PUB-000001.json",
        {
            "id": "NKS-PUB-000001",
            "title": "Publication Record",
            "status": "review",
            "metadata": {},
            "artifact_id": "NKS-ART-000001",
            "proof_id": "NKS-PRF-000001",
            "narrative_id": "NKS-NAR-000001",
            "visual_package_id": "NKS-VIS-000001",
            "draft_path": "publishing/drafts/NKS-PUB-000001.md",
            "editorial_status": "ready",
            "user_approval": "approved",
        },
    )
    write_event(
        tmp_path / "events" / "events.jsonl",
        {
            "event_id": "test.event:1",
            "event_type": "test.event",
            "subject_id": "NKS-PUB-000001",
            "payload": {"test": 1},
        },
    )

    report = build_runtime_status(tmp_path)

    assert report.event_count == 1
    assert report.record_counts["publications"] == 1
    assert report.graph_node_count >= 1
    assert report.graph_edge_count >= 0
    assert report.publication_readiness["ready"] == 1
    assert report.missing_references


def test_graph_and_audit_views_render(tmp_path: Path):
    records = tmp_path / "records"
    write_json(
        records / "publications" / "NKS-PUB-000001.json",
        {
            "id": "NKS-PUB-000001",
            "title": "Test Publication",
            "status": "review",
            "metadata": {},
            "artifact_id": "NKS-ART-000001",
            "proof_id": "NKS-PRF-000001",
            "narrative_id": "NKS-NAR-000001",
            "visual_package_id": "NKS-VIS-000001",
            "draft_path": "publishing/drafts/NKS-PUB-000001.md",
            "editorial_status": "ready",
            "user_approval": "approved",
        },
    )
    graph_markdown = render_graph_index(records)
    audit_markdown = render_audit_report(records)

    assert "# Generated Knowledge Graph Index" in graph_markdown
    assert "# Generated Audit Report" in audit_markdown
    assert "Publication Readiness" in audit_markdown
