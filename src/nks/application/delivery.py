"""Application services for publication preparation and feedback promotion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pydantic import ValidationError

from nks.domain.delivery import (
    FeedbackPromotionAuthorization,
    FeedbackProvenance,
    FeedbackRecord,
    PromotionDecision,
    PublicationPayload,
    PublicationReceipt,
)
from nks.domain.models import (
    GateStatus,
    PublicationRecord,
    RecordStatus,
    SourceRecord,
    WorkflowEvent,
)
from nks.ports.delivery import FeedbackRepository, PublicationAdapter
from nks.ports.repositories import EventRepository


class PublicationNotApprovedError(ValueError):
    pass


class FeedbackPromotionError(ValueError):
    """Base error for rejected feedback promotion attempts."""


class FeedbackPromotionNotAuthorizedError(FeedbackPromotionError):
    pass


class FeedbackPromotionProhibitedError(FeedbackPromotionError):
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

    def execute_json(self, raw_feedback: str) -> FeedbackRecord:
        """Validate and ingest JSON while retaining validation failure evidence."""
        try:
            feedback = FeedbackRecord.model_validate_json(raw_feedback)
        except ValidationError as exc:
            digest = hashlib.sha256(raw_feedback.encode("utf-8")).hexdigest()
            subject_id = "feedback-ingestion"
            try:
                payload = json.loads(raw_feedback)
                if isinstance(payload, dict):
                    subject_id = str(
                        payload.get("feedback_id")
                        or payload.get("publication_id")
                        or subject_id
                    )
            except json.JSONDecodeError:
                pass

            self.events.append(
                WorkflowEvent(
                    event_id=f"feedback.validation_failed:{digest[:16]}",
                    event_type="feedback.validation_failed",
                    subject_id=subject_id,
                    payload={
                        "reason_code": "SCHEMA_VALIDATION_FAILED",
                        "content_sha256": digest,
                        "error_count": len(exc.errors()),
                    },
                )
            )
            raise

        return self.execute(feedback)

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
                    "provenance": feedback.provenance,
                    "scenario_id": feedback.scenario_id,
                    "lineage_ids": feedback.lineage_ids,
                    "proof_boundary_count": len(feedback.proof_boundaries),
                },
            )
        )
        return saved

    def _deny_promotion(
        self,
        feedback: FeedbackRecord,
        *,
        source_id: str,
        reason_code: str,
        authorization: FeedbackPromotionAuthorization | None,
    ) -> None:
        self.events.append(
            WorkflowEvent(
                event_id=(
                    f"feedback.promotion_denied:{feedback.feedback_id}:"
                    f"{source_id}:{reason_code}"
                ),
                event_type="feedback.promotion_denied",
                subject_id=feedback.feedback_id,
                payload={
                    "reason_code": reason_code,
                    "target_source_id": source_id,
                    "provenance": feedback.provenance,
                    "authorization_id": (
                        authorization.authorization_id if authorization else None
                    ),
                },
            )
        )

    def promote_to_source(
        self,
        feedback: FeedbackRecord,
        *,
        source_id: str,
        source_location: str,
        authorization: FeedbackPromotionAuthorization | None,
    ) -> SourceRecord:
        if feedback.provenance in {
            FeedbackProvenance.SYNTHETIC,
            FeedbackProvenance.REPLAY,
        }:
            reason_code = f"{feedback.provenance}_PROMOTION_PROHIBITED"
            self._deny_promotion(
                feedback,
                source_id=source_id,
                reason_code=reason_code,
                authorization=authorization,
            )
            raise FeedbackPromotionProhibitedError(
                f"{feedback.provenance} feedback cannot be promoted to a factual source"
            )

        if authorization is None:
            self._deny_promotion(
                feedback,
                source_id=source_id,
                reason_code="AUTHORIZATION_REQUIRED",
                authorization=None,
            )
            raise FeedbackPromotionNotAuthorizedError(
                "explicit promotion authorization is required"
            )

        if authorization.decision != PromotionDecision.APPROVED:
            self._deny_promotion(
                feedback,
                source_id=source_id,
                reason_code="AUTHORIZATION_DENIED",
                authorization=authorization,
            )
            raise FeedbackPromotionNotAuthorizedError(
                "promotion authorization decision is not APPROVED"
            )

        if authorization.feedback_id != feedback.feedback_id:
            self._deny_promotion(
                feedback,
                source_id=source_id,
                reason_code="AUTHORIZATION_FEEDBACK_MISMATCH",
                authorization=authorization,
            )
            raise FeedbackPromotionNotAuthorizedError(
                "promotion authorization does not match feedback record"
            )

        if authorization.target_source_id != source_id:
            self._deny_promotion(
                feedback,
                source_id=source_id,
                reason_code="AUTHORIZATION_TARGET_MISMATCH",
                authorization=authorization,
            )
            raise FeedbackPromotionNotAuthorizedError(
                "promotion authorization does not match target source"
            )

        if feedback.promoted_to_source_id and feedback.promoted_to_source_id != source_id:
            self._deny_promotion(
                feedback,
                source_id=source_id,
                reason_code="ALREADY_PROMOTED_TO_DIFFERENT_SOURCE",
                authorization=authorization,
            )
            raise FeedbackPromotionError(
                "feedback is already promoted to a different source record"
            )

        source = SourceRecord(
            id=source_id,
            title=f"Feedback from {feedback.platform}: {feedback.feedback_id}",
            status=RecordStatus.REVIEW,
            source_type="external-feedback",
            source_location=source_location,
            limitations=[
                "External feedback is an observation, not automatically verified proof.",
                f"Feedback classification: {feedback.classification}",
                *feedback.proof_boundaries,
            ],
            metadata={
                "feedback_id": feedback.feedback_id,
                "publication_id": feedback.publication_id,
                "platform": feedback.platform,
                "provenance": feedback.provenance,
                "lineage_ids": feedback.lineage_ids,
                "authorization_id": authorization.authorization_id,
                "authorized_by": authorization.authorized_by,
                "authorization_justification": authorization.justification,
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
                    "provenance": feedback.provenance,
                    "authorization_id": authorization.authorization_id,
                    "authorized_by": authorization.authorized_by,
                },
            )
        )
        return source
