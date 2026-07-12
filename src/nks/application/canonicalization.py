"""Restricted, content-bound canonical source creation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from nks.domain.canonicalization import (
    CanonicalMaintenanceAuthorization,
    CanonicalTargetReservation,
    CanonicalWriteMode,
)
from nks.domain.delivery import (
    FeedbackProofReview,
    FeedbackPromotionAuthorization,
    FeedbackProvenance,
    FeedbackRecord,
    PromotionDecision,
    ProofReviewDecision,
)
from nks.domain.models import RecordStatus, SourceRecord, WorkflowEvent
from nks.ports.canonicalization import (
    CanonicalSourceStore,
    CanonicalStoreConflictError,
)
from nks.ports.delivery import FeedbackRepository
from nks.ports.repositories import EventRepository


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


def source_sha256(source: SourceRecord) -> str:
    """Hash an exact proposed source before canonical-writer metadata is added."""
    payload = source.model_dump(mode="json")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def promotion_idempotency_key(
    content_hash: str, authorization_id: str, target_source_id: str
) -> str:
    encoded = f"{content_hash}:{authorization_id}:{target_source_id}".encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class RestrictedCanonicalSourceWriter:
    """Single application boundary for all canonical source creation."""

    store: CanonicalSourceStore
    feedback: FeedbackRepository
    events: EventRepository
    clock: Callable[[], datetime] = field(
        default=lambda: datetime.now(timezone.utc)
    )

    def _reject(
        self,
        *,
        subject_id: str,
        source_id: str,
        authorization_id: str | None,
        reason_code: str,
        mode: CanonicalWriteMode,
    ) -> None:
        self.events.append(
            WorkflowEvent(
                event_id=(
                    f"canonical.write_rejected:{subject_id}:"
                    f"{source_id}:{reason_code}"
                ),
                event_type="canonical.write_rejected",
                subject_id=subject_id,
                payload={
                    "reason_code": reason_code,
                    "target_source_id": source_id,
                    "authorization_id": authorization_id,
                    "mode": mode,
                },
            )
        )

    def _reject_feedback(
        self,
        feedback: FeedbackRecord,
        source_id: str,
        authorization: FeedbackPromotionAuthorization,
        reason_code: str,
    ) -> None:
        self._reject(
            subject_id=feedback.feedback_id,
            source_id=source_id,
            authorization_id=authorization.authorization_id,
            reason_code=reason_code,
            mode=CanonicalWriteMode.NORMAL,
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
        now = self.clock()
        digest = feedback_sha256(feedback)

        if feedback.provenance != FeedbackProvenance.REAL:
            self._reject_feedback(
                feedback, source_id, authorization, "PROVENANCE_INELIGIBLE"
            )
            raise CanonicalWriteIntegrityError(
                "only REAL observed feedback is eligible for factual source promotion"
            )
        if (
            feedback.promoted_to_source_id is not None
            and feedback.promoted_to_source_id != source_id
        ):
            self._reject_feedback(
                feedback, source_id, authorization, "ALREADY_PROMOTED_ELSEWHERE"
            )
            raise CanonicalWriteIntegrityError(
                "feedback is already promoted to a different canonical source"
            )
        if authorization.decision != PromotionDecision.APPROVED:
            self._reject_feedback(
                feedback, source_id, authorization, "AUTHORIZATION_DENIED"
            )
            raise CanonicalWriteAuthorizationError("authorization is not APPROVED")
        if authorization.revoked_at is not None:
            self._reject_feedback(
                feedback, source_id, authorization, "AUTHORIZATION_REVOKED"
            )
            raise CanonicalWriteAuthorizationError("authorization has been revoked")
        if authorization.expires_at is not None and now >= authorization.expires_at:
            self._reject_feedback(
                feedback, source_id, authorization, "AUTHORIZATION_EXPIRED"
            )
            raise CanonicalWriteAuthorizationError("authorization has expired")
        if authorization.feedback_id != feedback.feedback_id:
            self._reject_feedback(
                feedback, source_id, authorization, "FEEDBACK_ID_MISMATCH"
            )
            raise CanonicalWriteAuthorizationError(
                "authorization does not match feedback"
            )
        if authorization.target_source_id != source_id:
            self._reject_feedback(
                feedback, source_id, authorization, "TARGET_ID_MISMATCH"
            )
            raise CanonicalWriteAuthorizationError(
                "authorization does not match target source"
            )
        if authorization.feedback_sha256 != digest:
            self._reject_feedback(
                feedback, source_id, authorization, "CONTENT_HASH_MISMATCH"
            )
            raise CanonicalWriteAuthorizationError(
                "authorization is not bound to current feedback content"
            )
        if authorization.proof_review_id != proof_review.review_id:
            self._reject_feedback(
                feedback, source_id, authorization, "PROOF_REVIEW_MISMATCH"
            )
            raise CanonicalWriteAuthorizationError(
                "authorization does not match proof review"
            )
        if proof_review.feedback_id != feedback.feedback_id:
            self._reject_feedback(
                feedback, source_id, authorization, "REVIEW_FEEDBACK_MISMATCH"
            )
            raise CanonicalWriteIntegrityError("proof review references other feedback")
        if proof_review.feedback_sha256 != digest:
            self._reject_feedback(
                feedback, source_id, authorization, "REVIEW_HASH_MISMATCH"
            )
            raise CanonicalWriteIntegrityError(
                "proof review is stale for current feedback content"
            )
        if proof_review.decision != ProofReviewDecision.ELIGIBLE:
            self._reject_feedback(
                feedback, source_id, authorization, "PROOF_REVIEW_INELIGIBLE"
            )
            raise CanonicalWriteIntegrityError(
                "proof review did not mark feedback eligible"
            )
        if proof_review.revoked_at is not None:
            self._reject_feedback(
                feedback, source_id, authorization, "PROOF_REVIEW_REVOKED"
            )
            raise CanonicalWriteIntegrityError("proof review has been revoked")
        if proof_review.expires_at is not None and now >= proof_review.expires_at:
            self._reject_feedback(
                feedback, source_id, authorization, "PROOF_REVIEW_EXPIRED"
            )
            raise CanonicalWriteIntegrityError("proof review has expired")

        expected_key = promotion_idempotency_key(
            digest, authorization.authorization_id, source_id
        )
        if authorization.idempotency_key != expected_key:
            self._reject_feedback(
                feedback, source_id, authorization, "IDEMPOTENCY_KEY_MISMATCH"
            )
            raise CanonicalWriteAuthorizationError("invalid promotion idempotency key")

        existing = self.store.get(source_id)
        if existing is not None:
            if (
                existing.metadata.get("promotion_idempotency_key") == expected_key
                and existing.metadata.get("content_sha256") == digest
            ):
                self.feedback.save(
                    feedback.model_copy(update={"promoted_to_source_id": source_id})
                )
                return existing
            self._reject_feedback(
                feedback, source_id, authorization, "TARGET_ALREADY_RESERVED"
            )
            raise CanonicalTargetReservedError(
                f"canonical source identifier {source_id} is already reserved"
            )

        reservation = CanonicalTargetReservation(
            reservation_id=f"canonical-reservation:{source_id}",
            target_source_id=source_id,
            idempotency_key=expected_key,
            authorization_id=authorization.authorization_id,
            subject_id=feedback.feedback_id,
            content_sha256=digest,
            mode=CanonicalWriteMode.NORMAL,
            reserved_at=now,
        )
        try:
            reservation = self.store.reserve(reservation)
        except CanonicalStoreConflictError as exc:
            self._reject_feedback(
                feedback, source_id, authorization, "TARGET_ALREADY_RESERVED"
            )
            raise CanonicalTargetReservedError(str(exc)) from exc

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
                "content_sha256": digest,
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
                "canonical_reservation_id": reservation.reservation_id,
                "canonical_write_mode": CanonicalWriteMode.NORMAL,
                "canonical_writer": "RestrictedCanonicalSourceWriter",
            },
        )

        try:
            saved_source = self.store.commit(reservation, source)
        except CanonicalStoreConflictError as exc:
            self._reject_feedback(
                feedback, source_id, authorization, "TARGET_COMMIT_CONFLICT"
            )
            raise CanonicalTargetReservedError(str(exc)) from exc

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
                    "content_sha256": digest,
                    "authorization_id": authorization.authorization_id,
                    "proof_review_id": proof_review.review_id,
                    "promotion_idempotency_key": expected_key,
                    "reservation_id": reservation.reservation_id,
                    "mode": CanonicalWriteMode.NORMAL,
                },
            )
        )
        return saved_source

    def write_maintenance_source(
        self,
        source: SourceRecord,
        *,
        authorization: CanonicalMaintenanceAuthorization,
    ) -> SourceRecord:
        """Create a source through an explicit migration/recovery/bootstrap exception."""
        now = self.clock()
        digest = source_sha256(source)
        mode = authorization.mode

        def reject(reason_code: str) -> None:
            self._reject(
                subject_id=source.id,
                source_id=source.id,
                authorization_id=authorization.authorization_id,
                reason_code=reason_code,
                mode=mode,
            )

        if authorization.decision != PromotionDecision.APPROVED:
            reject("MAINTENANCE_AUTHORIZATION_DENIED")
            raise CanonicalWriteAuthorizationError(
                "maintenance authorization is not APPROVED"
            )
        if authorization.revoked_at is not None:
            reject("MAINTENANCE_AUTHORIZATION_REVOKED")
            raise CanonicalWriteAuthorizationError(
                "maintenance authorization has been revoked"
            )
        if authorization.expires_at is not None and now >= authorization.expires_at:
            reject("MAINTENANCE_AUTHORIZATION_EXPIRED")
            raise CanonicalWriteAuthorizationError(
                "maintenance authorization has expired"
            )
        if authorization.target_source_id != source.id:
            reject("MAINTENANCE_TARGET_MISMATCH")
            raise CanonicalWriteAuthorizationError(
                "maintenance authorization does not match target source"
            )
        if authorization.source_sha256 != digest:
            reject("MAINTENANCE_CONTENT_HASH_MISMATCH")
            raise CanonicalWriteAuthorizationError(
                "maintenance authorization is not bound to source content"
            )

        expected_key = promotion_idempotency_key(
            digest, authorization.authorization_id, source.id
        )
        if authorization.idempotency_key != expected_key:
            reject("MAINTENANCE_IDEMPOTENCY_KEY_MISMATCH")
            raise CanonicalWriteAuthorizationError(
                "invalid maintenance idempotency key"
            )

        existing = self.store.get(source.id)
        if existing is not None:
            if (
                existing.metadata.get("promotion_idempotency_key") == expected_key
                and existing.metadata.get("content_sha256") == digest
            ):
                return existing
            reject("MAINTENANCE_TARGET_ALREADY_RESERVED")
            raise CanonicalTargetReservedError(
                f"canonical source identifier {source.id} is already reserved"
            )

        reservation = CanonicalTargetReservation(
            reservation_id=f"canonical-reservation:{source.id}",
            target_source_id=source.id,
            idempotency_key=expected_key,
            authorization_id=authorization.authorization_id,
            subject_id=source.id,
            content_sha256=digest,
            mode=mode,
            reserved_at=now,
        )
        try:
            reservation = self.store.reserve(reservation)
        except CanonicalStoreConflictError as exc:
            reject("MAINTENANCE_TARGET_ALREADY_RESERVED")
            raise CanonicalTargetReservedError(str(exc)) from exc

        governed_source = source.model_copy(
            update={
                "metadata": {
                    **source.metadata,
                    "content_sha256": digest,
                    "authorization_id": authorization.authorization_id,
                    "authorized_by": authorization.authorized_by,
                    "authorization_reason": authorization.reason,
                    "promotion_idempotency_key": expected_key,
                    "canonical_reservation_id": reservation.reservation_id,
                    "canonical_write_mode": mode,
                    "canonical_writer": "RestrictedCanonicalSourceWriter",
                }
            }
        )
        try:
            saved_source = self.store.commit(reservation, governed_source)
        except CanonicalStoreConflictError as exc:
            reject("MAINTENANCE_TARGET_COMMIT_CONFLICT")
            raise CanonicalTargetReservedError(str(exc)) from exc

        self.events.append(
            WorkflowEvent(
                event_id=f"canonical.source_created:{source.id}:{expected_key[:16]}",
                event_type="canonical.source_created",
                subject_id=source.id,
                payload={
                    "content_sha256": digest,
                    "authorization_id": authorization.authorization_id,
                    "promotion_idempotency_key": expected_key,
                    "reservation_id": reservation.reservation_id,
                    "mode": mode,
                },
            )
        )
        return saved_source
