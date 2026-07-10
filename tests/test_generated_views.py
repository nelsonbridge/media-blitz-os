import json
from pathlib import Path

from nks.views.markdown import (
    render_capability_summary,
    render_proof_index,
    render_publication_index,
    render_visual_index,
    write_generated_views,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_generated_views_are_deterministic_and_record_driven(tmp_path: Path):
    records = tmp_path / "records"
    write_json(
        records / "publications" / "NKS-PUB-000001.json",
        {
            "id": "NKS-PUB-000001",
            "title": "The Corpus Is Manufactured, Not Found",
            "artifact_id": "NKS-ART-000001",
            "status": "review",
            "editorial_status": "ready",
            "user_approval": "needed",
            "draft_path": "publishing/drafts/NKS-PUB-000001.md",
        },
    )
    write_json(
        records / "proofs" / "NKS-PRF-000001.json",
        {
            "id": "NKS-PRF-000001",
            "title": "Proof Boundary",
            "artifact_id": "NKS-ART-000001",
            "category": "repository-derived",
            "gate_status": "ready",
            "citations_required": False,
        },
    )
    write_json(
        records / "visuals" / "NKS-VIS-000001.json",
        {
            "id": "NKS-VIS-000001",
            "title": "Visual Package",
            "publication_id": "NKS-PUB-000001",
            "artifact_id": "NKS-ART-000001",
            "signature_diagram_id": "NKS-DGM-000001",
            "hero_image_id": "NKS-HRO-000001",
            "gate_status": "ready",
            "asset_ids": ["NKS-DGM-000001", "NKS-HRO-000001"],
        },
    )
    write_json(
        records / "capabilities" / "ecosystem-capabilities.json",
        {
            "registry_id": "NKS-CAP-REGISTRY-0001",
            "version": 1,
            "capabilities": [
                {
                    "id": "NKS-CAP-GITHUB",
                    "name": "GitHub",
                    "status": "available",
                    "reliability": "high",
                    "canonical_authority": True,
                    "adapter_boundary": "repository-adapter",
                }
            ],
        },
    )

    first = write_generated_views(tmp_path)
    first_content = {path.name: path.read_text(encoding="utf-8") for path in first}
    second = write_generated_views(tmp_path)
    second_content = {path.name: path.read_text(encoding="utf-8") for path in second}

    assert first_content == second_content
    assert "NKS-PUB-000001" in render_publication_index(records)
    assert "user approval" in render_publication_index(records).lower()
    assert "NKS-PRF-000001" in render_proof_index(records)
    assert "Total visual packages: 1" in render_visual_index(records)
    assert "NKS-CAP-GITHUB" in render_capability_summary(
        records / "capabilities" / "ecosystem-capabilities.json"
    )


def test_empty_collections_render_zero_counts(tmp_path: Path):
    assert "Total publications: 0" in render_publication_index(tmp_path)
    assert "Total proof records: 0" in render_proof_index(tmp_path)
    assert "Total visual packages: 0" in render_visual_index(tmp_path)
