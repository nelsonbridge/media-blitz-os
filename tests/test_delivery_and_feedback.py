import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.adapters.canonicalization import JsonCanonicalSourceStore
from nks.adapters.manual_delivery import JsonFeedbackRepository, ManualPublicationAdapter
from nks.application.canonicalization import (
    RestrictedCanonicalSourceWriter,
    feedback_sha256,
    promotion_idempotency_key,
)
from nks.application.delivery import (
    FeedbackPromotionNotAuthorizedError,
    FeedbackPromotionProhibitedError,
    IngestFeedback,
    PreparePublication,
    PublicationNotApprovedError,
)
from nks.application.feedback import FeedbackReplayHarness
from nks.domain.delivery import (
    FeedbackClassification,
    FeedbackProofReview,
    FeedbackPromotionAuthorization,
    FeedbackProvenance,
    FeedbackRecord,
    FeedbackScenario,
    PromotionDecision,
    ProofReviewDecision,
    PublicationPayload,
)
from nks.domain.models import GateStatus, PublicationRecord, WorkflowEvent

NOW = datetime(2026, 7, 12, 20, 40, tzinfo=timezone.utc)


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


def real_feedback(feedback_id: str = "NKS-FDB-000001") -> FeedbackRecord:
    return FeedbackRecord(
        feedback_id=feedback_id,
        publication_id="NKS-PUB-000001",
        platform="linkedin",
        classification=FeedbackClassification.CORRECTION,
        content="A reader suggests a factual correction.",
        provenance=FeedbackProvenance.REAL,
        lineage_ids=["NKS-PUB-000001"],
        proof_boundaries=[
            "Treat the response as an observation, not verified proof."
        ],
    )


def proof_review(item: FeedbackRecord) -> FeedbackProofReview:
    return FeedbackProofReview(
        review_id=f"NKS-PRV-{item.feedback_id}",
        feedback_id=item.feedback_id,
        feedback_sha256=feedback_sha256(item),
        reviewed_by="S. Michael Nelson",
        reviewed_at=NOW - timedelta(minutes=5),
        decision=ProofReviewDecision.ELIGIBLE,
        evidence_ids=[item.publication_id],
        limitations=["Independent validation remains required."],
    )


def promotion_authorization(
    item: FeedbackRecord,
    review: FeedbackProofReview,
    *,
    feedback_id: str | None = None,
    source_id: str = "NKS-SRC-000004",
    decision: PromotionDecision = PromotionDecision.APPROVED,
) -> FeedbackPromotionAuthorization:
    digest = feedback_sha256(item)
    authorization_id = f"NKS-AUTH-{item.feedback_id}"
    return FeedbackPromotionAuthorization(
        authorization_id=authorization_id,
        feedback_id=feedback_id or item.feedback_id,
        feedback_sha256=digest,
        target_source_id=source_id,
        proof_review_id=review.review_id,
        idempotency_key=promotion_idempotency_key(
            digest, authorization_id, source_id
        ),
        authorized_by="S. Michael Nelson",
        justification="Retain the observed correction as a review-state source.",
        decision=decision,
        authorized_at=NOW - timedelta(minutes=1),
    )


def synthetic_scenario() -> FeedbackScenario:
    return FeedbackScenario(
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
            lineage_ids=["NKS-PUB-000001", "SYNTH-000001"],
            proof_boundaries=[
                "This is manufactured test input and must not be represented as observed feedback."
            ],
        ),
    )


def promotion_service(tmp_path: Path, events: MemoryEvents):
    repository = JsonFeedbackRepository(tmp_path)
    writer = RestrictedCanonicalSourceWriter(
        store=JsonCanonicalSourceStore(tmp_path / "records"),
        feedback=repository,
        events=events,
        clock=lambda: NOW,
    )
    return repository, IngestFeedback(repository, events, writer)


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


def test_feedback_requires_explicit_provenance():
    record = real_feedback().model_dump(mode="json")
    record.pop("provenance")
    with pytest.raises(ValidationError):
        FeedbackRecord.model_validate(record)


def test_feedback_rejects_unknown_provenance():
    record = real_feedback().model_dump(mode="json")
    record["provenance"] = "ASSUMED_REAL"
    with pytest.raises(ValidationError):
        FeedbackRecord.model_validate(record)


def test_feedback_requires_lineage_and_proof_boundaries():
    record = real_feedback().model_dump(mode="json")
    record["lineage_ids"] = []
    with pytest.raises(ValidationError):
        FeedbackRecord.model_validate(record)

    record = real_feedback().model_dump(mode="json")
    record["proof_boundaries"] = []
    with pytest.raises(ValidationError):
        FeedbackRecord.model_validate(record)


def test_real_feedback_cannot_carry_scenario_id():
    record = real_feedback().model_dump(mode="json")
    record["scenario_id"] = "SYNTH-000001"
    with pytest.raises(ValidationError):
        FeedbackRecord.model_validate(record)


