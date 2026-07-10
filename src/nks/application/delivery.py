"""Application services for publication preparation and feedback promotion."""

from __future__ import annotations

from dataclasses import dataclass

from nks.domain.delivery import FeedbackRecord, PublicationPayload, PublicationReceipt
from nks.domain.models import GateStatus, PublicationRecord, RecordStatus, SourceRecord, WorkflowEvent
from nks.ports.delivery import FeedbackRepository, PublicationAdapter
from nks.ports.repositories import EventRepository


class PublicationNotApprovedError(ValueError):
    pass


@dataclass
class PreparePublication:
    adapter: PublicationAdapter
    events: EventRepository

    def execute(
        self,
        publication: PublicationRecord,
        payload: PublicationPayload,
    ) -> PublicationReceipt:
        if publication.user_approval != GateStatus.APPROVED:
            raise PublicationNotApprovedError(
                f"publication {publication.id} requires explicit user approval"
            )
        if payload.publication_id != publication.id:
            raise ValueError("payload publication_id does not match publication record")

        receipt = self.adapter.prepare(payload)
        self.events.append(
            WorkflowEvent(
                event_id=f"publication.prepared:{payload.platform}:{publication.id}",
                event_type="publication.prepared",
                subject_id=publication.id,
                payload={
                    "platform": payload.platform,
                    "receipt_id": receipt.receipt_id,
                    "status": receipt.status,
                },
            )
        )
        return receipt


@dataclass
class IngestFeedback:
    repository: FeedbackRepository
    events: EventRepository

    def execute(self, feedback: FeedbackRecord) -> FeedbackRecord:
        saved = self.repository.save(feedback)
        self.events.append(
            WorkflowEvent(
                event_id=f"feedback.recorded:{feedback.feedback_id}",
                event_type="feedback.recorded",
                subject_id=feedback.publication_id,
                payload={
                    "feedback_id": feedback.feedback_id,
                    "classification": feedback.classification,
                    "platform": feedback.platform,
                },
            )
        )
        return saved

    def promote_to_source(
        self,
        feedback: FeedbackRecord,
        *,
        source_id: str,
        source_location: str,
    ) -> SourceRecord:
        if feedback.promoted_to_source_id and feedback.promoted_to_source_id != source_id:
            raise ValueError("feedback is already promoted to a different source record")

        source = SourceRecord(
            id=source_id,
            title=f"Feedback from {feedback.platform}: {feedback.feedback_id}",
            status=RecordStatus.REVIEW,
            source_type="external-feedback",
            source_location=source_location,
            limitations=[
                "External feedback is an observation, not automatically verified proof.",
                f"Feedback classification: {feedback.classification}",
            ],
            metadata={
                "feedback_id": feedback.feedback_id,
                "publication_id": feedback.publication_id,
                "platform": feedback.platform,
            },
        )
        promoted = feedback.model_copy(update={"promoted_to_source_id": source_id})
        self.repository.save(promoted)
        self.events.append(
            WorkflowEvent(
                event_id=f"feedback.promoted:{feedback.feedback_id}",
                event_type="feedback.promoted_to_source",
                subject_id=source_id,
                payload={
                    "feedback_id": feedback.feedback_id,
                    "publication_id": feedback.publication_id,
                },
            )
        )
        return source
