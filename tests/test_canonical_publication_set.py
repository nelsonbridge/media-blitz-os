from pathlib import Path

from nks.application.load_records import load_record
from nks.domain.models import (
    ArtifactRecord,
    GateStatus,
    NarrativeRecord,
    ProofRecord,
    PublicationRecord,
    SourceRecord,
    VisualPackageRecord,
)

ROOT = Path(__file__).resolve().parents[1] / "records"
PUBLICATION_IDS = [f"NKS-PUB-{index:06d}" for index in range(1, 13)]


def test_all_twelve_publications_have_complete_canonical_reference_sets():
    for publication_id in PUBLICATION_IDS:
        suffix = publication_id.rsplit("-", 1)[1]
        artifact_id = f"NKS-ART-{suffix}"
        proof_id = f"NKS-PRF-{suffix}"
        narrative_id = f"NKS-NAR-{suffix}"
        visual_id = f"NKS-VIS-{suffix}"

        publication = load_record(
            ROOT, "publications", publication_id, PublicationRecord
        )
        artifact = load_record(ROOT, "artifacts", artifact_id, ArtifactRecord)
        proof = load_record(ROOT, "proofs", proof_id, ProofRecord)
        narrative = load_record(ROOT, "narratives", narrative_id, NarrativeRecord)
        visual = load_record(ROOT, "visuals", visual_id, VisualPackageRecord)

        assert publication.artifact_id == artifact.id
        assert publication.proof_id == proof.id
        assert publication.narrative_id == narrative.id
        assert publication.visual_package_id == visual.id
        assert proof.artifact_id == artifact.id
        assert narrative.artifact_id == artifact.id
        assert visual.artifact_id == artifact.id
        assert visual.publication_id == publication.id
        assert narrative.gate_status in {GateStatus.READY, GateStatus.APPROVED}

        for source_id in artifact.source_ids:
            load_record(ROOT, "sources", source_id, SourceRecord)


def test_publication_gate_posture_matches_canonical_scope():
    for index in range(1, 13):
        suffix = f"{index:06d}"
        publication = load_record(
            ROOT, "publications", f"NKS-PUB-{suffix}", PublicationRecord
        )
        visual = load_record(
            ROOT, "visuals", f"NKS-VIS-{suffix}", VisualPackageRecord
        )

        assert publication.editorial_status == GateStatus.READY
        assert publication.user_approval == GateStatus.NEEDED
        assert visual.signature_diagram_id is not None
        assert visual.hero_image_id is not None
        assert visual.gate_status == GateStatus.NEEDED


def test_publication_000001_assets_are_rendered_but_require_human_review():
    visual = load_record(ROOT, "visuals", "NKS-VIS-000001", VisualPackageRecord)

    assert visual.status == "review"
    assert visual.gate_status == GateStatus.NEEDED
    assert visual.metadata["render_status"] == "rendered"
    assert visual.metadata["review_status"] == "needed"
    assert visual.metadata["manifest_path"] == "assets/publication-000001/manifest.json"
    assert (
        visual.metadata["review_record_path"]
        == "publishing/reviews/NKS-PUB-000001-visual-review.md"
    )


def test_citation_required_proofs_are_ready_with_current_verification_recorded():
    for index in (5, 9, 10, 11, 12):
        proof = load_record(ROOT, "proofs", f"NKS-PRF-{index:06d}", ProofRecord)
        assert proof.citations_required is True
        assert proof.gate_status == GateStatus.READY
