"""Platform-neutral publication delivery and feedback models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


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
    REAL = "real"
    SYNTHETIC = "synthetic"
    REPLAY = "replay"


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

    feedback_id: str
    publication_id: str
    derivative_id: str | None = None
    platform: str
    classification: FeedbackClassification
    content: str
    provenance: FeedbackProvenance = FeedbackProvenance.REAL
    scenario_id: str | None = None
    source_url: HttpUrl | None = None
    metric_name: str | None = None
    metric_value: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    promoted_to_source_id: str | None = None


class FeedbackScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    description: str
    feedback: FeedbackRecord
