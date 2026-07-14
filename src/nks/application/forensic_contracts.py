"""Shared immutable contracts for Enki forensic reconstruction."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext


class ReconstructionStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REPAIRABLE = "REPAIRABLE"
    ROLLED_BACK = "ROLLED_BACK"
    CONFLICT = "CONFLICT"


class ForensicRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    record_type: str = Field(min_length=1)
    operation_family: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    execution_context: ExecutionContext
    authority_class: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    lineage_ids: list[str] = Field(default_factory=list)
    payload: dict[str, object]
    recorded_at: datetime

    @classmethod
    def create(
        cls,
        *,
        record_id: str,
        record_type: str,
        operation_family: str,
        operation_id: str,
        transaction_id: str,
        execution_context: ExecutionContext,
        authority_class: str,
        payload: dict[str, object],
        recorded_at: datetime,
        lineage_ids: list[str] | None = None,
    ) -> "ForensicRecord":
        return cls(
            record_id=record_id,
            record_type=record_type,
            operation_family=operation_family,
            operation_id=operation_id,
            transaction_id=transaction_id,
            execution_context=execution_context,
            authority_class=authority_class,
            content_sha256=canonical_sha256(payload),
            lineage_ids=lineage_ids or [],
            payload=payload,
            recorded_at=recorded_at,
        )


class ReconstructionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_family: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    execution_context: ExecutionContext
    required_record_types: set[str] = Field(min_length=1)
    repairable_record_types: set[str] = Field(default_factory=set)
    acceptable_authority_classes: set[str] = Field(min_length=1)
    expected_plan_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    expected_output_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")


class ReconstructionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_family: str
    operation_id: str
    transaction_id: str
    status: ReconstructionStatus
    evidence_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    record_ids: list[str] = Field(default_factory=list)
    missing_record_types: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    repair_actions: list[str] = Field(default_factory=list)
    terminal_state: str | None = None
    output_sha256: str | None = None


class ForensicEvidenceStore(Protocol):
    capabilities: frozenset[str]

    def append(self, record: ForensicRecord) -> None: ...
    def get(self, record_id: str) -> ForensicRecord | None: ...
    def list_records(self) -> list[ForensicRecord]: ...
    def delete(self, record_id: str) -> None: ...
    def replace(self, record: ForensicRecord) -> None: ...


def evidence_hash(records: list[ForensicRecord]) -> str:
    return canonical_sha256([
        record.model_dump(mode="python")
        for record in sorted(records, key=lambda item: item.record_id)
    ])
