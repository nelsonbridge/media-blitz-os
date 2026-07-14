"""Generic governed Enki transition and conflict contracts."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from enum import StrEnum
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
    TransactionTerminalState,
    canonical_sha256,
)
from nks.enki.contracts import SubjectRef
from nks.governance.approvals import ExecutionContext


class TransitionType(StrEnum):
    CORRECTION = "CORRECTION"
    REFINEMENT = "REFINEMENT"
    SUPERSESSION = "SUPERSESSION"
    RETRACTION = "RETRACTION"
    REVERSAL = "REVERSAL"
    EXPANSION = "EXPANSION"
    RESTRICTION = "RESTRICTION"
    CONFIDENCE_CHANGE = "CONFIDENCE_CHANGE"
    CONTEXT_SHIFT = "CONTEXT_SHIFT"
    MERGE = "MERGE"
    SPLIT = "SPLIT"
    DEPRECATION = "DEPRECATION"


class ConflictKind(StrEnum):
    OVERLAP = "OVERLAP"
    BRANCH = "BRANCH"
    CONTRADICTION = "CONTRADICTION"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    CYCLE = "CYCLE"
    STALE_INPUT = "STALE_INPUT"


class TransitionReconstructionStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REPAIRABLE = "REPAIRABLE"
    ROLLED_BACK = "ROLLED_BACK"
    CONFLICT = "CONFLICT"


class StateSnapshot(BaseModel):
    """Immutable state reference used as a transition endpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state_id: str = Field(min_length=1)
    subject: SubjectRef
    domain: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    observation_ids: list[str] = Field(default_factory=list)
    relationship_ids: list[str] = Field(default_factory=list)
    context: list[str] = Field(default_factory=list)
    temporal_status: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unique_references(self) -> "StateSnapshot":
        if len(self.observation_ids) != len(set(self.observation_ids)):
            raise ValueError("observation ids must be unique")
        if len(self.relationship_ids) != len(set(self.relationship_ids)):
            raise ValueError("relationship ids must be unique")
        if not self.observation_ids and not self.relationship_ids:
            raise ValueError("a state snapshot must reference canonical state")
        return self


