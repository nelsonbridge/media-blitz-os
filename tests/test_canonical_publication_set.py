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

        publication = load_record(ROOT, "publications", publication_id, PublicationRecord)
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
    publication_1 = load_record(ROOT, "publications", "NKS-PUB-000001", PublicationRecord)
    assert publication_1.editorial_status == GateStatus.READY
    assert publication_1.user_approval == GateStatus.NEEDED

    for index in range(2, 13):
        suffix = f"{index:06d}"
        publication = load_record(ROOT, "publications", f"NKS-PUB-{suffix}", PublicationRecord)
        visual = load_record(ROOT, "visuals", f"NKS-VIS-{suffix}", VisualPackageRecord)

        assert publication.editorial_status == GateStatus.NEEDED
        assert publication.user_approval == GateStatus.NEEDED
        assert visual.gate_status == GateStatus.NEEDED
        assert visual.signature_diagram_id is None


def test_technical_publications_remain_proof_partial_until_current_verification():
    for index in (9, 10, 11, 12):
        proof = load_record(ROOT, "proofs", f"NKS-PRF-{index:06d}", ProofRecord)
        assert proof.citations_required is True
        assert proof.gate_status == GateStatus.PARTIAL

    clarity_proof = load_record(ROOT, "proofs", "NKS-PRF-000005", ProofRecord)
    assert clarity_proof.citations_required is True
    assert clarity_proof.gate_status == GateStatus.PARTIAL
