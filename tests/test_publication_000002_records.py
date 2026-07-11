from pathlib import Path

from nks.application.load_records import load_record
from nks.domain.models import NarrativeRecord, ProofRecord, PublicationRecord, SourceRecord, VisualPackageRecord
from nks.policies.readiness import validate_publication_readiness

ROOT = Path(__file__).resolve().parents[1] / "records"


def test_publication_000002_has_proof_and_narrative_but_stops_at_visual_editorial_and_approval_gates():
    source = load_record(ROOT, "sources", "NKS-SRC-000001", SourceRecord)
    proof = load_record(ROOT, "proofs", "NKS-PRF-000002", ProofRecord)
    narrative = load_record(ROOT, "narratives", "NKS-NAR-000002", NarrativeRecord)
    visual = load_record(ROOT, "visuals", "NKS-VIS-000002", VisualPackageRecord)
    publication = load_record(ROOT, "publications", "NKS-PUB-000002", PublicationRecord)

    result = validate_publication_readiness(publication, source, proof, narrative, visual)

    assert not result.passed
    assert result.failures == (
        "visual gate is needed",
        "editorial gate is needed",
        "user approval is needed",
    )