def test_ingestion_validation_failure_is_audited(tmp_path: Path):
    events = MemoryEvents()
    service = IngestFeedback(JsonFeedbackRepository(tmp_path), events)
    invalid = real_feedback().model_dump(mode="json")
    invalid.pop("provenance")

    with pytest.raises(ValidationError):
        service.execute_json(json.dumps(invalid))

    assert [item.event_type for item in events.list()] == [
        "feedback.validation_failed"
    ]
    assert events.list()[0].payload["reason_code"] == "SCHEMA_VALIDATION_FAILED"


def test_feedback_is_idempotent_and_requires_authorized_promotion(tmp_path: Path):
    events = MemoryEvents()
    repository, service = promotion_service(tmp_path, events)
    item = real_feedback()
    review = proof_review(item)
    authorization = promotion_authorization(item, review)

    service.execute(item)
    service.execute(item)

    with pytest.raises(FeedbackPromotionNotAuthorizedError):
        service.promote_to_source(
            item,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000001.json",
            authorization=None,
        )

    source = service.promote_to_source(
        item,
        source_id="NKS-SRC-000004",
        source_location="records/feedback/NKS-FDB-000001.json",
        authorization=authorization,
        proof_review=review,
    )

    assert len(repository.list_for_publication("NKS-PUB-000001")) == 1
    assert source.source_type == "external-feedback"
    assert source.status == "review"
    assert "not automatically verified proof" in source.limitations[0]
    assert source.metadata["authorization_id"] == authorization.authorization_id
    assert [event.event_type for event in events.list()] == [
        "feedback.recorded",
        "feedback.promotion_denied",
        "canonical.source_created",
    ]
    assert events.list()[1].payload["reason_code"] == "AUTHORIZATION_REQUIRED"


def test_denied_or_mismatched_authorization_blocks_promotion(tmp_path: Path):
    events = MemoryEvents()
    _, service = promotion_service(tmp_path, events)
    item = real_feedback()
    review = proof_review(item)

    with pytest.raises(FeedbackPromotionNotAuthorizedError):
        service.promote_to_source(
            item,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000001.json",
            authorization=promotion_authorization(
                item, review, decision=PromotionDecision.DENIED
            ),
            proof_review=review,
        )

    with pytest.raises(FeedbackPromotionNotAuthorizedError):
        service.promote_to_source(
            item,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000001.json",
            authorization=promotion_authorization(
                item, review, feedback_id="NKS-FDB-OTHER"
            ),
            proof_review=review,
        )

    assert [event.payload["reason_code"] for event in events.list()] == [
        "AUTHORIZATION_DENIED",
        "FEEDBACK_ID_MISMATCH",
    ]


def test_synthetic_feedback_replay_is_forced_to_replay_provenance(tmp_path: Path):
    events = MemoryEvents()
    repository = JsonFeedbackRepository(tmp_path)
    harness = FeedbackReplayHarness(repository, events)
    played = harness.replay([synthetic_scenario()])

    assert len(played) == 1
    assert played[0].provenance == FeedbackProvenance.REPLAY
    assert played[0].scenario_id == "SYNTH-000001"
    assert "SYNTH-000001" in played[0].lineage_ids
    assert played[0].metadata["replay_source_provenance"] == "SYNTHETIC"
    assert repository.get("NKS-FDB-000002") is not None
    assert [item.event_type for item in events.list()] == ["feedback.replayed"]
    assert events.list()[0].payload["provenance"] == "REPLAY"


def test_replay_promotion_is_prohibited_and_audited(tmp_path: Path):
    events = MemoryEvents()
    repository = JsonFeedbackRepository(tmp_path)
    harness = FeedbackReplayHarness(repository, events)
    replayed = harness.replay([synthetic_scenario()])[0]
    writer = RestrictedCanonicalSourceWriter(
        store=JsonCanonicalSourceStore(tmp_path / "records"),
        feedback=repository,
        events=events,
        clock=lambda: NOW,
    )
    service = IngestFeedback(repository, events, writer)
    review = proof_review(replayed)

    with pytest.raises(FeedbackPromotionProhibitedError):
        service.promote_to_source(
            replayed,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000002.json",
            authorization=promotion_authorization(replayed, review),
            proof_review=review,
        )

    assert events.list()[-1].event_type == "canonical.write_rejected"
    assert events.list()[-1].payload["reason_code"] == "PROVENANCE_INELIGIBLE"


def test_replay_validation_failure_is_audited(tmp_path: Path):
    events = MemoryEvents()
    harness = FeedbackReplayHarness(JsonFeedbackRepository(tmp_path), events)
    invalid = synthetic_scenario().model_dump(mode="json")
    invalid["feedback"]["provenance"] = "REAL"

    with pytest.raises(ValidationError):
        harness.replay_json(json.dumps(invalid))

    assert [item.event_type for item in events.list()] == [
        "feedback.replay_validation_failed"
    ]
    assert events.list()[0].payload["reason_code"] == "SCENARIO_VALIDATION_FAILED"
