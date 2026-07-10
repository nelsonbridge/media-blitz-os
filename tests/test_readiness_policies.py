from nks.domain.models import (
    GateStatus,
    NarrativeRecord,
    ProofRecord,
    PublicationRecord,
    RecordStatus,
    SourceRecord,
    VisualPackageRecord,
)
from nks.policies.readiness import validate_publication_readiness


def valid_records():
    source = SourceRecord(
        id="SRC", title="Source", status=RecordStatus.APPROVED,
        source_type="fixture", source_location="fixture.md",
    )
    proof = ProofRecord(
        id="PRF", title="Proof", artifact_id="ART", category="fixture",
        gate_status=GateStatus.READY,
    )
    narrative = NarrativeRecord(
        id="NAR", title="Narrative", artifact_id="ART",
        recognition="r", reframe="r", framework="f", proof="p",
        application="a", consequence="c", invitation="i",
        gate_status=GateStatus.READY,
    )
    visual = VisualPackageRecord(
        id="VIS", title="Visual", artifact_id="ART", publication_id="PUB",
        signature_diagram_id="DGM", gate_status=GateStatus.READY,
    )
    publication = PublicationRecord(
        id="PUB", title="Publication", artifact_id="ART", proof_id="PRF",
        narrative_id="NAR", visual_package_id="VIS", draft_path="draft.md",
        editorial_status=GateStatus.READY, user_approval=GateStatus.APPROVED,
    )
    return source, proof, narrative, visual, publication


def test_missing_source_fails():
    _, proof, narrative, visual, publication = valid_records()
    result = validate_publication_readiness(publication, None, proof, narrative, visual)
    assert not result.passed
    assert "source record is missing" in result.failures


def test_incomplete_narrative_fails():
    source, proof, narrative, visual, publication = valid_records()
    narrative.invitation = ""
    result = validate_publication_readiness(publication, source, proof, narrative, visual)
    assert not result.passed
    assert "narrative segment missing: invitation" in result.failures


def test_missing_signature_diagram_fails():
    source, proof, narrative, visual, publication = valid_records()
    visual.signature_diagram_id = None
    result = validate_publication_readiness(publication, source, proof, narrative, visual)
    assert not result.passed
    assert "signature diagram is missing" in result.failures


def test_user_approval_is_mandatory():
    source, proof, narrative, visual, publication = valid_records()
    publication.user_approval = GateStatus.NEEDED
    result = validate_publication_readiness(publication, source, proof, narrative, visual)
    assert not result.passed
    assert "user approval is needed" in result.failures
