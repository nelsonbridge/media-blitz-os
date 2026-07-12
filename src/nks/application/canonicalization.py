"""Restricted, content-bound canonical source creation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from nks.domain.delivery import (
    FeedbackProofReview,
    FeedbackPromotionAuthorization,
    FeedbackProvenance,
    FeedbackRecord,
    PromotionDecision,
    ProofReviewDecision,
)
from nks.domain.models import RecordStatus, SourceRecord, WorkflowEvent
from nks.ports.delivery import FeedbackRepository
from nks.ports.repositories import EventRepository, RecordRepository


class CanonicalWriteError(ValueError):
    """Base class for rejected canonical writes."""


class CanonicalWriteAuthorizationError(CanonicalWriteError):
    pass


class CanonicalWriteIntegrityError(CanonicalWriteError):
    pass


class CanonicalTargetReservedError(CanonicalWriteError):
    pass


def feedback_sha256(feedback: FeedbackRecord) -> str:
    """Hash the exact governed feedback representation deterministically."""
    payload = feedback.model_dump(mode="json", exclude={"promoted_to_source_id"})
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def promotion_idempotency_key(
    feedback_hash: str, authorization_id: str, target_source_id: str
) -> str:
    encoded = f"{feedback_hash}:{authorization_id}:{target_source_id}".encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class RestrictedCanonicalSourceWriter:
    """Single ordinary application boundary for feedback-to-source promotion."""

    sources: RecordRepository[SourceRecord]
    feedback: FeedbackRepository
    events: EventRepository

    def _reject(
        self,
        feedback: FeedbackRecord,
        source_id: str,
        authorization: FeedbackPromotionAuthorization,
        reason_code: str,
    ) -> None:
        self.events.append(
            WorkflowEvent(
                event_id=(
                    f"canonical.write_rejected:{feedback.feedback_id}:"
                    f"{source_id}:{reason_code}"
                ),
                event_type="canonical.write_rejected",
                subject_id=feedback.feedback_id,
                payload={
                    "reason_code": reason_code,
                    "target_source_id": source_id,
                    "authorization_id": authorization.authorization_id,
                },
            )
        )

    def promote_feedback(
        self,
        feedback: FeedbackRecord,
        *,
        source_id: str,
        source_location: str,
        authorization: FeedbackPromotionAuthorization,
        proof_review: FeedbackProofReview,
    ) -> SourceRecord:
        digest = feedback_sha256(feedback)

        if feedback.provenance != FeedbackProvenance.REAL:
            self._reject(feedback, source_id, authorization, "PROVENANCE_INELIGIBLE")
            raise CanonicalWriteIntegrityError(
                "only REAL observed feedback is eligible for factual source promotion"
            )
        if authorization.decision != PromotionDecision.APPROVED:
            self._reject(feedback, source_id, authorization, "AUTHORIZATION_DENIED")
            raise CanonicalWriteAuthorizationError("authorization is not APPROVED")
        if authorization.feedback_id != feedback.feedback_id:
            self._reject(feedback, source_id, authorization, "FEEDBACK_ID_MISMATCH")
            raise CanonicalWriteAuthorizationError(
                "authorization does not match feedback"
            )
        if authorization.target_source_id != source_id:
            self._reject(feedback, source_id, authorization, "TARGET_ID_MISMATCH")
            raise CanonicalWriteAuthorizationError(
                "authorization does not match target source"
            )
        if authorization.feedback_sha256 != digest:
            self._reject(feedback, source_id, authorization, "CONTENT_HASH_MISMATCH")
            raise CanonicalWriteAuthorizationError(
                "authorization is not bound to current feedback content"
            )
        if authorization.proof_review_id != proof_review.review_id:
            self._reject(feedback, source_id, authorization, "PROOF_REVIEW_MISMATCH")
            raise CanonicalWriteAuthorizationError(
                "authorization does not match proof review"
            )
        if proof_review.feedback_id != feedback.feedback_id:
            self._reject(feedback, source_id, authorization, "REVIEW_FEEDBACK_MISMATCH")
            raise CanonicalWriteIntegrityError("proof review references other feedback")
        if proof_review.feedback_sha256 != digest:
            self._reject(feedback, source_id, authorization, "REVIEW_HASH_MISMATCH")
            raise CanonicalWriteIntegrityError(
                "proof review is stale for current feedback content"
            )
        if proof_review.decision != ProofReviewDecision.ELIGIBLE:
            self._reject(feedback, source_id, authorization, "PROOF_REVIEW_INELIGIBLE")
            raise CanonicalWriteIntegrityError(
                "proof review did not mark feedback eligible"
            )

        expected_key = promotion_idempotency_key(
            digest, authorization.authorization_id, source_id
        )
        if authorization.idempotency_key != expected_key:
            self._reject(feedback, source_id, authorization, "IDEMPOTENCY_KEY_MISMATCH")
            raise CanonicalWriteAuthorizationError("invalid promotion idempotency key")

        existing = self.sources.get(source_id)
        if existing is not None:
            if (
                existing.metadata.get("promotion_idempotency_key") == expected_key
                and existing.metadata.get("feedback_sha256") == digest
            ):
                return existing
            self._reject(feedback, source_id, authorization, "TARGET_ALREADY_RESERVED")
            raise CanonicalTargetReservedError(
                f"canonical source identifier {source_id} is already reserved"
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
                *proof_review.limitations,
            ],
            metadata={
                "feedback_id": feedback.feedback_id,
                "feedback_sha256": digest,
                "publication_id": feedback.publication_id,
                "platform": feedback.platform,
                "provenance": feedback.provenance,
                "lineage_ids": feedback.lineage_ids,
                "authorization_id": authorization.authorization_id,
                "authorized_by": authorization.authorized_by,
                "authorization_justification": authorization.justification,
                "proof_review_id": proof_review.review_id,
                "reviewed_by": proof_review.reviewed_by,
                "promotion_idempotency_key": expected_key,
                "canonical_writer": "RestrictedCanonicalSourceWriter",
            },
        )

        saved_source = self.sources.save(source)
        self.feedback.save(
            feedback.model_copy(update={"promoted_to_source_id": source_id})
        )
        self.events.append(
            WorkflowEvent(
                event_id=f"canonical.source_created:{source_id}:{expected_key[:16]}",
                event_type="canonical.source_created",
                subject_id=source_id,
                payload={
                    "feedback_id": feedback.feedback_id,
                    "feedback_sha256": digest,
                    "authorization_id": authorization.authorization_id,
                    "proof_review_id": proof_review.review_id,
                    "promotion_idempotency_key": expected_key,
                },
            )
        )
        return saved_source
