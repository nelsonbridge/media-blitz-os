"""Domain-neutral contracts for governed reconciliation.

These models structure observations, evidence, relationships, findings, and
disclosure without defining what a subject ought to value or what decision a
subject ought to make.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfidenceLevel(StrEnum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class ExpressionOrigin(StrEnum):
    SELF_DECLARED = "SELF_DECLARED"
    OBSERVED = "OBSERVED"
    GOVERNED_INFERENCE = "GOVERNED_INFERENCE"


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


class ReferenceKind(StrEnum):
    OBSERVATION = "OBSERVATION"
    OBJECTIVE = "OBJECTIVE"
    PRIORITY = "PRIORITY"
    DECISION = "DECISION"
    OUTCOME = "OUTCOME"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    OTHER = "OTHER"


class FindingKind(StrEnum):
    ALIGNMENT = "ALIGNMENT"
    DIVERGENCE = "DIVERGENCE"
    UNCERTAINTY = "UNCERTAINTY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DisclosureAction(StrEnum):
    SURFACE = "SURFACE"
    DEFER = "DEFER"
    WITHHOLD = "WITHHOLD"


class SubjectRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_id: str = Field(min_length=1)
    subject_type: str = Field(min_length=1)
    namespace: str = Field(default="default", min_length=1)


class TemporalApplicability(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    effective_from: date
    effective_until: date | None = None

    @model_validator(mode="after")
    def validate_window(self) -> TemporalApplicability:
        if self.effective_until and self.effective_until < self.effective_from:
            raise ValueError("effective_until cannot precede effective_from")
        return self


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    observed_at: datetime
    provenance_classification: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    level: ConfidenceLevel
    rationale: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(min_length=1)
    subject: SubjectRef
    domain: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    evidence: list[EvidenceRef] = Field(default_factory=list)
    observed_at: datetime
    applicability: TemporalApplicability
    context: list[str] = Field(default_factory=list)
    expression_origin: ExpressionOrigin
    confidence: ConfidenceAssertion
    temporal_status: TemporalStatus
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_id: str = Field(min_length=1)
    subject: SubjectRef
    domain: str = Field(min_length=1)
    source_kind: ReferenceKind
    source_id: str = Field(min_length=1)
    target_kind: ReferenceKind
    target_id: str = Field(min_length=1)
    relationship_type: str = Field(min_length=1)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    confidence: ConfidenceAssertion
    observed_at: datetime
    applicability: TemporalApplicability
    context: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReconciliationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1)
    subject: SubjectRef
    domain: str = Field(min_length=1)
    finding_kind: FindingKind
    summary: str = Field(min_length=1)
    observation_ids: list[str] = Field(default_factory=list)
    relationship_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    objective_refs: list[str] = Field(default_factory=list)
    priority_refs: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    confidence: ConfidenceAssertion
    created_at: datetime
    interpretation_version: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_traceable_basis(self) -> ReconciliationFinding:
        if not self.observation_ids and not self.relationship_ids:
            raise ValueError("a finding must reference at least one observation or relationship")
        return self


class DisclosureDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1)
    action: DisclosureAction
    reasons: list[str] = Field(default_factory=list)
    decided_at: datetime
    policy_version: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReconciliationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: SubjectRef
    domain: str = Field(min_length=1)
    observations: list[Observation] = Field(default_factory=list)
    relationships: list[RelationshipAssertion] = Field(default_factory=list)
    objective_refs: list[str] = Field(default_factory=list)
    priority_refs: list[str] = Field(default_factory=list)
    as_of: datetime


class ReconciliationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: SubjectRef
    domain: str
    findings: list[ReconciliationFinding] = Field(default_factory=list)
    unresolved_observation_ids: list[str] = Field(default_factory=list)
    interpretation_version: str
    reconciled_at: datetime
