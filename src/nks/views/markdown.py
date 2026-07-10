"""Deterministic human-readable views generated from canonical JSON records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_records(root: Path, collection: str) -> list[dict[str, Any]]:
    directory = root / collection
    if not directory.exists():
        return []
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.json"))
    ]


def _string_value(item: dict[str, Any], key: str, default: str = "—") -> str:
    value = item.get(key, default)
    return str(value) if value is not None else default


def _render_table(
    title: str,
    source_note: str,
    headers: list[str],
    row_formatter: callable,
    count_label: str,
    records: list[dict[str, Any]],
) -> str:
    lines = [
        f"# Generated {title}",
        "",
        source_note,
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend(row_formatter(item) for item in records)
    lines.extend(["", f"Total {count_label}: {len(records)}", ""])
    return "\n".join(lines)


def render_publication_index(root: Path) -> str:
    records = _load_records(root / "canonical", "publications")

    def row(item: dict[str, Any]) -> str:
        return "| {id} | {title} | {artifact} | {status} | {editorial} | {approval} | {draft} |".format(
            id=_string_value(item, "id"),
            title=_string_value(item, "title"),
            artifact=_string_value(item, "artifact_id"),
            status=_string_value(item, "status"),
            editorial=_string_value(item, "editorial_status"),
            approval=_string_value(item, "user_approval"),
            draft=_string_value(item, "draft_path"),
        )

    return _render_table(
        "Publication Index",
        "> Generated from `records/canonical/publications/*.json`. Do not edit manually.",
        [
            "Publication ID",
            "Title",
            "Artifact",
            "Status",
            "Editorial",
            "User Approval",
            "Draft Path",
        ],
        row,
        "publications",
        records,
    )


def render_proof_index(root: Path) -> str:
    records = _load_records(root / "canonical", "proofs")

    def row(item: dict[str, Any]) -> str:
        return "| {id} | {title} | {artifact} | {category} | {gate} | {citations} |".format(
            id=_string_value(item, "id"),
            title=_string_value(item, "title"),
            artifact=_string_value(item, "artifact_id"),
            category=_string_value(item, "category"),
            gate=_string_value(item, "gate_status"),
            citations=_string_value(item, "citations_required"),
        )

    return _render_table(
        "Proof Index",
        "> Generated from `records/canonical/proofs/*.json`. Do not edit manually.",
        ["Proof ID", "Title", "Artifact", "Category", "Gate", "Citations Required"],
        row,
        "proof records",
        records,
    )


def render_visual_index(root: Path) -> str:
    records = _load_records(root / "canonical", "visuals")

    def row(item: dict[str, Any]) -> str:
        return "| {id} | {title} | {publication} | {artifact} | {signature} | {hero} | {gate} | {assets} |".format(
            id=_string_value(item, "id"),
            title=_string_value(item, "title"),
            publication=_string_value(item, "publication_id"),
            artifact=_string_value(item, "artifact_id"),
            signature=_string_value(item, "signature_diagram_id"),
            hero=_string_value(item, "hero_image_id"),
            gate=_string_value(item, "gate_status"),
            assets=str(len(item.get("asset_ids", []))),
        )

    return _render_table(
        "Visual Package Index",
        "> Generated from `records/canonical/visuals/*.json`. Do not edit manually.",
        [
            "Visual Package ID",
            "Title",
            "Publication",
            "Artifact",
            "Signature Diagram",
            "Hero Image",
            "Gate",
            "Assets",
        ],
        row,
        "visual packages",
        records,
    )


def render_visual_request_index(root: Path) -> str:
    records = _load_records(root / "requests", "visual-requests")

    def row(item: dict[str, Any]) -> str:
        return "| {request_id} | {visual_id} | {publication_id} | {asset_type} | {dimensions} | {review_required} |".format(
            request_id=_string_value(item, "request_id"),
            visual_id=_string_value(item, "visual_id"),
            publication_id=_string_value(item, "publication_id"),
            asset_type=_string_value(item, "asset_type"),
            dimensions=_string_value(item, "dimensions"),
            review_required=str(item.get("metadata", {}).get("review_required", False)),
        )

    return _render_table(
        "Visual Render Request Index",
        "> Generated from `records/requests/visual-requests/*.json`. Do not edit manually.",
        [
            "Request ID",
            "Visual ID",
            "Publication",
            "Asset Type",
            "Dimensions",
            "Review Required",
        ],
        row,
        "visual render requests",
        records,
    )


def render_feedback_index(root: Path) -> str:
    records = _load_records(root, "feedback")

    def row(item: dict[str, Any]) -> str:
        return "| {feedback_id} | {publication_id} | {platform} | {classification} | {promoted} |".format(
            feedback_id=_string_value(item, "feedback_id"),
            publication_id=_string_value(item, "publication_id"),
            platform=_string_value(item, "platform"),
            classification=_string_value(item, "classification"),
            promoted=_string_value(item, "promoted_to_source_id", "—"),
        )

    return _render_table(
        "Feedback Index",
        "> Generated from `records/feedback/*.json`. Do not edit manually.",
        ["Feedback ID", "Publication", "Platform", "Classification", "Promoted Source"],
        row,
        "feedback records",
        records,
    )


def render_event_index(root: Path) -> str:
    records = _load_records(root, "events")

    def row(item: dict[str, Any]) -> str:
        return "| {event_id} | {event_type} | {subject_id} | {payload_count} |".format(
            event_id=_string_value(item, "event_id"),
            event_type=_string_value(item, "event_type"),
            subject_id=_string_value(item, "subject_id"),
            payload_count=str(len(item.get("payload", {}))),
        )

    return _render_table(
        "Workflow Event Index",
        "> Generated from `records/events/*.json`. Do not edit manually.",
        ["Event ID", "Event Type", "Subject ID", "Payload Fields"],
        row,
        "workflow events",
        records,
    )


def render_capability_summary(registry_path: Path) -> str:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    capabilities = sorted(registry.get("capabilities", []), key=lambda item: item["id"])
    lines = [
        "# Generated Ecosystem Capability Summary",
        "",
        "> Generated from `records/canonical/capabilities/ecosystem-capabilities.json`. Do not edit manually.",
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
        output_root / "ecosystem-capabilities.md": render_capability_summary(
            records_root / "canonical" / "capabilities" / "ecosystem-capabilities.json"
        ),
    }
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    return sorted(outputs)
