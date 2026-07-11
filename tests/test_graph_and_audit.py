import json
from pathlib import Path

from nks.application.graph import build_audit_report, build_graph_index


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_graph_index_and_audit_report(tmp_path: Path):
    records = tmp_path / "records"
    write_json(
        records / "sources" / "NKS-SRC-000001.json",
        {
            "id": "NKS-SRC-000001",
            "title": "Source Record",
            "status": "approved",
            "metadata": {},
            "source_type": "external",
            "source_location": "source.md",
            "limitations": [],
        },
    )
    write_json(
        records / "artifacts" / "NKS-ART-000001.json",
        {
            "id": "NKS-ART-000001",
            "title": "Artifact Record",
            "status": "review",
            "metadata": {},
            "source_ids": ["NKS-SRC-000001"],
            "proof_status": "needed",
            "narrative_status": "needed",
            "visual_status": "needed",
        },
    )
    write_json(
        records / "proofs" / "NKS-PRF-000001.json",
        {
            "id": "NKS-PRF-000001",
            "title": "Proof Record",
            "status": "review",
            "metadata": {},
            "artifact_id": "NKS-ART-000001",
            "category": "repository-derived",
            "supported_claims": [],
            "unsupported_claims": [],
            "citations_required": False,
            "gate_status": "ready",
        },
    )
    write_json(
        records / "narratives" / "NKS-NAR-000001.json",
        {
            "id": "NKS-NAR-000001",
            "title": "Narrative Record",
            "status": "review",
            "metadata": {},
            "artifact_id": "NKS-ART-000001",
            "recognition": "r",
            "reframe": "r",
            "framework": "f",
            "proof": "p",
            "application": "a",
            "consequence": "c",
            "invitation": "i",
            "gate_status": "ready",
        },
    )
    write_json(
        records / "visuals" / "NKS-VIS-000001.json",
        {
            "id": "NKS-VIS-000001",
            "title": "Visual Package",
            "status": "planned",
            "metadata": {},
            "artifact_id": "NKS-ART-000001",
            "publication_id": "NKS-PUB-000001",
            "signature_diagram_id": "NKS-DGM-000001",
            "hero_image_id": "NKS-HRO-000001",
            "asset_ids": ["NKS-DGM-000001", "NKS-HRO-000001"],
            "gate_status": "needed",
        },
    )
    write_json(
        records / "publications" / "NKS-PUB-000001.json",
        {
            "id": "NKS-PUB-000001",
            "title": "Publication Record",
            "status": "review",
            "metadata": {},
            "artifact_id": "NKS-ART-000001",
            "proof_id": "NKS-PRF-000001",
            "narrative_id": "NKS-NAR-000001",
            "visual_package_id": "NKS-VIS-000001",
            "draft_path": "publishing/drafts/NKS-PUB-000001.md",
            "editorial_status": "ready",
            "user_approval": "approved",
        },
    )

    graph = build_graph_index(records)
    audit = build_audit_report(records)

    assert any(node.id == "NKS-PUB-000001" for node in graph.nodes)
    assert any(edge.relation == "published_as" for edge in graph.edges)
    assert audit.total_records["publications"] == 1
    assert audit.publication_readiness["ready"] == 1
    assert audit.missing_references == []
