"""Health dashboard generation for the Nelson Knowledge System."""

from __future__ import annotations

from pathlib import Path

from nks.application.health import build_corpus_health


def render_corpus_health_dashboard(root: Path) -> str:
    health = build_corpus_health(root)
    lines = [
        "# Corpus Health Dashboard",
        "",
        "> Generated from corpus health metrics and audit signals. Do not edit manually.",
        "",
        f"Total score: {health.total_score} / {health.max_score}",
        f"Percentage: {health.percentage()}%",
        "",
        "## Health Dimensions",
        "",
        "| Dimension | Score | Max | Notes |",
        "|---|---:|---:|---|",
    ]
    for dimension in health.dimensions:
        lines.append(
            f"| {dimension.title} | {dimension.score} | {dimension.max_score} | {dimension.notes} |"
        )
    lines.extend(["", "## Notes", "", "- This dashboard is generated from canonical corpus state and audit results.", ""])
    return "\n".join(lines)
