"""Graph and audit builders for the Nelson Knowledge System."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nks.domain.graph import AuditReport, GraphEdge, GraphIndex, GraphNode
from nks.domain.models import (
    ArtifactRecord,
    CanonicalRecord,
    NarrativeRecord,
    ProofRecord,
    PublicationRecord,
    SourceRecord,
    VisualPackageRecord,
)


def _load_records(root: Path, collection: str, record_type: type[CanonicalRecord]) -> list[CanonicalRecord]:
    directory = root / collection
    if not directory.exists():
        return []
    return [record_type.model_validate_json(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.json"))]


def build_graph_index(root: Path) -> GraphIndex:
    sources = _load_records(root, "sources", SourceRecord)
    artifacts = _load_records(root, "artifacts", ArtifactRecord)
    proofs = _load_records(root, "proofs", ProofRecord)
    narratives = _load_records(root, "narratives", NarrativeRecord)
    visuals = _load_records(root, "visuals", VisualPackageRecord)
    publications = _load_records(root, "publications", PublicationRecord)

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    def add_node(record: CanonicalRecord, type_name: str) -> None:
        nodes.append(GraphNode(id=record.id, type=type_name, title=record.title, status=getattr(record, "status", None)))

    for record in sources:
        add_node(record, "source")
    for record in artifacts:
        add_node(record, "artifact")
    for record in proofs:
        add_node(record, "proof")
    for record in narratives:
        add_node(record, "narrative")
    for record in visuals:
        add_node(record, "visual")
    for record in publications:
        add_node(record, "publication")

    def add_edge(source_id: str, target_id: str, relation: str) -> None:
        if source_id and target_id:
            edges.append(GraphEdge(source_id=source_id, target_id=target_id, relation=relation))

    for artifact in artifacts:
        for source_id in artifact.source_ids:
            add_edge(source_id, artifact.id, "supports")
    for proof in proofs:
        add_edge(proof.artifact_id, proof.id, "validated_by")
    for narrative in narratives:
        add_edge(narrative.artifact_id, narrative.id, "narrativized_by")
    for visual in visuals:
        add_edge(visual.artifact_id, visual.id, "visualized_by")
        add_edge(visual.publication_id, visual.id, "packaged_by")
    for publication in publications:
        add_edge(publication.artifact_id, publication.id, "published_as")
        add_edge(publication.proof_id, publication.id, "proof_for")
        add_edge(publication.narrative_id, publication.id, "narrative_for")
        add_edge(publication.visual_package_id, publication.id, "visual_package_for")

    return GraphIndex(nodes=nodes, edges=edges)


def build_audit_report(root: Path) -> AuditReport:
    sources = _load_records(root, "sources", SourceRecord)
    artifacts = _load_records(root, "artifacts", ArtifactRecord)
    proofs = _load_records(root, "proofs", ProofRecord)
    narratives = _load_records(root, "narratives", NarrativeRecord)
    visuals = _load_records(root, "visuals", VisualPackageRecord)
    publications = _load_records(root, "publications", PublicationRecord)

    missing_references: list[str] = []
    orphan_records: list[str] = []
    ids = {record.id for record in sources + artifacts + proofs + narratives + visuals + publications}

    def check_reference(record_id: str | None, label: str) -> None:
        if record_id and record_id not in ids:
            missing_references.append(f"{label} references missing record {record_id}")

    for artifact in artifacts:
        for source_id in artifact.source_ids:
            check_reference(source_id, f"Artifact {artifact.id}")
    for proof in proofs:
        check_reference(proof.artifact_id, f"Proof {proof.id}")
    for narrative in narratives:
        check_reference(narrative.artifact_id, f"Narrative {narrative.id}")
    for visual in visuals:
        check_reference(visual.artifact_id, f"Visual {visual.id}")
        check_reference(visual.publication_id, f"Visual {visual.id}")
    for publication in publications:
        check_reference(publication.artifact_id, f"Publication {publication.id}")
        check_reference(publication.proof_id, f"Publication {publication.id}")
        check_reference(publication.narrative_id, f"Publication {publication.id}")
        check_reference(publication.visual_package_id, f"Publication {publication.id}")

    record_counts = {
        "sources": len(sources),
        "artifacts": len(artifacts),
        "proofs": len(proofs),
        "narratives": len(narratives),
        "visuals": len(visuals),
        "publications": len(publications),
    }

    def bucket_status(records: list[CanonicalRecord], status_field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in records:
            status = getattr(record, status_field, "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts

    proof_status = bucket_status(proofs, "gate_status")
    narrative_status = bucket_status(narratives, "gate_status")
    visual_status = bucket_status(visuals, "gate_status")

    publication_readiness = {
        "ready": 0,
        "pending": 0,
    }
    for publication in publications:
        if publication.editorial_status == "ready" and publication.user_approval == "approved":
            publication_readiness["ready"] += 1
        else:
            publication_readiness["pending"] += 1

    referenced: set[str] = set()
    for artifact in artifacts:
        for source_id in artifact.source_ids:
            referenced.add(source_id)
    for proof in proofs:
        referenced.add(proof.artifact_id)
    for narrative in narratives:
        referenced.add(narrative.artifact_id)
    for visual in visuals:
        referenced.add(visual.artifact_id)
        referenced.add(visual.publication_id)
    for publication in publications:
        referenced.add(publication.artifact_id)
        referenced.add(publication.proof_id)
        referenced.add(publication.narrative_id)
        referenced.add(publication.visual_package_id)

    for record in sources + artifacts + proofs + narratives + visuals + publications:
        if getattr(record, "id", None) not in referenced:
            orphan_records.append(record.id)

    return AuditReport(
        total_records=record_counts,
        publication_readiness=publication_readiness,
        proof_status=proof_status,
        narrative_status=narrative_status,
        visual_status=visual_status,
        missing_references=sorted(missing_references),
        orphan_records=sorted(orphan_records),
    )
