"""Reusable governed transaction execution with fail-closed recovery semantics."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.approval_lifecycle import (
    ApprovalGrantRepository,
    ConsumeApproval,
    ReleaseApprovalReservation,
    ReserveApproval,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalRequest,
    ExecutionContext,
)


class TransactionStage(StrEnum):
    PLANNED = "PLANNED"
    APPROVAL_RESERVED = "APPROVAL_RESERVED"
    RECOVERY_STARTED = "RECOVERY_STARTED"
    APPROVAL_CONSUMED = "APPROVAL_CONSUMED"
    EFFECT_APPLIED = "EFFECT_APPLIED"
    RECEIPT_PERSISTED = "RECEIPT_PERSISTED"
    RESERVATION_RELEASED = "RESERVATION_RELEASED"
    COMMITTED = "COMMITTED"
    RECOVERED = "RECOVERED"
    ROLLED_BACK = "ROLLED_BACK"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    FAILED = "FAILED"


class TransactionTerminalState(StrEnum):
    COMMITTED = "COMMITTED"
    RECOVERED = "RECOVERED"
    ROLLED_BACK = "ROLLED_BACK"


class RecoveryStrategy(StrEnum):
    NONE = "NONE"
    RELEASE_RESERVATION = "RELEASE_RESERVATION"
    EXACT_RETRY = "EXACT_RETRY"


def _canonicalize(value: object) -> object:
    if isinstance(value, BaseModel):
        return _canonicalize(value.model_dump(mode="python", exclude_none=False))
    if isinstance(value, dict):
        return {str(key): _canonicalize(item) for key, item in sorted(value.items())}
    if isinstance(value, (set, frozenset)):
        return [_canonicalize(item) for item in sorted(value, key=str)]
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    return value


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        _canonicalize(value),
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class GovernedOperationPlan(BaseModel):
    """Exact immutable input to one governed operation transaction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext
    acceptable_authority_classes: set[str] = Field(min_length=1)
    requested_at: datetime
    metadata: dict[str, object] = Field(default_factory=dict)

    @property
    def plan_sha256(self) -> str:
        return canonical_sha256(self)


class GovernedOperationResult(BaseModel):
    """Deterministic result returned by an idempotent operation adapter."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    output_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    metadata: dict[str, object] = Field(default_factory=dict)


class GovernedTransactionEvent(BaseModel):
    """Append-only journal event for one exact transaction boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    plan_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    stage: TransactionStage
    occurred_at: datetime
    payload: dict[str, object] = Field(default_factory=dict)