class TransitionPayload(BaseModel):
    """Exact transition semantics independent of persistence and approval adapters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    transition_id: str = Field(min_length=1)
    transition_type: TransitionType
    subject: SubjectRef
    domain: str = Field(min_length=1)
    from_states: list[StateSnapshot] = Field(min_length=1)
    to_states: list[StateSnapshot] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    provenance_classification: str = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    interpretation_version: str = Field(min_length=1)
    required_context: set[str] = Field(default_factory=set)
    accepted_conflicts: set[ConflictKind] = Field(default_factory=set)
    occurred_at: datetime
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_transition_shape(self) -> "TransitionPayload":
        from_ids = [state.state_id for state in self.from_states]
        to_ids = [state.state_id for state in self.to_states]
        if len(from_ids) != len(set(from_ids)):
            raise ValueError("from-state ids must be unique")
        if len(to_ids) != len(set(to_ids)):
            raise ValueError("to-state ids must be unique")
        if set(from_ids) & set(to_ids):
            raise ValueError("from and to state ids must be distinct")

        for state in [*self.from_states, *self.to_states]:
            if state.subject != self.subject:
                raise ValueError("transition endpoint subject does not match")
            if state.domain != self.domain:
                raise ValueError("transition endpoint domain does not match")
            if self.required_context and not self.required_context <= set(state.context):
                raise ValueError("transition endpoint context does not satisfy required context")

        if self.transition_type in {TransitionType.RETRACTION, TransitionType.DEPRECATION}:
            if self.to_states:
                raise ValueError(f"{self.transition_type.value} cannot declare to_states")
        elif not self.to_states:
            raise ValueError(f"{self.transition_type.value} requires to_states")

        if self.transition_type == TransitionType.MERGE:
            if len(self.from_states) < 2 or len(self.to_states) != 1:
                raise ValueError("MERGE requires multiple from_states and one to_state")
        elif self.transition_type == TransitionType.SPLIT:
            if len(self.from_states) != 1 or len(self.to_states) < 2:
                raise ValueError("SPLIT requires one from_state and multiple to_states")
        elif self.transition_type not in {TransitionType.RETRACTION, TransitionType.DEPRECATION}:
            if len(self.from_states) != 1 or len(self.to_states) != 1:
                raise ValueError(
                    f"{self.transition_type.value} requires one from_state and one to_state"
                )

        unconditionally_rejected = {
            ConflictKind.CYCLE,
            ConflictKind.STALE_INPUT,
            ConflictKind.CONTRADICTION,
        }
        invalid = self.accepted_conflicts & unconditionally_rejected
        if invalid:
            names = ", ".join(sorted(item.value for item in invalid))
            raise ValueError(f"these conflicts can never be accepted: {names}")
        return self

    @property
    def before_sha256(self) -> str:
        return canonical_sha256(sorted(self.from_states, key=lambda state: state.state_id))

    @property
    def after_sha256(self) -> str:
        return canonical_sha256(sorted(self.to_states, key=lambda state: state.state_id))


class GovernedTransitionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: GovernedOperationPlan
    payload: TransitionPayload

    @model_validator(mode="after")
    def validate_binding(self) -> "GovernedTransitionPlan":
        expected_action = f"enki:transition:{self.payload.transition_type.value.lower()}"
        if self.operation.operation_id != "enki-transition":
            raise ValueError("operation is not an Enki transition")
        if self.operation.action != expected_action:
            raise ValueError("operation action does not match transition type")
        if self.operation.subject_id != self.payload.subject.subject_id:
            raise ValueError("operation subject does not match transition subject")
        if self.operation.content_sha256 != canonical_sha256(self.payload):
            raise ValueError("operation content hash does not match transition payload")
        if self.operation.acceptable_authority_classes != {self.payload.authority_class}:
            raise ValueError("operation authority does not match transition authority")
        return self

    @classmethod
    def create(
        cls,
        *,
        transaction_id: str,
        payload: TransitionPayload,
        execution_context: ExecutionContext,
    ) -> "GovernedTransitionPlan":
        operation = GovernedOperationPlan(
            operation_id="enki-transition",
            transaction_id=transaction_id,
            action=f"enki:transition:{payload.transition_type.value.lower()}",
            subject_id=payload.subject.subject_id,
            content_sha256=canonical_sha256(payload),
            execution_context=execution_context,
            acceptable_authority_classes={payload.authority_class},
            requested_at=payload.occurred_at,
            metadata={
                "transition_id": payload.transition_id,
                "transition_type": payload.transition_type.value,
                "before_sha256": payload.before_sha256,
                "after_sha256": payload.after_sha256,
                "interpretation_version": payload.interpretation_version,
            },
        )
        return cls(operation=operation, payload=payload)


class TransitionRecord(BaseModel):
    """Append-only canonical record of an executed transition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    transition_id: str = Field(min_length=1)
    transition_type: TransitionType
    subject: SubjectRef
    domain: str = Field(min_length=1)
    from_states: list[StateSnapshot]
    to_states: list[StateSnapshot] = Field(default_factory=list)
    before_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    after_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    reason: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    provenance_classification: str = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    interpretation_version: str = Field(min_length=1)
    execution_context: ExecutionContext
    transaction_id: str = Field(min_length=1)
    detected_conflicts: set[ConflictKind] = Field(default_factory=set)
    occurred_at: datetime
    metadata: dict[str, object] = Field(default_factory=dict)


class TransitionRepository(Protocol):
    def get_transition(self, transition_id: str) -> TransitionRecord | None: ...

    def list_transitions(self, subject: SubjectRef, domain: str) -> list[TransitionRecord]: ...

    def append_transition(self, transition: TransitionRecord) -> None: ...


class StateSnapshotReader(Protocol):
    def get_snapshot(self, state_id: str) -> StateSnapshot | None: ...


class TransitionConflictError(RuntimeError):
    def __init__(self, conflicts: set[ConflictKind], message: str) -> None:
        self.conflicts = conflicts
        super().__init__(message)


