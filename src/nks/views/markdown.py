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
        "| Feedback ID | Publication | Platform | Classification | Promoted Source |",
        "|---|---|---|---|---|",
    ]
    for item in records:
        lines.append(
            "| {feedback_id} | {publication_id} | {platform} | {classification} | {promoted} |".format(
                **item, promoted=item.get("promoted_to_source_id") or "—"
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
        output_root / "ecosystem-capabilities.md": render_capability_summary(
            records_root / "capabilities" / "ecosystem-capabilities.json"
        ),
    }
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    return sorted(outputs)