class GovernedTransactionReceipt(BaseModel):
    """Immutable terminal receipt for a governed operation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    plan_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    approval_id: str = Field(min_length=1)
    execution_context: ExecutionContext
    terminal_state: TransactionTerminalState
    recovery_strategy: RecoveryStrategy
    output_sha256: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    recorded_at: datetime
    exact_retry: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_terminal_state(self) -> "GovernedTransactionReceipt":
        if self.terminal_state in {
            TransactionTerminalState.COMMITTED,
            TransactionTerminalState.RECOVERED,
        } and self.output_sha256 is None:
            raise ValueError("committed or recovered receipts require output_sha256")
        if (
            self.terminal_state == TransactionTerminalState.ROLLED_BACK
            and self.output_sha256 is not None
        ):
            raise ValueError("rolled-back receipts cannot claim an output")
        return self


class GovernedOperationAdapter(Protocol):
    """Idempotent effect adapter used by the transaction executor."""

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult: ...


class GovernedTransactionJournal(Protocol):
    def append_event(self, event: GovernedTransactionEvent) -> None: ...

    def list_events(self, transaction_id: str) -> list[GovernedTransactionEvent]: ...


class GovernedTransactionReceiptRepository(Protocol):
    def get_receipt(self, transaction_id: str) -> GovernedTransactionReceipt | None: ...

    def append_receipt(self, receipt: GovernedTransactionReceipt) -> None: ...


FailureHook = Callable[[TransactionStage], None]


class GovernedTransactionExecutor:
    """Execute one exact operation with rollback or exact-retry recovery."""

    def __init__(
        self,
        *,
        approval_repository: ApprovalGrantRepository,
        journal: GovernedTransactionJournal,
        receipt_repository: GovernedTransactionReceiptRepository,
    ) -> None:
        self._approval_repository = approval_repository
        self._reserve = ReserveApproval(approval_repository)
        self._consume = ConsumeApproval(approval_repository)
        self._release = ReleaseApprovalReservation(approval_repository)
        self._journal_repository = journal
        self._receipt_repository = receipt_repository

    def _record(
        self,
        plan: GovernedOperationPlan,
        stage: TransactionStage,
        *,
        payload: dict[str, object] | None = None,
    ) -> None:
        sequence = len(self._journal_repository.list_events(plan.transaction_id)) + 1
        event = GovernedTransactionEvent(
            event_id=f"{plan.transaction_id}:{sequence:04d}",
            transaction_id=plan.transaction_id,
            operation_id=plan.operation_id,
            plan_sha256=plan.plan_sha256,
            stage=stage,
            occurred_at=plan.requested_at,
            payload=payload or {},
        )
        self._journal_repository.append_event(event)

    @staticmethod
    def _approval_request(plan: GovernedOperationPlan) -> ApprovalRequest:
        return ApprovalRequest(
            execution_context=plan.execution_context,
            action=plan.action,
            subject_id=plan.subject_id,
            content_sha256=plan.content_sha256,
            acceptable_authority_classes=plan.acceptable_authority_classes,
            transaction_id=plan.transaction_id,
            requested_at=plan.requested_at,
        )

    def execute(
        self,
        plan: GovernedOperationPlan,
        *,
        approval_id: str,
        adapter: GovernedOperationAdapter,
        now: datetime | None = None,
        failure_hook: FailureHook | None = None,
    ) -> GovernedTransactionReceipt:
        existing = self._receipt_repository.get_receipt(plan.transaction_id)
        if existing is not None:
            if existing.plan_sha256 != plan.plan_sha256:
                raise RuntimeError("transaction receipt belongs to a different plan")
            if existing.approval_id != approval_id:
                raise RuntimeError("transaction receipt belongs to a different approval")
            return existing.model_copy(update={"exact_retry": True})

        request = self._approval_request(plan)
        hook = failure_hook or (lambda _stage: None)
        self._record(plan, TransactionStage.PLANNED)

        reserved = self._reserve.execute(approval_id, request, now=now)
        already_consumed = (
            reserved.consumption_status == ApprovalConsumptionStatus.CONSUMED
        )
        recovery_stage = (
            TransactionStage.RECOVERY_STARTED
            if already_consumed
            else TransactionStage.APPROVAL_RESERVED
        )
        self._record(plan, recovery_stage)

        try:
            hook(recovery_stage)

            self._consume.execute(approval_id, request, now=now)
            self._record(plan, TransactionStage.APPROVAL_CONSUMED)
            hook(TransactionStage.APPROVAL_CONSUMED)

            result = adapter.apply(plan)
            self._record(
                plan,
                TransactionStage.EFFECT_APPLIED,
                payload={"output_sha256": result.output_sha256},
            )
            hook(TransactionStage.EFFECT_APPLIED)

            terminal_state = (
                TransactionTerminalState.RECOVERED
                if already_consumed
                else TransactionTerminalState.COMMITTED
            )
            receipt = GovernedTransactionReceipt(
                receipt_id=f"GTR-{plan.transaction_id}",
                operation_id=plan.operation_id,
                transaction_id=plan.transaction_id,
                plan_sha256=plan.plan_sha256,
                approval_id=approval_id,
                execution_context=plan.execution_context,
                terminal_state=terminal_state,
                recovery_strategy=(
                    RecoveryStrategy.EXACT_RETRY
                    if already_consumed
                    else RecoveryStrategy.NONE
                ),
                output_sha256=result.output_sha256,
                recorded_at=plan.requested_at,
                exact_retry=already_consumed,
                metadata=result.metadata,
            )
            self._receipt_repository.append_receipt(receipt)
            self._record(plan, TransactionStage.RECEIPT_PERSISTED)
            hook(TransactionStage.RECEIPT_PERSISTED)
            self._record(
                plan,
                TransactionStage.RECOVERED
                if already_consumed
                else TransactionStage.COMMITTED,
            )
            return receipt
        except Exception as exc:
            current = self._approval_repository.get_approval(approval_id)
            if (
                current is not None
                and current.consumption_status == ApprovalConsumptionStatus.RESERVED
                and current.reserved_by_transaction_id == plan.transaction_id
            ):
                self._release.execute(approval_id, plan.transaction_id)
                self._record(plan, TransactionStage.RESERVATION_RELEASED)
                rollback_receipt = GovernedTransactionReceipt(
                    receipt_id=f"GTR-{plan.transaction_id}",
                    operation_id=plan.operation_id,
                    transaction_id=plan.transaction_id,
                    plan_sha256=plan.plan_sha256,
                    approval_id=approval_id,
                    execution_context=plan.execution_context,
                    terminal_state=TransactionTerminalState.ROLLED_BACK,
                    recovery_strategy=RecoveryStrategy.RELEASE_RESERVATION,
                    output_sha256=None,
                    recorded_at=plan.requested_at,
                    metadata={"failure_type": type(exc).__name__},
                )
                self._receipt_repository.append_receipt(rollback_receipt)
                self._record(plan, TransactionStage.ROLLED_BACK)
            elif (
                current is not None
                and current.consumption_status == ApprovalConsumptionStatus.CONSUMED
                and current.consumed_by_transaction_id == plan.transaction_id
            ):
                self._record(
                    plan,
                    TransactionStage.RECOVERY_REQUIRED,
                    payload={
                        "failure_type": type(exc).__name__,
                        "recovery_strategy": RecoveryStrategy.EXACT_RETRY.value,
                    },
                )
            else:
                self._record(
                    plan,
                    TransactionStage.FAILED,
                    payload={"failure_type": type(exc).__name__},
                )
            raise
