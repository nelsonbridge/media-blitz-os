"""Deterministic human-readable views generated from canonical JSON records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nks.application.graph import build_audit_report, build_graph_index
from nks.application.runtime import build_runtime_status
from nks.domain.delivery import PublicationReceipt
from nks.views.health import render_corpus_health_dashboard
from nks.views.health import render_corpus_health_dashboard


def _load_records(root: Path, collection: str) -> list[dict[str, Any]]:
    directory = root / collection
    if not directory.exists():
        return []
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.json"))
    ]


def render_publication_index(root: Path) -> str:
    records = _load_records(root, "publications")
    lines = [
        "# Generated Publication Index",
        "",
        "> Generated from `records/publications/*.json`. Do not edit manually.",
        "",
        "| Publication ID | Title | Artifact | Status | Editorial | User Approval | Draft Path |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in records:
        lines.append(
            "| {id} | {title} | {artifact_id} | {status} | {editorial_status} | "
            "{user_approval} | {draft_path} |".format(**item)
        )
    lines.extend(["", f"Total publications: {len(records)}", ""])
    return "\n".join(lines)


def render_proof_index(root: Path) -> str:
    records = _load_records(root, "proofs")
    lines = [
        "# Generated Proof Index",
        "",
        "> Generated from `records/proofs/*.json`. Do not edit manually.",
        "",
        "| Proof ID | Title | Artifact | Category | Gate | Citations Required |",
        "|---|---|---|---|---|---|",
    ]
    for item in records:
        lines.append(
            "| {id} | {title} | {artifact_id} | {category} | {gate_status} | {citations_required} |".format(
                **item
            )
        )
    lines.extend(["", f"Total proof records: {len(records)}", ""])
    return "\n".join(lines)


def render_visual_index(root: Path) -> str:
    records = _load_records(root, "visuals")
    lines = [
        "# Generated Visual Package Index",
        "",
        "> Generated from `records/visuals/*.json`. Do not edit manually.",
        "",
        "| Visual Package ID | Title | Publication | Artifact | Signature Diagram | Hero Image | Gate | Assets |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for item in records:
        lines.append(
            "| {id} | {title} | {publication_id} | {artifact_id} | {signature_diagram_id} | "
            "{hero_image_id} | {gate_status} | {asset_count} |".format(
                **item, asset_count=len(item.get("asset_ids", []))
            )
        )
    lines.extend(["", f"Total visual packages: {len(records)}", ""])
    return "\n".join(lines)


def render_visual_request_index(root: Path) -> str:
    records = _load_records(root, "visual-requests")
    lines = [
        "# Generated Visual Render Request Index",
        "",
        "> Generated from `records/visual-requests/*.json`. Do not edit manually.",
        "",
        "| Request ID | Visual ID | Publication | Asset Type | Dimensions | Review Required |",
        "|---|---|---|---|---|---|",
    ]
    for item in records:
        lines.append(
            "| {request_id} | {visual_id} | {publication_id} | {asset_type} | {dimensions} | {review_required} |".format(
                **item, review_required=item.get("metadata", {}).get("review_required", False)
            )
        )
    lines.extend(["", f"Total visual render requests: {len(records)}", ""])
    return "\n".join(lines)


def render_feedback_index(root: Path) -> str:
    records = _load_records(root, "feedback")
    lines = [
        "# Generated Feedback Index",
        "",
        "> Generated from `records/feedback/*.json`. Do not edit manually.",
        "",
        "| Feedback ID | Publication | Platform | Classification | Provenance | Promoted Source |",
        "|---|---|---|---|---|---|",
    ]
    for item in records:
        lines.append(
            "| {feedback_id} | {publication_id} | {platform} | {classification} | {provenance} | {promoted} |".format(
                **item,
                provenance=item.get("provenance", "real"),
                promoted=item.get("promoted_to_source_id") or "—",
            )
        )
    lines.extend(["", f"Total feedback records: {len(records)}", ""])
    return "\n".join(lines)


def render_event_index(root: Path) -> str:
    records = _load_records(root, "events")
    lines = [
        "# Generated Workflow Event Index",
        "",
        "> Generated from `records/events/*.json`. Do not edit manually.",
        "",
        "| Event ID | Event Type | Subject ID | Payload Fields |",
        "|---|---|---|---:|",
    ]
    for item in records:
        lines.append(
            "| {event_id} | {event_type} | {subject_id} | {payload_count} |".format(
                **item, payload_count=len(item.get("payload", {}))
            )
        )
    lines.extend(["", f"Total workflow events: {len(records)}", ""])
    return "\n".join(lines)


def render_graph_index(root: Path) -> str:
    graph = build_graph_index(root)
    lines = [
        "# Generated Knowledge Graph Index",
        "",
        "> Generated from canonical records. Do not edit manually.",
        "",
        f"Total nodes: {len(graph.nodes)}",
        f"Total edges: {len(graph.edges)}",
        "",
        "## Nodes",
        "",
        "| ID | Type | Title | Status |",
        "|---|---|---|---|",
    ]
    for node in sorted(graph.nodes, key=lambda item: item.id):
        title = node.title or "—"
        status = node.status or "—"
        lines.append(f"| {node.id} | {node.type} | {title} | {status} |")
    lines.extend(["", "## Edges", "", "| Source | Relation | Target |", "|---|---|---|"])
    for edge in sorted(graph.edges, key=lambda item: (item.source_id, item.relation, item.target_id)):
        lines.append(f"| {edge.source_id} | {edge.relation} | {edge.target_id} |")
    lines.extend(["", f"Total nodes: {len(graph.nodes)}", f"Total edges: {len(graph.edges)}", ""])
    return "\n".join(lines)


def render_audit_report(root: Path) -> str:
    report = build_audit_report(root)
    lines = [
        "# Generated Audit Report",
        "",
        "> Generated from canonical records. Do not edit manually.",
        "",
        "## Record Counts",
        "",
        "| Record Type | Count |",
        "|---|---:|",
    ]
    for record_type, count in sorted(report.total_records.items()):
        lines.append(f"| {record_type} | {count} |")
    lines.extend([
        "",
        "## Publication Readiness",
        "",
        "| State | Count |",
        "|---|---:|",
        f"| ready | {report.publication_readiness.get('ready', 0)} |",
        f"| pending | {report.publication_readiness.get('pending', 0)} |",
        "",
        "## Proof Status",
        "",
        "| Status | Count |",
        "|---|---:|",
    ])
    for status, count in sorted(report.proof_status.items()):
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "## Narrative Status",
        "",
        "| Status | Count |",
        "|---|---:|",
    ])
    for status, count in sorted(report.narrative_status.items()):
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "## Visual Status",
        "",
        "| Status | Count |",
        "|---|---:|",
    ])
    for status, count in sorted(report.visual_status.items()):
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "## Missing References",
        "",
    ])
    if report.missing_references:
        lines.extend(f"- {item}" for item in report.missing_references)
    else:
        lines.append("- None")
    lines.extend(["", "## Orphan Records", "",])
    if report.orphan_records:
        lines.extend(f"- {item}" for item in report.orphan_records)
    else:
        lines.append("- None")
    lines.extend(["", f"Total records: {sum(report.total_records.values())}", ""])
    return "\n".join(lines)


def render_runtime_status_report(root: Path) -> str:
    status = build_runtime_status(root)
    lines = [
        "# Generated Runtime Status Report",
        "",
        "> Generated from canonical records, workflow events, and graph/audit state. Do not edit manually.",
        "",
        "## Summary",
        "",
        f"Total canonical records: {sum(status.record_counts.values())}",
        f"Total event records: {status.event_count}",
        f"Graph nodes: {status.graph_node_count}",
        f"Graph edges: {status.graph_edge_count}",
        "",
        "## Publication Readiness",
        "",
        "| State | Count |",
        "|---|---:|",
        f"| ready | {status.publication_readiness.get('ready', 0)} |",
        f"| pending | {status.publication_readiness.get('pending', 0)} |",
        "",
        "## Missing References",
        "",
    ]
    if status.missing_references:
        lines.extend(f"- {item}" for item in status.missing_references)
    else:
        lines.append("- None")
    lines.extend(["", "## Orphan Records", "",])
    if status.orphan_records:
        lines.extend(f"- {item}" for item in status.orphan_records)
    else:
        lines.append("- None")
    lines.extend(["", "## Record Counts", "", "| Record Type | Count |", "|---|---:|"])
    for record_type, count in sorted(status.record_counts.items()):
        lines.append(f"| {record_type} | {count} |")
    lines.extend(["", f"Total records: {sum(status.record_counts.values())}", ""])
    return "\n".join(lines)


def render_publication_package_index(repository_root: Path) -> str:
    package_dirs = sorted(repository_root.glob("*/*/receipt.json"))
    packages: list[PublicationReceipt] = []
    for path in package_dirs:
        packages.append(
            PublicationReceipt.model_validate_json(path.read_text(encoding="utf-8"))
        )

    lines = [
        "# Generated Publication Package Index",
        "",
        "> Generated from manual publication package receipts. Do not edit manually.",
        "",
        "| Publication ID | Platform | Receipt ID | Status | Package Path |",
        "|---|---|---|---|---|",
    ]
    for receipt in packages:
        lines.append(
            "| {publication_id} | {platform} | {receipt_id} | {status} | {path} |".format(
                publication_id=receipt.publication_id,
                platform=receipt.platform,
                receipt_id=receipt.receipt_id,
                status=receipt.status,
                path=receipt.metadata.get("package_path", "-"),
            )
        )
    lines.extend(["", f"Total publication packages: {len(packages)}", ""])
    return "\n".join(lines)


def render_capability_summary(registry_path: Path) -> str:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    capabilities = sorted(registry.get("capabilities", []), key=lambda item: item["id"])
    lines = [
        "# Generated Ecosystem Capability Summary",
        "",
        "> Generated from `records/capabilities/ecosystem-capabilities.json`. Do not edit manually.",
        "",
        f"Registry: {registry['registry_id']} — version {registry['version']}",
        "",
        "| Capability ID | Name | Status | Reliability | Canonical | Adapter Boundary |",
        "|---|---|---|---|---|---|",
    ]
    for item in capabilities:
        lines.append(
            "| {id} | {name} | {status} | {reliability} | {canonical_authority} | {adapter_boundary} |".format(
                **item
            )
        )
    lines.extend(["", f"Total capabilities: {len(capabilities)}", ""])
    return "\n".join(lines)


def write_generated_views(repository_root: Path) -> list[Path]:
    records_root = repository_root / "records"
    output_root = repository_root / "generated"
    output_root.mkdir(parents=True, exist_ok=True)

    outputs = {
        output_root / "publication-index.md": render_publication_index(records_root),
        output_root / "proof-index.md": render_proof_index(records_root),
        output_root / "visual-package-index.md": render_visual_index(records_root),
        output_root / "visual-request-index.md": render_visual_request_index(records_root),
        output_root / "feedback-index.md": render_feedback_index(records_root),
        output_root / "event-index.md": render_event_index(records_root),
        output_root / "graph-index.md": render_graph_index(records_root),
        output_root / "audit-report.md": render_audit_report(records_root),
        output_root / "runtime-status-report.md": render_runtime_status_report(records_root),
        output_root / "corpus-health-dashboard.md": render_corpus_health_dashboard(records_root),
        output_root / "publication-package-index.md": render_publication_package_index(repository_root),
        output_root / "ecosystem-capabilities.md": render_capability_summary(
            records_root / "capabilities" / "ecosystem-capabilities.json"
        ),
    }
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    return sorted(outputs)
