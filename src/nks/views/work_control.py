"""Deterministic human-readable projections for canonical work control state."""

from __future__ import annotations

from pathlib import Path

from nks.adapters.work_control import JsonWorkControlRepository

GENERATED_WARNING = "> Generated from canonical work-control records. Do not edit manually."


def render_backlog(root: Path) -> str:
    repository = JsonWorkControlRepository(root)
    records = repository.list_work_items()
    lines = ["# Canonical Backlog", "", GENERATED_WARNING, ""]
    lines.extend(
        [
            "| ID | Status | Sprint | Title | Evidence |",
            "|---|---|---|---|---:|",
        ]
    )
    for record in records:
        lines.append(
            f"| {record.work_item_id} | {record.status.value} | "
            f"{record.sprint_id or '-'} | {record.title} | {len(record.evidence)} |"
        )
    lines.extend(["", f"Total work items: {len(records)}", ""])
    return "\n".join(lines)


def render_roadmap(root: Path) -> str:
    repository = JsonWorkControlRepository(root)
    records = repository.list_sprints()
    lines = ["# Canonical Sprint Roadmap", "", GENERATED_WARNING, ""]
    for record in records:
        lines.extend(
            [
                f"## Sprint {record.sequence} — {record.title}",
                "",
                f"- ID: `{record.sprint_id}`",
                f"- Status: `{record.status.value}`",
                f"- Objective: {record.objective}",
                f"- Work items: {', '.join(record.work_item_ids)}",
                f"- Evidence records: {len(record.evidence)}",
                "",
                "Exit criteria:",
                "",
            ]
        )
        lines.extend(f"- {criterion}" for criterion in record.exit_criteria)
        lines.append("")
    lines.extend([f"Total sprints: {len(records)}", ""])
    return "\n".join(lines)


def write_work_control_views(root: Path) -> list[Path]:
    generated = root / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    outputs = {
        generated / "canonical-backlog.md": render_backlog(root),
        generated / "canonical-roadmap.md": render_roadmap(root),
    }
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    return sorted(outputs)
