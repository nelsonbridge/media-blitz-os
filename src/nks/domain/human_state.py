"""Governed temporal human-state and model-feedback domain models."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TemporalStatus(StrEnum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"
    CONDITIONAL = "CONDITIONAL"
    CONTEXT_SPECIFIC = "CONTEXT_SPECIFIC"
    TENTATIVE = "TENTATIVE"
    DISPUTED = "DISPUTED"
    UNRESOLVED = "UNRESOLVED"
    EXPIRED = "EXPIRED"


class ExpressionStrength(StrEnum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    TENTATIVE = "TENTATIVE"


class TransitionOrigin(StrEnum):
    SUBJECT_DECLARED = "SUBJECT_DECLARED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    GOVERNED_INFERENCE = "GOVERNED_INFERENCE"


class TransitionType(StrEnum):
    CLARIFICATION = "CLARIFICATION"
    REFINEMENT = "REFINEMENT"
    CONDITIONAL_REVISION = "CONDITIONAL_REVISION"
    FULL_REVERSAL = "FULL_REVERSAL"
    CONTEXT_EXPANSION = "CONTEXT_EXPANSION"
    CONTEXT_RESTRICTION = "CONTEXT_RESTRICTION"
    TEMPORARY_DEVIATION = "TEMPORARY_DEVIATION"
    RETRACTION = "RETRACTION"
    CONFIDENCE_INCREASE = "CONFIDENCE_INCREASE"
    CONFIDENCE_DECREASE = "CONFIDENCE_DECREASE"
    VALUE_STABLE_CONCLUSION_CHANGED = "VALUE_STABLE_CONCLUSION_CHANGED"
    UNRESOLVED_CONTRADICTION = "UNRESOLVED_CONTRADICTION"


class IngestionScope(StrEnum):
    PERSONALIZATION = "PERSONALIZATION"
    RETRIEVAL = "RETRIEVAL"
    EVALUATION_ONLY = "EVALUATION_ONLY"
    REPLAY_TESTING = "REPLAY_TESTING"
    FINE_TUNING = "FINE_TUNING"
    TRAINING = "TRAINING"
    EXTERNAL_MODEL_TRANSMISSION = "EXTERNAL_MODEL_TRANSMISSION"


class HumanStateObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    domain: str = Field(min_length=1)
    state_type: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    observed_at: datetime
    effective_from: date
    effective_until: date | None = None
    context: list[str] = Field(default_factory=list)
    expression_strength: ExpressionStrength
    confidence: str = Field(min_length=1)
    temporal_status: TemporalStatus
    supersedes_observation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_temporal_window(self) -> HumanStateObservation:
        if self.effective_until and self.effective_until < self.effective_from:
            raise ValueError("effective_until cannot precede effective_from")
        if self.temporal_status == TemporalStatus.SUPERSEDED and not self.supersedes_observation_id:
            raise ValueError("SUPERSEDED observations require supersedes_observation_id")
        return self


class HumanStateTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    from_observation_id: str = Field(min_length=1)
    to_observation_id: str = Field(min_length=1)
    transition_type: TransitionType
    origin: TransitionOrigin
    detected_at: datetime
    stated_reason: str | None = None
    inferred_causes: list[str] = Field(default_factory=list)
    durability: str = Field(min_length=1)
    reversibility: str = Field(min_length=1)
    confidence: str = Field(min_length=1)
    approved_for_model_feedback: bool = False
    approved_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_transition_authority(self) -> HumanStateTransition:
        if self.from_observation_id == self.to_observation_id:
            raise ValueError("transition endpoints must differ")
        if self.origin == TransitionOrigin.GOVERNED_INFERENCE and not self.inferred_causes:
            raise ValueError("governed inference requires inferred_causes")
        if self.approved_for_model_feedback and not self.approved_by:
            raise ValueError("approved model feedback requires approved_by")
        return self


class ModelIngestionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    observation_id: str = Field(min_length=1)
    observation_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    approved_scopes: set[IngestionScope] = Field(default_factory=set)
    denied_scopes: set[IngestionScope] = Field(default_factory=set)
    requires_context_match: bool = True
    approved_by: str = Field(min_length=1)
    approved_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_scope_separation(self) -> ModelIngestionPolicy:
        overlap = self.approved_scopes & self.denied_scopes
        if overlap:
            raise ValueError(f"scopes cannot be both approved and denied: {sorted(overlap)}")
        return self


class ModelFeedbackPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str
    domain: str
    current_observation: HumanStateObservation
    historical_observations: list[HumanStateObservation] = Field(default_factory=list)
    transitions: list[HumanStateTransition] = Field(default_factory=list)
    permitted_scope: IngestionScope
    behavioral_instructions: dict[str, bool] = Field(default_factory=dict)


class ModelFeedbackReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt_id: str
    subject_id: str
    domain: str
    observation_ids: list[str]
    transition_ids: list[str]
    policy_id: str
    destination_scope: IngestionScope
    payload_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    published_at: datetime
    publisher_version: str
    revocable: bool = True
