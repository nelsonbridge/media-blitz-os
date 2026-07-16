from pathlib import Path

from nks.adapters.filesystem import JsonEventRepository, JsonRecordRepository
from nks.adapters.manual_delivery import JsonFeedbackRepository, ManualPublicationAdapter
from nks.application.delivery import IngestFeedback, PreparePublication
from nks.application.manufacture import ManufacturePublication, ManufacturingRepositories
from nks.domain.delivery import FeedbackClassification, FeedbackRecord, PublicationPayload
from nks.domain.models import (
    ArtifactRecord,
    GateStatus,
    NarrativeRecord,
    ProofRecord,
    PublicationRecord,
    RecordStatus,
    SourceRecord,
    VisualPackageRecord,
)


def build_manufacturing_runtime(root: Path) -> ManufacturePublication:
    repositories = ManufacturingRepositories(
        sources=JsonRecordRepository(root, SourceRecord, "sources"),
        artifacts=JsonRecordRepository(root, ArtifactRecord, "artifacts"),
        proofs=JsonRecordRepository(root, ProofRecord, "proofs"),
        narratives=JsonRecordRepository(root, NarrativeRecord, "narratives"),
        visuals=JsonRecordRepository(root, VisualPackageRecord, "visuals"),
        publications=JsonRecordRepository(root, PublicationRecord, "publications"),
        events=JsonEventRepository(root),
    )
    return ManufacturePublication(repositories)


def make_test_package() -> tuple[SourceRecord, ArtifactRecord, ProofRecord, NarrativeRecord, VisualPackageRecord, PublicationRecord]:
    source = SourceRecord(
        id="NKS-SRC-E2E-0001",
        title="End-to-End Source",
        status=RecordStatus.APPROVED,
        source_type="e2e-fixture",
        source_location="fixtures/source.md",
    )
    artifact = ArtifactRecord(
        id="NKS-ART-E2E-0001",
        title="End-to-End Publication Artifact",
        status=RecordStatus.REVIEW,
        source_ids=[source.id],
        proof_status=GateStatus.READY,
        narrative_status=GateStatus.READY,
        visual_status=GateStatus.READY,
    )
    proof = ProofRecord(
        id="NKS-PRF-E2E-0001",
        title="End-to-End Proof",
        status=RecordStatus.REVIEW,
        artifact_id=artifact.id,
        category="repository-derived",
        supported_claims=["The runtime persists platform-neutral canonical records."],
        unsupported_claims=["The runtime does not publish external content."],
        gate_status=GateStatus.READY,
    )
    narrative = NarrativeRecord(
        id="NKS-NAR-E2E-0001",
        title="End-to-End Narrative",
        status=RecordStatus.REVIEW,
        artifact_id=artifact.id,
        recognition="The system needs a connected narrative arc.",
        reframe="Published knowledge is a manufactured asset, not a discovered file set.",
        framework="Source → Artifact → Proof → Narrative → Visual → Publication",
        proof="This test validates the end-to-end workflow through the NKS runtime.",
        application="Use the same canonically stored records for delivery and feedback.",
        consequence="A portable runtime can be exercised without external platform APIs.",
        invitation="Validate the package with manual preparation and feedback stubs.",
        gate_status=GateStatus.READY,
    )
    visual = VisualPackageRecord(
        id="NKS-VIS-E2E-0001",
        title="End-to-End Visual Package",
        status=RecordStatus.REVIEW,
        artifact_id=artifact.id,
        publication_id="NKS-PUB-E2E-0001",
        signature_diagram_id="NKS-DGM-E2E-0001",
        hero_image_id="NKS-HRO-E2E-0001",
        asset_ids=["NKS-DGM-E2E-0001", "NKS-HRO-E2E-0001"],
        gate_status=GateStatus.READY,
    )
    publication = PublicationRecord(
        id="NKS-PUB-E2E-0001",
        title="End-to-End Publication Test",
        status=RecordStatus.REVIEW,
        artifact_id=artifact.id,
        proof_id=proof.id,
        narrative_id=narrative.id,
        visual_package_id=visual.id,
        draft_path="publishing/drafts/NKS-PUB-E2E-0001.md",
        editorial_status=GateStatus.READY,
        user_approval=GateStatus.APPROVED,
    )
    return source, artifact, proof, narrative, visual, publication


def test_end_to_end_package_can_flow_from_manufacture_to_manual_publication_and_feedback(tmp_path: Path):
    runtime = build_manufacturing_runtime(tmp_path)
    source, artifact, proof, narrative, visual, publication = make_test_package()

    readiness = runtime.execute(
        source=source,
        artifact=artifact,
        proof=proof,
        narrative=narrative,
        visual=visual,
        publication=publication,
    )

    assert readiness.passed, readiness.failures
    assert (tmp_path / "sources" / f"{source.id}.json").exists()
    assert (tmp_path / "publications" / f"{publication.id}.json").exists()

    output_root = tmp_path / "output"
    adapter = ManualPublicationAdapter(output_root)
    events = JsonEventRepository(tmp_path)
    publisher = PreparePublication(adapter, events)
    payload = PublicationPayload(
        publication_id=publication.id,
        platform="mock-publisher",
        title=publication.title,
        body="This is a dry-run publication payload for end-to-end verification.",
        asset_ids=[visual.signature_diagram_id, visual.hero_image_id],
    )

    receipt = publisher.execute(publication, payload)
    package_dir = output_root / payload.platform / publication.id

    assert receipt.status == "prepared"
    assert package_dir.exists()
    assert (package_dir / "payload.json").exists()
    assert (package_dir / "checklist.md").exists()

    # Verify the publication workflow events include manufacturing and preparation steps.
    persisted_events = [event.event_type for event in events.list()]
    assert "publication.manufactured" in persisted_events
    assert "publication.prepared" in persisted_events

    feedback_repo = JsonFeedbackRepository(tmp_path)
    feedback_events = JsonEventRepository(tmp_path)
    ingester = IngestFeedback(feedback_repo, feedback_events)
    feedback = FeedbackRecord(
        feedback_id="NKS-FDB-E2E-0001",
        publication_id=publication.id,
        platform="mock-review",
        classification=FeedbackClassification.COMMENT,
        content="This is a review stub for the end-to-end test.",
    )

    recorded = ingester.execute(feedback)
    assert len(feedback_repo.list_for_publication(publication.id)) == 1
    assert recorded.feedback_id == feedback.feedback_id

    promoted = ingester.promote_to_source(
        recorded,
        source_id="NKS-SRC-E2E-0002",
        source_location=f"feedback/{recorded.feedback_id}.json",
    )

    assert promoted.status == RecordStatus.REVIEW
    assert promoted.source_type == "external-feedback"
    assert len(feedback_events.list()) >= 2
