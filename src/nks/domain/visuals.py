"""Platform-neutral visual rendering request and asset models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VisualAssetStatus(StrEnum):
    BRIEFED = "briefed"
    GENERATED = "generated"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"


class VisualRenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    visual_id: str
    publication_id: str
    asset_type: str
    prompt: str
    proof_boundaries: list[str] = Field(default_factory=list)
    dimensions: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisualAssetRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str
    visual_id: str
    publication_id: str
    asset_type: str
    status: VisualAssetStatus
    renderer: str
    location: str | None = None
    request_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
