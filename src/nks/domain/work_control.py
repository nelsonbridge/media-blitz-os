"""Canonical backlog and sprint control-plane models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorkStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    SUPERSEDED = "superseded"


class EvidenceKind(StrEnum):
    COMMIT = "commit"
    PULL_REQUEST = "pull-request"
    TEST_RUN = "test-run"
    GENERATED_REPORT = "generated-report"
    RECEIPT = "receipt"
    HUMAN_DECISION = "human-decision"
    CANONICAL_RECORD = "canonical-record"


class WorkEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    kind: EvidenceKind
    reference: str = Field(min_length=1)
    description: str = Field(min_length=1)


class BacklogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_item_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: WorkStatus
    sprint_id: str | None = None
    acceptance_criteria: list[str] = Field(min_length=1)
    evidence: list[WorkEvidence] = Field(default_factory=list)
    blocked_reason: str | None = None
    superseded_by: str | None = None
    updated_at: datetime

    @model_validator(mode="after")
    def validate_status_contract(self) -> BacklogItem:
        if self.status == WorkStatus.COMPLETE and not self.evidence:
            raise ValueError("complete work items require implementation evidence")
        if self.status == WorkStatus.BLOCKED and not self.blocked_reason:
            raise ValueError("blocked work items require blocked_reason")
        if self.status == WorkStatus.SUPERSEDED and not self.superseded_by:
            raise ValueError("superseded work items require superseded_by")
        return self


class SprintRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sprint_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    status: WorkStatus
    work_item_ids: list[str] = Field(min_length=1)
    exit_criteria: list[str] = Field(min_length=1)
    evidence: list[WorkEvidence] = Field(default_factory=list)
    blocked_reason: str | None = None
    updated_at: datetime

    @model_validator(mode="after")
    def validate_status_contract(self) -> SprintRecord:
        if self.status == WorkStatus.COMPLETE and not self.evidence:
            raise ValueError("complete sprints require completion evidence")
        if self.status == WorkStatus.BLOCKED and not self.blocked_reason:
            raise ValueError("blocked sprints require blocked_reason")
        return self
