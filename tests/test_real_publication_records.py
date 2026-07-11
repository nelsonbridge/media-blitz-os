from pathlib import Path

from nks.application.load_records import load_record
from nks.domain.models import (
    NarrativeRecord,
    ProofRecord,
    PublicationRecord,
    SourceRecord,
    VisualPackageRecord,
)
from nks.policies.readiness import validate_publication_readiness


ROOT = Path(__file__).resolve().parents[1] / "records"


def test_publication_000001_waits_for_visual_review_and_user_approval():
    source = load_record(ROOT, "sources", "NKS-SRC-000001", SourceRecord)
    proof = load_record(ROOT, "proofs", "NKS-PRF-000001", ProofRecord)
    narrative = load_record(ROOT, "narratives", "NKS-NAR-000001", NarrativeRecord)
    visual = load_record(ROOT, "visuals", "NKS-VIS-000001", VisualPackageRecord)
    publication = load_record(
        ROOT, "publications", "NKS-PUB-000001", PublicationRecord
    )

    result = validate_publication_readiness(
        publication, source, proof, narrative, visual
    )

    assert not result.passed
    assert result.failures == (
        "visual gate is needed",
        "user approval is needed",
    )
