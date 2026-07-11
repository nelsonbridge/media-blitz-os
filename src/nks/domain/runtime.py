"""Runtime state report models for the Nelson Knowledge System."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeStatusReport:
    record_counts: dict[str, int]
    event_count: int
    graph_node_count: int
    graph_edge_count: int
    publication_readiness: dict[str, int]
    missing_references: list[str]
    orphan_records: list[str]

    def summary(self) -> str:
        lines = [
            "Runtime Status Summary",
            "",
            f"Total record types: {len(self.record_counts)}",
            f"Total canonical records: {sum(self.record_counts.values())}",
            f"Total workflow events: {self.event_count}",
            f"Graph nodes: {self.graph_node_count}",
            f"Graph edges: {self.graph_edge_count}",
            "",
            "Publication readiness:",
            f"  ready: {self.publication_readiness.get('ready', 0)}",
            f"  pending: {self.publication_readiness.get('pending', 0)}",
            "",
            f"Missing references: {len(self.missing_references)}",
            f"Orphan records: {len(self.orphan_records)}",
        ]
        return "\n".join(lines)
