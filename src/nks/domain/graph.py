"""Knowledge graph domain models for the Nelson Knowledge System."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: str
    title: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    relation: str


@dataclass(frozen=True)
class GraphIndex:
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@dataclass(frozen=True)
class AuditReport:
    total_records: dict[str, int]
    publication_readiness: dict[str, int]
    proof_status: dict[str, int]
    narrative_status: dict[str, int]
    visual_status: dict[str, int]
    missing_references: list[str]
    orphan_records: list[str]
