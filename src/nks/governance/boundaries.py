"""Provider-neutral boundary contracts for zero-cost Enki isolation proof.

The contracts are deliberately infrastructure-agnostic. They bind namespace,
tenant, subject, domain, audience, and execution context into one immutable
security boundary that is exercised with governed TEST data.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext


_SAFE_IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"


class BoundaryAction(StrEnum):
    WRITE = "WRITE"
    READ = "READ"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    RECOVER = "RECOVER"
    REPLAY = "REPLAY"


class BoundaryOutcome(StrEnum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"


class BoundaryContext(BaseModel):
    """Exact immutable scope for one governed record or operation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    namespace_id: str = Field(pattern=_SAFE_IDENTIFIER)
    tenant_id: str = Field(pattern=_SAFE_IDENTIFIER)
    subject_id: str = Field(pattern=_SAFE_IDENTIFIER)
    domain: str = Field(pattern=_SAFE_IDENTIFIER)
    audience: str = Field(pattern=_SAFE_IDENTIFIER)
    execution_context: ExecutionContext

    @model_validator(mode="after")
    def reject_path_shaped_identifiers(self) -> "BoundaryContext":
        for value in (
            self.namespace_id,
            self.tenant_id,
            self.subject_id,
            self.domain,
            self.audience,
        ):
            if value in {".", ".."} or ".." in value or "/" in value or "\\" in value:
                raise ValueError("boundary identifiers cannot contain path traversal")
        return self

    @property
    def boundary_sha256(self) -> str:
        return canonical_sha256(self)


class BoundaryAuthorization(BaseModel):
    """Authority for exact actions inside one exact boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_id: str = Field(min_length=1)
    boundary: BoundaryContext
    permitted_actions: set[BoundaryAction] = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    issued_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "BoundaryAuthorization":
        if self.expires_at is not None and self.expires_at <= self.issued_at:
            raise ValueError("expires_at must follow issued_at")
        if self.revoked_at is not None and self.revoked_at < self.issued_at:
            raise ValueError("revoked_at cannot precede issued_at")
        return self


class BoundaryAccessDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_id: str
    action: BoundaryAction
    requested_boundary_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    outcome: BoundaryOutcome
    reason_code: str
    evaluated_at: datetime


class HumanBoundaryPolicy(BaseModel):
    """Human protections that remain stricter than generic tenant authority."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    consent_granted: bool
    purpose_allowed: bool
    revoked: bool = False
    correction_or_retraction_blocked: bool = False

    @property
    def permits_use(self) -> bool:
        return (
            self.consent_granted
            and self.purpose_allowed
            and not self.revoked
            and not self.correction_or_retraction_blocked
        )


class BoundaryEnvelope(BaseModel):
    """Locally signed TEST envelope used for forged-identity testing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    boundary: BoundaryContext
    payload_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    signature: str = Field(pattern=r"^hmac-sha256:[0-9a-f]{64}$")


class TestBoundarySigner:
    """Disposable TEST-only signer using per-tenant local keys."""

    __test__ = False

    def __init__(self, tenant_keys: dict[str, bytes]) -> None:
        if not tenant_keys or any(not key for key in tenant_keys.values()):
            raise ValueError("non-empty TEST keys are required")
        self._tenant_keys = dict(tenant_keys)

    @staticmethod
    def _message(boundary: BoundaryContext, payload_sha256: str) -> bytes:
        return f"{boundary.boundary_sha256}|{payload_sha256}".encode("utf-8")

    def sign(self, boundary: BoundaryContext, payload_sha256: str) -> BoundaryEnvelope:
        if boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("local boundary signer is TEST-only")
        key = self._tenant_keys.get(boundary.tenant_id)
        if key is None:
            raise ValueError("no TEST key exists for tenant")
        digest = hmac.new(key, self._message(boundary, payload_sha256), hashlib.sha256).hexdigest()
        return BoundaryEnvelope(
            boundary=boundary,
            payload_sha256=payload_sha256,
            signature=f"hmac-sha256:{digest}",
        )

    def verify(self, envelope: BoundaryEnvelope) -> bool:
        key = self._tenant_keys.get(envelope.boundary.tenant_id)
        if key is None or envelope.boundary.execution_context != ExecutionContext.TEST:
            return False
        expected = hmac.new(
            key,
            self._message(envelope.boundary, envelope.payload_sha256),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(envelope.signature, f"hmac-sha256:{expected}")


def evaluate_boundary_authorization(
    authorization: BoundaryAuthorization,
    *,
    action: BoundaryAction,
    requested_boundary: BoundaryContext,
    evaluated_at: datetime,
) -> BoundaryAccessDecision:
    reason = "AUTHORIZED"
    if authorization.boundary != requested_boundary:
        reason = "BOUNDARY_MISMATCH"
    elif requested_boundary.execution_context != ExecutionContext.TEST:
        reason = "TEST_PROOF_CANNOT_AUTHORIZE_PRODUCTION"
    elif action not in authorization.permitted_actions:
        reason = "ACTION_NOT_PERMITTED"
    elif authorization.expires_at is not None and authorization.expires_at <= evaluated_at:
        reason = "AUTHORIZATION_EXPIRED"
    elif authorization.revoked_at is not None and authorization.revoked_at <= evaluated_at:
        reason = "AUTHORIZATION_REVOKED"

    return BoundaryAccessDecision(
        authorization_id=authorization.authorization_id,
        action=action,
        requested_boundary_sha256=requested_boundary.boundary_sha256,
        outcome=BoundaryOutcome.ALLOWED if reason == "AUTHORIZED" else BoundaryOutcome.DENIED,
        reason_code=reason,
        evaluated_at=evaluated_at,
    )