class TransitionGraphAnalyzer:
    """Detect stale inputs, cycles, branches, overlap, contradictions, and authority conflict."""

    def __init__(
        self,
        *,
        transition_repository: TransitionRepository,
        state_reader: StateSnapshotReader,
    ) -> None:
        self._transitions = transition_repository
        self._states = state_reader

    @staticmethod
    def _edges(records: list[TransitionRecord]) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = defaultdict(set)
        for record in records:
            for source in record.from_states:
                for target in record.to_states:
                    graph[source.state_id].add(target.state_id)
        return graph

    @staticmethod
    def _reachable(graph: dict[str, set[str]], start: str, target: str) -> bool:
        queue: deque[str] = deque([start])
        visited: set[str] = set()
        while queue:
            node = queue.popleft()
            if node == target:
                return True
            if node in visited:
                continue
            visited.add(node)
            queue.extend(graph.get(node, set()) - visited)
        return False

    def analyze(self, payload: TransitionPayload) -> set[ConflictKind]:
        existing = self._transitions.list_transitions(payload.subject, payload.domain)
        conflicts: set[ConflictKind] = set()

        for source in payload.from_states:
            current = self._states.get_snapshot(source.state_id)
            if current is None:
                raise ValueError(f"unknown from-state: {source.state_id}")
            if current.content_sha256 != source.content_sha256:
                conflicts.add(ConflictKind.STALE_INPUT)

        for target in payload.to_states:
            current = self._states.get_snapshot(target.state_id)
            if current is not None and current.content_sha256 != target.content_sha256:
                conflicts.add(ConflictKind.CONTRADICTION)

        outgoing: dict[str, list[TransitionRecord]] = defaultdict(list)
        for record in existing:
            for source in record.from_states:
                outgoing[source.state_id].append(record)

        for source in payload.from_states:
            prior = outgoing.get(source.state_id, [])
            if not prior:
                continue
            exact_output = any(
                record.after_sha256 == payload.after_sha256
                and record.before_sha256 == payload.before_sha256
                for record in prior
            )
            conflicts.add(ConflictKind.OVERLAP if exact_output else ConflictKind.BRANCH)
            if any(record.authority_class != payload.authority_class for record in prior):
                conflicts.add(ConflictKind.AUTHORITY_CONFLICT)

        graph = self._edges(existing)
        for source in payload.from_states:
            for target in payload.to_states:
                if source.state_id == target.state_id or self._reachable(
                    graph, target.state_id, source.state_id
                ):
                    conflicts.add(ConflictKind.CYCLE)
                graph[source.state_id].add(target.state_id)

        rejected = conflicts - payload.accepted_conflicts
        rejected.update(
            conflicts
            & {
                ConflictKind.CYCLE,
                ConflictKind.STALE_INPUT,
                ConflictKind.CONTRADICTION,
            }
        )
        if rejected:
            names = ", ".join(sorted(item.value for item in rejected))
            raise TransitionConflictError(
                rejected,
                f"transition conflicts are not accepted: {names}",
            )
        return conflicts


class TransitionAdapter:
    def __init__(
        self,
        *,
        repository: TransitionRepository,
        record: TransitionRecord,
    ) -> None:
        self._repository = repository
        self._record = record

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        if plan.transaction_id != self._record.transaction_id:
            raise RuntimeError("transition adapter received a mismatched transaction")
        self._repository.append_transition(self._record)
        return GovernedOperationResult(
            output_sha256=canonical_sha256(self._record),
            metadata={
                "transition_id": self._record.transition_id,
                "before_sha256": self._record.before_sha256,
                "after_sha256": self._record.after_sha256,
                "detected_conflicts": sorted(
                    conflict.value for conflict in self._record.detected_conflicts
                ),
            },
        )


class GovernedTransitionOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transition: TransitionRecord
    transaction_receipt: GovernedTransactionReceipt


