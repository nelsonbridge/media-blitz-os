"""Platform-neutral domain models for the Nelson Knowledge System."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RecordStatus(StrEnum):
    PLANNED = "planned"
    DRAFTED = "drafted"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    BLOCKED = "blocked"


class GateStatus(StrEnum):
    NEEDED = "needed"
    PARTIAL = "partial"
    READY = "ready"
    APPROVED = "approved"
    WAIVED = "waived"


class CanonicalRecord(BaseModel):
    """Base record using platform-neutral identifiers and metadata."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: RecordStatus = RecordStatus.PLANNED
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceRecord(CanonicalRecord):
    source_type: str
    source_location: str
    limitations: list[str] = Field(default_factory=list)


class ArtifactRecord(CanonicalRecord):
    source_ids: list[str] = Field(min_length=1)
    proof_status: GateStatus = GateStatus.NEEDED
    narrative_status: GateStatus = GateStatus.NEEDED
    visual_status: GateStatus = GateStatus.NEEDED


class ProofRecord(CanonicalRecord):
    artifact_id: str
    category: str
    supported_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    citations_required: bool = False
    gate_status: GateStatus = GateStatus.NEEDED


class NarrativeRecord(CanonicalRecord):
    artifact_id: str
    recognition: str
    reframe: str
    framework: str
    proof: str
    application: str
    consequence: str
    invitation: str
    gate_status: GateStatus = GateStatus.NEEDED


class VisualPackageRecord(CanonicalRecord):
    artifact_id: str
    publication_id: str
    signature_diagram_id: str | None = None
    hero_image_id: str | None = None
    asset_ids: list[str] = Field(default_factory=list)
    gate_status: GateStatus = GateStatus.NEEDED


class PublicationRecord(CanonicalRecord):
    artifact_id: str
    proof_id: str
    narrative_id: str
    visual_package_id: str
    draft_path: str
    editorial_status: GateStatus = GateStatus.NEEDED
    user_approval: GateStatus = GateStatus.NEEDED


class WorkflowEvent(BaseModel):
    """Append-only event with enduring capability and transient implementation attribution."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: str
    subject_id: str
    actor_capability: str | None = None
    actor_implementation: str | None = None
    authority_source: str | None = None
    legacy_actor: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
