"""Runtime state generation and diagnostics."""

from __future__ import annotations

from pathlib import Path

from nks.application.graph import build_audit_report, build_graph_index
from nks.domain.models import WorkflowEvent
from nks.domain.runtime import RuntimeStatusReport


def _load_events(root: Path) -> list[WorkflowEvent]:
    events_file = root / "events" / "events.jsonl"
    if not events_file.exists():
        return []
    return [
        WorkflowEvent.model_validate_json(line)
        for line in events_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_runtime_status(root: Path) -> RuntimeStatusReport:
    records_root = root / "records"
    graph = build_graph_index(records_root)
    audit = build_audit_report(records_root)
    events = _load_events(root)

    return RuntimeStatusReport(
        record_counts=audit.total_records,
        event_count=len(events),
        graph_node_count=len(graph.nodes),
        graph_edge_count=len(graph.edges),
        publication_readiness=audit.publication_readiness,
        missing_references=audit.missing_references,
        orphan_records=audit.orphan_records,
    )
