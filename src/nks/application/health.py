"""Corpus health reporting and dashboard diagnostics."""

from __future__ import annotations

from pathlib import Path

from nks.application.graph import build_audit_report
from nks.domain.health import CorpusHealthReport, HealthDimension


def build_corpus_health(root: Path) -> CorpusHealthReport:
    audit = build_audit_report(root)

    dimensions = [
        HealthDimension(
            id="source-lineage",
            title="Source Lineage Coverage",
            score=min(5, max(0, audit.total_records.get("sources", 0))),
            notes="Track artifacts back to source lineage.",
        ),
        HealthDimension(
            id="proof-boundary",
            title="Proof Boundary Coverage",
            score=min(5, max(0, audit.total_records.get("proofs", 0))),
            notes="Proof boundaries should exist for artifacts.",
        ),
        HealthDimension(
            id="relationship-density",
            title="Relationship Density",
            score=min(5, max(0, audit.total_records.get("publications", 0))),
            notes="More linked outputs increase relationship density.",
        ),
        HealthDimension(
            id="graph-coverage",
            title="Graph Coverage",
            score=min(5, max(0, audit.total_records.get("visuals", 0))),
            notes="Graph coverage grows as visuals and publications link records.",
        ),
        HealthDimension(
            id="orphan-control",
            title="Orphan Control",
            score=max(0, 5 - len(audit.orphan_records)),
            notes="Fewer orphans indicate stronger corpus control.",
        ),
    ]

    return CorpusHealthReport(dimensions=dimensions)
