"""Product-neutral Enki contracts for governed downstream model influence."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.enki.contracts import ConfidenceAssertion, SubjectRef
from nks.governance.approvals import ExecutionContext


class ModelUseAudience(StrEnum):
    INTERNAL_MODEL = "INTERNAL_MODEL"
    EXTERNAL_MODEL = "EXTERNAL_MODEL"


class ModelUseItemKind(StrEnum):
    OBSERVATION = "OBSERVATION"
    RELATIONSHIP = "RELATIONSHIP"
    FINDING = "FINDING"
    TRANSITION = "TRANSITION"


class ModelUseDirectiveAction(StrEnum):
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"


class ModelUseSensitivity(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class ModelUseConsentState(StrEnum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    REVOKED = "REVOKED"
    NOT_REQUIRED = "NOT_REQUIRED"
    UNKNOWN = "UNKNOWN"


class ModelUseTemporalState(StrEnum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    DISPUTED = "DISPUTED"
    INAPPLICABLE = "INAPPLICABLE"
    RETRACTED = "RETRACTED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"


class ModelUseDecisionAction(StrEnum):
    INCLUDE = "INCLUDE"
    DEFER = "DEFER"
    WITHHOLD = "WITHHOLD"


class EnkiModelUseItem(BaseModel):
    """One attributable canonical-state item considered for model influence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str = Field(min_length=1)
    item_kind: ModelUseItemKind
    subject: SubjectRef
    domain: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    context: list[str] = Field(default_factory=list)
    temporal_state: ModelUseTemporalState
    confidence: ConfidenceAssertion
    sensitivity: ModelUseSensitivity
    consent_state: ModelUseConsentState
    allowed_purposes: set[str] = Field(min_length=1)
    redaction_required_for: set[ModelUseAudience] = Field(default_factory=set)
    provenance_classification: str = Field(min_length=1)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class EnkiModelUseDirective(BaseModel):
    """Typed, attributable, purpose-bound instruction for one exact item."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    directive_id: str = Field(min_length=1)
    action: ModelUseDirectiveAction
    item_id: str = Field(min_length=1)
    item_kind: ModelUseItemKind
    subject: SubjectRef
    domain: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    audience: ModelUseAudience
    required_context: set[str] = Field(default_factory=set)
    transition_inclusion: bool | None = None
    rationale: str = Field(min_length=1)
    issued_by: str = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    issued_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_transition_choice(self) -> "EnkiModelUseDirective":
        if self.item_kind == ModelUseItemKind.TRANSITION:
            if self.transition_inclusion is None:
                raise ValueError("transition directives require explicit inclusion choice")
        elif self.transition_inclusion is not None:
            raise ValueError("transition_inclusion applies only to transition items")
        if self.expires_at is not None and self.expires_at <= self.issued_at:
            raise ValueError("directive expiry must follow issuance")
        if self.revoked_at is not None and self.revoked_at < self.issued_at:
            raise ValueError("directive revocation cannot precede issuance")
        return self


class EnkiModelUseRequest(BaseModel):
    """Exact context for building one downstream model-use package."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package_id: str = Field(min_length=1)
    subject: SubjectRef
    domain: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    audience: ModelUseAudience
    context: set[str] = Field(default_factory=set)
    execution_context: ExecutionContext
    items: list[EnkiModelUseItem] = Field(default_factory=list)
    directives: list[EnkiModelUseDirective] = Field(default_factory=list)
    requested_at: datetime
    package_version: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unique_identifiers(self) -> "EnkiModelUseRequest":
        item_ids = [item.item_id for item in self.items]
        directive_ids = [directive.directive_id for directive in self.directives]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("model-use item ids must be unique")
        if len(directive_ids) != len(set(directive_ids)):
            raise ValueError("model-use directive ids must be unique")
        return self


class ModelUseItemDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str = Field(min_length=1)
    action: ModelUseDecisionAction
    directive_id: str | None = None
    reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class EnkiModelUsePackage(BaseModel):
    """Deterministic, policy-filtered package safe for a bounded dispatcher."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package_id: str = Field(min_length=1)
    subject: SubjectRef
    domain: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    audience: ModelUseAudience
    context: set[str] = Field(default_factory=set)
    execution_context: ExecutionContext
    included_items: list[EnkiModelUseItem] = Field(default_factory=list)
    decisions: list[ModelUseItemDecision] = Field(default_factory=list)
    directive_ids: list[str] = Field(default_factory=list)
    context_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    created_at: datetime
    package_version: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class ModelUseRevocation(BaseModel):
    """Governed revocation of one exact downstream-use package."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    revocation_id: str = Field(min_length=1)
    package_id: str = Field(min_length=1)
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    subject: SubjectRef
    purpose: str = Field(min_length=1)
    audience: ModelUseAudience
    execution_context: ExecutionContext
    reason: str = Field(min_length=1)
    revoked_by: str = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    revoked_at: datetime
    transaction_id: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class DownstreamEffectStatus(StrEnum):
    NO_EFFECT_TEST = "NO_EFFECT_TEST"
    DISPATCHED = "DISPATCHED"
    FAILED = "FAILED"
    REVOKED = "REVOKED"


class DownstreamEffectReceipt(BaseModel):
    """Attributable result of bounded model-use dispatch or revocation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    effect_id: str = Field(min_length=1)
    package_id: str = Field(min_length=1)
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext
    status: DownstreamEffectStatus
    external_effect: bool
    dispatcher_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    provider_reference: str | None = None
    recorded_at: datetime
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_effect_boundary(self) -> "DownstreamEffectReceipt":
        if self.execution_context == ExecutionContext.TEST:
            if self.external_effect:
                raise ValueError("TEST effect receipts cannot claim an external effect")
            if self.provider_reference is not None:
                raise ValueError("TEST effect receipts cannot contain provider references")
            if self.status not in {
                DownstreamEffectStatus.NO_EFFECT_TEST,
                DownstreamEffectStatus.REVOKED,
            }:
                raise ValueError("TEST effect receipts must be no-effect or revocation records")
        if self.status == DownstreamEffectStatus.DISPATCHED and not self.external_effect:
            raise ValueError("DISPATCHED receipts must record an external effect")
        return self
