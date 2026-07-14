"""Approval-bound generic Enki state creation built on governed transactions."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.approval_lifecycle import ApprovalGrantRepository
from nks.application.governed_transactions import (
    FailureHook,
    GovernedOperationPlan,
    GovernedOperationResult,
    GovernedTransactionExecutor,
    GovernedTransactionJournal,
    GovernedTransactionReceipt,
    GovernedTransactionReceiptRepository,
    canonical_sha256,
)
from nks.enki.contracts import (
    Observation,
    ReferenceKind,
    RelationshipAssertion,
    SubjectRef,
)
from nks.governance.approvals import ExecutionContext


class EnkiStateWriter(Protocol):
    def append_observations(self, observations: Iterable[Observation]) -> None: ...

    def append_relationships(
        self,
        relationships: Iterable[RelationshipAssertion],
    ) -> None: ...


class StateWritePayload(BaseModel):
    """Exact generic state records and known-reference boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: SubjectRef
    domain: str = Field(min_length=1)
    observations: list[Observation] = Field(default_factory=list)
    relationships: list[RelationshipAssertion] = Field(default_factory=list)
    known_observation_ids: set[str] = Field(default_factory=set)

    @model_validator(mode="after")
    def validate_records(self) -> "StateWritePayload":
        observation_ids = [item.observation_id for item in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("observation ids must be unique")

        relationship_ids = [item.relationship_id for item in self.relationships]
        if len(relationship_ids) != len(set(relationship_ids)):
            raise ValueError("relationship ids must be unique")

        for observation in self.observations:
            if observation.subject != self.subject:
                raise ValueError("observation subject does not match state-write subject")
            if observation.domain != self.domain:
                raise ValueError("observation domain does not match state-write domain")

        known_ids = self.known_observation_ids | set(observation_ids)
        for relationship in self.relationships:
            if relationship.subject != self.subject:
                raise ValueError("relationship subject does not match state-write subject")
            if relationship.domain != self.domain:
                raise ValueError("relationship domain does not match state-write domain")
            if (
                relationship.source_kind == ReferenceKind.OBSERVATION
                and relationship.source_id not in known_ids
            ):
                raise ValueError(
                    f"unknown relationship source observation: {relationship.source_id}"
                )
            if (
                relationship.target_kind == ReferenceKind.OBSERVATION
                and relationship.target_id not in known_ids
            ):
                raise ValueError(
                    f"unknown relationship target observation: {relationship.target_id}"
                )
        return self


class GovernedStateWritePlan(BaseModel):
    """Content-addressed state-write payload bound to one operation transaction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: GovernedOperationPlan
    payload: StateWritePayload

    @model_validator(mode="after")
    def validate_binding(self) -> "GovernedStateWritePlan":
        if self.operation.subject_id != self.payload.subject.subject_id:
            raise ValueError("operation subject does not match state-write subject")
        if self.operation.content_sha256 != canonical_sha256(self.payload):
            raise ValueError("operation content hash does not match state-write payload")
        return self

    @classmethod
    def create(
        cls,
        *,
        transaction_id: str,
        subject: SubjectRef,
        domain: str,
        observations: list[Observation],
        relationships: list[RelationshipAssertion],
        known_observation_ids: set[str],
        execution_context: ExecutionContext,
        acceptable_authority_classes: set[str],
        requested_at: datetime,
        metadata: dict[str, object] | None = None,
    ) -> "GovernedStateWritePlan":
        payload = StateWritePayload(
            subject=subject,
            domain=domain,
            observations=observations,
            relationships=relationships,
            known_observation_ids=known_observation_ids,
        )
        operation = GovernedOperationPlan(
            operation_id="enki-state-write",
            transaction_id=transaction_id,
            action="enki:state-write",
            subject_id=subject.subject_id,
            content_sha256=canonical_sha256(payload),
            execution_context=execution_context,
            acceptable_authority_classes=acceptable_authority_classes,
            requested_at=requested_at,
            metadata=metadata or {},
        )
        return cls(operation=operation, payload=payload)


StateWriteFailureHook = Callable[[str], None]


class StateWriteAdapter:
    """Idempotent append-only state writer with a partial-write boundary."""

    def __init__(
        self,
        writer: EnkiStateWriter,
        payload: StateWritePayload,
        *,
        failure_hook: StateWriteFailureHook | None = None,
    ) -> None:
        self._writer = writer
        self._payload = payload
        self._failure_hook = failure_hook or (lambda _boundary: None)

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        if plan.content_sha256 != canonical_sha256(self._payload):
            raise RuntimeError("state-write adapter received a mismatched operation plan")
        self._writer.append_observations(self._payload.observations)
        self._failure_hook("after-observations")
        self._writer.append_relationships(self._payload.relationships)
        return GovernedOperationResult(
            output_sha256=canonical_sha256(
                {
                    "observation_ids": [
                        item.observation_id for item in self._payload.observations
                    ],
                    "relationship_ids": [
                        item.relationship_id for item in self._payload.relationships
                    ],
                    "subject": self._payload.subject,
                    "domain": self._payload.domain,
                }
            ),
            metadata={
                "observation_count": len(self._payload.observations),
                "relationship_count": len(self._payload.relationships),
            },
        )


class ExecuteGovernedStateWrite:
    """Execute one generic state write through the shared transaction foundation."""

    def __init__(
        self,
        *,
        state_writer: EnkiStateWriter,
        approval_repository: ApprovalGrantRepository,
        journal: GovernedTransactionJournal,
        receipt_repository: GovernedTransactionReceiptRepository,
    ) -> None:
        self._state_writer = state_writer
        self._executor = GovernedTransactionExecutor(
            approval_repository=approval_repository,
            journal=journal,
            receipt_repository=receipt_repository,
        )

    def execute(
        self,
        plan: GovernedStateWritePlan,
        *,
        approval_id: str,
        now: datetime | None = None,
        transaction_failure_hook: FailureHook | None = None,
        state_write_failure_hook: StateWriteFailureHook | None = None,
    ) -> GovernedTransactionReceipt:
        adapter = StateWriteAdapter(
            self._state_writer,
            plan.payload,
            failure_hook=state_write_failure_hook,
        )
        return self._executor.execute(
            plan.operation,
            approval_id=approval_id,
            adapter=adapter,
            now=now,
            failure_hook=transaction_failure_hook,
        )
