"""Application services for publication preparation and feedback ingestion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import ValidationError

from nks.application.canonicalization import (
    CanonicalTargetReservedError,
    CanonicalWriteAuthorizationError,
    CanonicalWriteIntegrityError,
)
from nks.domain.delivery import (
    FeedbackProofReview,
    FeedbackPromotionAuthorization,
    FeedbackRecord,
    PublicationPayload,
    PublicationReceipt,
)
from nks.domain.models import GateStatus, PublicationRecord, WorkflowEvent
from nks.ports.canonicalization import CanonicalSourceWriter
from nks.ports.delivery import FeedbackRepository, PublicationAdapter
from nks.ports.repositories import EventRepository

if TYPE_CHECKING:
    from nks.domain.models import SourceRecord


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
    canonical_writer: CanonicalSourceWriter | None = None

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
        proof_review: FeedbackProofReview | None = None,
    ) -> SourceRecord:
        """Delegate promotion to the sole restricted canonical writer."""
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
        if proof_review is None:
            self._deny_promotion(
                feedback,
                source_id=source_id,
                reason_code="PROOF_REVIEW_REQUIRED",
                authorization=authorization,
            )
            raise FeedbackPromotionNotAuthorizedError(
                "structured proof review is required"
            )
        if self.canonical_writer is None:
            self._deny_promotion(
                feedback,
                source_id=source_id,
                reason_code="CANONICAL_WRITER_REQUIRED",
                authorization=authorization,
            )
            raise FeedbackPromotionNotAuthorizedError(
                "restricted canonical writer is not configured"
            )

        try:
            return self.canonical_writer.promote_feedback(
                feedback,
                source_id=source_id,
                source_location=source_location,
                authorization=authorization,
                proof_review=proof_review,
            )
        except CanonicalWriteAuthorizationError as exc:
            raise FeedbackPromotionNotAuthorizedError(str(exc)) from exc
        except CanonicalWriteIntegrityError as exc:
            if feedback.provenance != "REAL":
                raise FeedbackPromotionProhibitedError(str(exc)) from exc
            raise FeedbackPromotionError(str(exc)) from exc
        except CanonicalTargetReservedError as exc:
            raise FeedbackPromotionError(str(exc)) from exc
