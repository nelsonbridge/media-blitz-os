"""Ports for controlled canonical source creation."""

from __future__ import annotations

from typing import Protocol

from nks.domain.canonicalization import (
    CanonicalMaintenanceAuthorization,
    CanonicalTargetReservation,
)
from nks.domain.delivery import (
    FeedbackProofReview,
    FeedbackPromotionAuthorization,
    FeedbackRecord,
)
from nks.domain.models import SourceRecord


class CanonicalStoreConflictError(ValueError):
    """Raised when a canonical target or idempotency key conflicts."""


class CanonicalSourceStore(Protocol):
    """Persistence contract available only to the restricted writer."""

    def get(self, source_id: str) -> SourceRecord | None: ...

    def get_reservation(
        self, source_id: str
    ) -> CanonicalTargetReservation | None: ...

    def reserve(
        self, reservation: CanonicalTargetReservation
    ) -> CanonicalTargetReservation: ...

    def commit(
        self,
        reservation: CanonicalTargetReservation,
        source: SourceRecord,
    ) -> SourceRecord: ...


class CanonicalSourceWriter(Protocol):
    """The only ordinary application boundary permitted to create sources."""

    def promote_feedback(
        self,
        feedback: FeedbackRecord,
        *,
        source_id: str,
        source_location: str,
        authorization: FeedbackPromotionAuthorization,
        proof_review: FeedbackProofReview,
    ) -> SourceRecord: ...

    def write_maintenance_source(
        self,
        source: SourceRecord,
        *,
        authorization: CanonicalMaintenanceAuthorization,
    ) -> SourceRecord: ...