class ExecuteGovernedTransition:
    def __init__(
        self,
        *,
        transition_repository: TransitionRepository,
        state_reader: StateSnapshotReader,
        approval_repository: ApprovalGrantRepository,
        journal: GovernedTransactionJournal,
        receipt_repository: GovernedTransactionReceiptRepository,
    ) -> None:
        self._transition_repository = transition_repository
        self._analyzer = TransitionGraphAnalyzer(
            transition_repository=transition_repository,
            state_reader=state_reader,
        )
        self._executor = GovernedTransactionExecutor(
            approval_repository=approval_repository,
            journal=journal,
            receipt_repository=receipt_repository,
        )

    def execute(
        self,
        plan: GovernedTransitionPlan,
        *,
        approval_id: str,
        now: datetime | None = None,
        failure_hook: FailureHook | None = None,
    ) -> GovernedTransitionOutcome:
        existing = self._transition_repository.get_transition(
            plan.payload.transition_id
        )
        if existing is not None:
            if existing.transaction_id != plan.operation.transaction_id:
                raise RuntimeError("transition id belongs to a different transaction")
            conflicts = existing.detected_conflicts
            record = existing
        else:
            conflicts = self._analyzer.analyze(plan.payload)
            record = TransitionRecord(
                transition_id=plan.payload.transition_id,
                transition_type=plan.payload.transition_type,
                subject=plan.payload.subject,
                domain=plan.payload.domain,
                from_states=plan.payload.from_states,
                to_states=plan.payload.to_states,
                before_sha256=plan.payload.before_sha256,
                after_sha256=plan.payload.after_sha256,
                reason=plan.payload.reason,
                evidence_ids=plan.payload.evidence_ids,
                provenance_classification=plan.payload.provenance_classification,
                authority_class=plan.payload.authority_class,
                interpretation_version=plan.payload.interpretation_version,
                execution_context=plan.operation.execution_context,
                transaction_id=plan.operation.transaction_id,
                detected_conflicts=conflicts,
                occurred_at=plan.payload.occurred_at,
                metadata=plan.payload.metadata,
            )
        receipt = self._executor.execute(
            plan.operation,
            approval_id=approval_id,
            adapter=TransitionAdapter(
                repository=self._transition_repository,
                record=record,
            ),
            now=now,
            failure_hook=failure_hook,
        )
        return GovernedTransitionOutcome(
            transition=record,
            transaction_receipt=receipt,
        )


class TransitionReconstruction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: TransitionReconstructionStatus
    transition_id: str
    issues: list[str] = Field(default_factory=list)


def reconstruct_transition(
    plan: GovernedTransitionPlan,
    *,
    record: TransitionRecord | None,
    receipt: GovernedTransactionReceipt | None,
) -> TransitionReconstruction:
    issues: list[str] = []
    if receipt is not None and receipt.terminal_state == TransactionTerminalState.ROLLED_BACK:
        return TransitionReconstruction(
            status=TransitionReconstructionStatus.ROLLED_BACK,
            transition_id=plan.payload.transition_id,
        )
    if record is None and receipt is None:
        return TransitionReconstruction(
            status=TransitionReconstructionStatus.INCOMPLETE,
            transition_id=plan.payload.transition_id,
            issues=["transition record and transaction receipt are absent"],
        )
    if record is not None:
        if record.transaction_id != plan.operation.transaction_id:
            issues.append("transition transaction does not match plan")
        if record.before_sha256 != plan.payload.before_sha256:
            issues.append("before-state hash does not match plan")
        if record.after_sha256 != plan.payload.after_sha256:
            issues.append("after-state hash does not match plan")
        if (
            receipt is not None
            and canonical_sha256(record) != receipt.output_sha256
        ):
            issues.append("transition record hash does not match transaction receipt")
    if receipt is not None:
        if receipt.plan_sha256 != plan.operation.plan_sha256:
            issues.append("transaction receipt plan hash does not match")
        if receipt.transaction_id != plan.operation.transaction_id:
            issues.append("transaction receipt transaction does not match")
    if issues:
        return TransitionReconstruction(
            status=TransitionReconstructionStatus.CONFLICT,
            transition_id=plan.payload.transition_id,
            issues=issues,
        )
    if record is not None and receipt is None:
        return TransitionReconstruction(
            status=TransitionReconstructionStatus.REPAIRABLE,
            transition_id=plan.payload.transition_id,
            issues=["transition record exists without terminal transaction receipt"],
        )
    if record is None and receipt is not None:
        return TransitionReconstruction(
            status=TransitionReconstructionStatus.CONFLICT,
            transition_id=plan.payload.transition_id,
            issues=["transaction receipt exists without transition record"],
        )
    return TransitionReconstruction(
        status=TransitionReconstructionStatus.COMPLETE,
        transition_id=plan.payload.transition_id,
    )
