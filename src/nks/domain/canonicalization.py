"""Domain contracts for controlled canonical source mutation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.domain.delivery import PromotionDecision


class CanonicalWriteMode(StrEnum):
    """Explicit operating mode for every canonical source creation."""

    NORMAL = "NORMAL"
    MIGRATION = "MIGRATION"
    DISASTER_RECOVERY = "DISASTER_RECOVERY"
    BOOTSTRAP = "BOOTSTRAP"


class ReservationStatus(StrEnum):
    RESERVED = "RESERVED"
    COMMITTED = "COMMITTED"


class CanonicalTargetReservation(BaseModel):
    """Durable reservation preventing conflicting use of a canonical source ID."""

    model_config = ConfigDict(extra="forbid")

    reservation_id: str = Field(min_length=1)
    target_source_id: str = Field(min_length=1)
    idempotency_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    authorization_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mode: CanonicalWriteMode
    status: ReservationStatus = ReservationStatus.RESERVED
    reserved_at: datetime
    committed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_status_timestamps(self) -> CanonicalTargetReservation:
        if self.status == ReservationStatus.RESERVED and self.committed_at is not None:
            raise ValueError("RESERVED target cannot have committed_at")
        if self.status == ReservationStatus.COMMITTED and self.committed_at is None:
            raise ValueError("COMMITTED target requires committed_at")
        return self


class CanonicalMaintenanceAuthorization(BaseModel):
    """Explicit authorization for migration, recovery, or bootstrap writes."""

    model_config = ConfigDict(extra="forbid")

    authorization_id: str = Field(min_length=1)
    mode: CanonicalWriteMode
    target_source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    idempotency_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    authorized_by: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decision: PromotionDecision
    authorized_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_maintenance_scope(self) -> CanonicalMaintenanceAuthorization:
        if self.mode == CanonicalWriteMode.NORMAL:
            raise ValueError("maintenance authorization cannot use NORMAL mode")
        if self.expires_at is not None and self.expires_at <= self.authorized_at:
            raise ValueError("expires_at must be after authorized_at")
        return self
