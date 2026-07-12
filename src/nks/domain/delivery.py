"""Platform-neutral publication delivery and feedback models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class DeliveryStatus(StrEnum):
    PREPARED = "prepared"
    PUBLISHED = "published"
    FAILED = "failed"


class FeedbackClassification(StrEnum):
    COMMENT = "comment"
    QUESTION = "question"
    CORRECTION = "correction"
    SIGNAL = "signal"
    METRIC = "metric"
    EDITORIAL_LESSON = "editorial-lesson"


class FeedbackProvenance(StrEnum):
    """Origin category, not a truth or confidence classification."""

    REAL = "REAL"
    SYNTHETIC = "SYNTHETIC"
    REPLAY = "REPLAY"


class PromotionDecision(StrEnum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class ProofReviewDecision(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


class PublicationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publication_id: str
    platform: str
    title: str
    body: str
    asset_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PublicationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt_id: str
    publication_id: str
    platform: str
    status: DeliveryStatus
    public_url: HttpUrl | None = None
    external_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feedback_id: str = Field(min_length=1)
    publication_id: str = Field(min_length=1)
    derivative_id: str | None = None
    platform: str = Field(min_length=1)
    classification: FeedbackClassification
    content: str = Field(min_length=1)
    provenance: FeedbackProvenance
    scenario_id: str | None = None
    lineage_ids: list[str] = Field(min_length=1)
    proof_boundaries: list[str] = Field(min_length=1)
    source_url: HttpUrl | None = None
    metric_name: str | None = None
    metric_value: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    promoted_to_source_id: str | None = None

    @model_validator(mode="after")
    def validate_integrity_boundary(self) -> FeedbackRecord:
        if self.publication_id not in self.lineage_ids:
            raise ValueError("lineage_ids must include publication_id")

        if self.provenance in {
            FeedbackProvenance.SYNTHETIC,
            FeedbackProvenance.REPLAY,
        } and not self.scenario_id:
            raise ValueError(
                "scenario_id is required for SYNTHETIC and REPLAY feedback"
            )

        if self.provenance == FeedbackProvenance.REAL and self.scenario_id is not None:
            raise ValueError("REAL feedback cannot carry scenario_id")

        return self


class FeedbackProofReview(BaseModel):
    """Structured human review bound to the exact feedback content."""

    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(min_length=1)
    feedback_id: str = Field(min_length=1)
    feedback_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_by: str = Field(min_length=1)
    reviewed_at: datetime
    decision: ProofReviewDecision
    evidence_ids: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(min_length=1)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_review_lifecycle(self) -> FeedbackProofReview:
        if self.expires_at is not None and self.expires_at <= self.reviewed_at:
            raise ValueError("expires_at must be after reviewed_at")
        return self


class FeedbackPromotionAuthorization(BaseModel):
    """Explicit authorization bound to exact feedback, review, and target source."""

    model_config = ConfigDict(extra="forbid")

    authorization_id: str = Field(min_length=1)
    feedback_id: str = Field(min_length=1)
    feedback_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    target_source_id: str = Field(min_length=1)
    proof_review_id: str | None = None
    idempotency_key: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    authorized_by: str = Field(min_length=1)
    justification: str = Field(min_length=1)
    decision: PromotionDecision
    authorized_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_authorization_boundary(self) -> FeedbackPromotionAuthorization:
        if self.expires_at is not None and self.expires_at <= self.authorized_at:
            raise ValueError("expires_at must be after authorized_at")
        if self.decision == PromotionDecision.APPROVED:
            if self.feedback_sha256 is None:
                raise ValueError("approved authorization requires feedback_sha256")
            if self.proof_review_id is None:
                raise ValueError("approved authorization requires proof_review_id")
            if self.idempotency_key is None:
                raise ValueError("approved authorization requires idempotency_key")
        return self


class FeedbackScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    feedback: FeedbackRecord

    @model_validator(mode="after")
    def validate_synthetic_scenario(self) -> FeedbackScenario:
        if self.feedback.provenance != FeedbackProvenance.SYNTHETIC:
            raise ValueError("scenario feedback must have SYNTHETIC provenance")
        if self.feedback.scenario_id != self.scenario_id:
            raise ValueError("scenario feedback scenario_id must match scenario_id")
        return self
