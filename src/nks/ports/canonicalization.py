"""Ports for controlled canonical source creation."""

from __future__ import annotations

from typing import Protocol

from nks.domain.delivery import (
    FeedbackProofReview,
    FeedbackPromotionAuthorization,
    FeedbackRecord,
)
from nks.domain.models import SourceRecord


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
