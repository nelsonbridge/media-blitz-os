from pathlib import Path

import pytest

from nks.adapters.manual_delivery import JsonFeedbackRepository, ManualPublicationAdapter
from nks.application.delivery import (
    IngestFeedback,
    PreparePublication,
    PublicationNotApprovedError,
)
from nks.application.feedback import FeedbackReplayHarness
from nks.domain.delivery import (
    FeedbackClassification,
    FeedbackProvenance,
    FeedbackRecord,
    FeedbackScenario,
    PublicationPayload,
)
from nks.domain.models import GateStatus, PublicationRecord, WorkflowEvent


class MemoryEvents:
    def __init__(self):
        self.items: list[WorkflowEvent] = []

    def append(self, event: WorkflowEvent) -> None:
        if not any(item.event_id == event.event_id for item in self.items):
            self.items.append(event)

    def list(self) -> list[WorkflowEvent]:
        return list(self.items)


def publication(approval: GateStatus) -> PublicationRecord:
    return PublicationRecord(
        id="NKS-PUB-000001",
        title="The Corpus Is Manufactured, Not Found",
        artifact_id="NKS-ART-000001",
        proof_id="NKS-PRF-000001",
        narrative_id="NKS-NAR-000001",
        visual_package_id="NKS-VIS-000001",
        draft_path="publishing/drafts/NKS-PUB-000001.md",
        editorial_status=GateStatus.READY,
        user_approval=approval,
    )


def payload() -> PublicationPayload:
    return PublicationPayload(
        publication_id="NKS-PUB-000001",
        platform="medium",
        title="The Corpus Is Manufactured, Not Found",
        body="Prepared article body.",
        asset_ids=["NKS-DGM-000001", "NKS-HRO-000001"],
    )


def test_manual_publication_requires_explicit_approval(tmp_path: Path):
    service = PreparePublication(ManualPublicationAdapter(tmp_path), MemoryEvents())
    with pytest.raises(PublicationNotApprovedError):
        service.execute(publication(GateStatus.NEEDED), payload())


def test_manual_publication_creates_package_and_event(tmp_path: Path):
    events = MemoryEvents()
    service = PreparePublication(ManualPublicationAdapter(tmp_path), events)

    receipt = service.execute(publication(GateStatus.APPROVED), payload())

    package = tmp_path / "medium" / "NKS-PUB-000001"
    assert receipt.status == "prepared"
    assert (package / "payload.json").exists()
    assert (package / "checklist.md").exists()
    assert [item.event_type for item in events.list()] == ["publication.prepared"]


def test_feedback_is_idempotent_and_requires_explicit_promotion(tmp_path: Path):
    events = MemoryEvents()
    repository = JsonFeedbackRepository(tmp_path)
    service = IngestFeedback(repository, events)
    feedback = FeedbackRecord(
        feedback_id="NKS-FDB-000001",
        publication_id="NKS-PUB-000001",
        platform="linkedin",
        classification=FeedbackClassification.CORRECTION,
        content="A reader suggests a factual correction.",
    )

    service.execute(feedback)
    service.execute(feedback)
    source = service.promote_to_source(
        feedback,
        source_id="NKS-SRC-000004",
        source_location="records/feedback/NKS-FDB-000001.json",
    )

    assert len(repository.list_for_publication("NKS-PUB-000001")) == 1
    assert source.source_type == "external-feedback"
    assert source.status == "review"
    assert "not automatically verified proof" in source.limitations[0]
    assert [item.event_type for item in events.list()] == [
        "feedback.recorded",
        "feedback.promoted_to_source",
    ]


def test_synthetic_feedback_replay_records(tmp_path: Path):
    events = MemoryEvents()
    repository = JsonFeedbackRepository(tmp_path)
    harness = FeedbackReplayHarness(repository, events)

    scenario = FeedbackScenario(
        scenario_id="SYNTH-000001",
        description="Synthetic feedback regression scenario.",
        feedback=FeedbackRecord(
            feedback_id="NKS-FDB-000002",
            publication_id="NKS-PUB-000001",
            platform="simulation",
            classification=FeedbackClassification.SIGNAL,
            content="Synthetic feedback sample for replay.",
            provenance=FeedbackProvenance.SYNTHETIC,
            scenario_id="SYNTH-000001",
        ),
    )

    played = harness.replay([scenario])

    assert len(played) == 1
    assert played[0].provenance == FeedbackProvenance.SYNTHETIC
    assert played[0].scenario_id == "SYNTH-000001"
    assert repository.get("NKS-FDB-000002") is not None
    assert [item.event_type for item in events.list()] == ["feedback.replayed"]
    assert events.list()[0].payload["provenance"] == "synthetic"
