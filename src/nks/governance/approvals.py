"""Context-bound approval grants and fail-closed evaluation.

This module implements the executable contract accepted in ADR-0001. It does
not persist or consume approvals; it evaluates whether a supplied grant may
legitimately authorize one exact requested operation. Reservation and durable
consumption remain application and adapter responsibilities.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExecutionContext(StrEnum):
    TEST = "TEST"
    PRODUCTION = "PRODUCTION"


class ApprovalDecision(StrEnum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class ApprovalConsumptionStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    REVOKED = "REVOKED"


class ApprovalGrant(BaseModel):
    """Authority granted for an exact bounded operation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    approval_id: str = Field(min_length=1)
    decision: ApprovalDecision
    execution_context: ExecutionContext
    permitted_actions: set[str] = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    authorized_by: str = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    issued_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    consumption_status: ApprovalConsumptionStatus = ApprovalConsumptionStatus.AVAILABLE
    consumed_by_transaction_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "ApprovalGrant":
        if self.expires_at is not None and self.expires_at <= self.issued_at:
            raise ValueError("expires_at must follow issued_at")
        if self.revoked_at is not None and self.revoked_at < self.issued_at:
            raise ValueError("revoked_at cannot precede issued_at")
        if self.consumption_status == ApprovalConsumptionStatus.CONSUMED:
            if not self.consumed_by_transaction_id:
                raise ValueError("consumed approvals require consumed_by_transaction_id")
        elif self.consumed_by_transaction_id is not None:
            raise ValueError("only consumed approvals may name a consuming transaction")
        return self


class ApprovalRequest(BaseModel):
    """The exact operation seeking authority."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_context: ExecutionContext
    action: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    acceptable_authority_classes: set[str] = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    requested_at: datetime


class ApprovalEvaluation(BaseModel):
    """Immutable result of evaluating one grant against one request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    approval_id: str
    authorized: bool
    exact_retry: bool = False
    reasons: list[str] = Field(default_factory=list)
    evaluated_at: datetime
    request: ApprovalRequest


def evaluate_approval(
    grant: ApprovalGrant,
    request: ApprovalRequest,
    *,
    now: datetime | None = None,
) -> ApprovalEvaluation:
    """Evaluate all ADR-0001 dimensions without mutating the grant.

    Ambiguity fails closed. A consumed grant is accepted only for an exact retry
    using the same transaction identifier; this does not authorize a second
    consumption operation.
    """

    evaluated_at = now or request.requested_at
    reasons: list[str] = []

    if grant.decision != ApprovalDecision.APPROVED:
        reasons.append("grant decision is not APPROVED")
    if grant.execution_context != request.execution_context:
        reasons.append("execution context does not match")
    if request.action not in grant.permitted_actions:
        reasons.append("requested action is not permitted")
    if grant.subject_id != request.subject_id:
        reasons.append("subject does not match")
    if grant.content_sha256 != request.content_sha256:
        reasons.append("content hash does not match")
    if grant.authority_class not in request.acceptable_authority_classes:
        reasons.append("authority class is insufficient")
    if grant.expires_at is not None and grant.expires_at <= evaluated_at:
        reasons.append("grant is expired")
    if grant.revoked_at is not None and grant.revoked_at <= evaluated_at:
        reasons.append("grant is revoked")
    if grant.consumption_status == ApprovalConsumptionStatus.REVOKED:
        reasons.append("grant consumption state is REVOKED")

    exact_retry = False
    if grant.consumption_status == ApprovalConsumptionStatus.CONSUMED:
        if grant.consumed_by_transaction_id == request.transaction_id:
            exact_retry = True
        else:
            reasons.append("grant was consumed by another transaction")

    return ApprovalEvaluation(
        approval_id=grant.approval_id,
        authorized=not reasons,
        exact_retry=exact_retry and not reasons,
        reasons=reasons,
        evaluated_at=evaluated_at,
        request=request,
    )
