"""Vendor-neutral social publication port and contract models."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SocialPublicationRequest(BaseModel):
    """Approved derivative payload presented to a social publishing adapter."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    package_id: str = Field(min_length=1)
    publication_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    account_reference: str = Field(min_length=1)
    body: str = Field(min_length=1)
    asset_ids: list[str] = Field(default_factory=list)
    approval_required: bool = True
    approved: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None
    publish_at: datetime | None = None
    idempotency_key: str = Field(min_length=1)
    credential_reference: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_approval_record(self) -> "SocialPublicationRequest":
        if self.approved and (not self.approved_by or self.approved_at is None):
            raise ValueError("approved requests require approved_by and approved_at")
        return self


class SocialPublicationResult(BaseModel):
    """Structured result returned by every social publication adapter."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    status: str
    external_id: str | None = None
    external_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retryable: bool = False
    manual_fallback_required: bool = False
    idempotency_key: str
    created_at: datetime
    audit_log: tuple[str, ...] = ()


class SocialPublisher(Protocol):
    """Port implemented by TryPost, Postiz, manual, and test adapters."""

    def publish(
        self,
        request: SocialPublicationRequest,
        *,
        dry_run: bool,
    ) -> SocialPublicationResult: ...


class DispatchLedger(Protocol):
    """Idempotency and receipt store independent of the publishing vendor."""

    def get(self, idempotency_key: str) -> SocialPublicationResult | None: ...

    def save(self, result: SocialPublicationResult) -> None: ...
