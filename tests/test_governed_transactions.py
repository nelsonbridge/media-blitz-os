from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from nks.adapters.governed_transactions import (
    GovernedTransactionRecordConflictError,
    JsonGovernedTransactionRepository,
)
from nks.application.governed_transactions import (
    GovernedOperationPlan,
    GovernedOperationResult,
    GovernedTransactionEvent,
    GovernedTransactionExecutor,
    GovernedTransactionReceipt,
    RecoveryStrategy,
    TransactionStage,
    TransactionTerminalState,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 6, 0, tzinfo=timezone.utc)


def _plan(
    *,
    transaction_id: str = "TX-1",
    context: ExecutionContext = ExecutionContext.TEST,
    content: str = "input",
) -> GovernedOperationPlan:
    return GovernedOperationPlan(
        operation_id="state-write",
        transaction_id=transaction_id,
        action="enki:state-write",
        subject_id="SUBJECT-1",
        content_sha256=_hash(content),
        execution_context=context,
        acceptable_authority_classes={"SUBJECT"},
        requested_at=_now(),
        metadata={"fixture": "test"},
    )


def _grant(
    plan: GovernedOperationPlan,
    *,
    context: ExecutionContext | None = None,
) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id="APR-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=context or plan.execution_context,
        permitted_actions={plan.action},
        subject_id=plan.subject_id,
        content_sha256=plan.content_sha256,
        authorized_by=plan.subject_id,
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=5),
        expires_at=_now() + timedelta(hours=1),
    )


class MemoryApprovalRepository:
    def __init__(self, grant: ApprovalGrant) -> None:
        self.current = grant

    def get_approval(self, approval_id: str) -> ApprovalGrant | None:
        return self.current if self.current.approval_id == approval_id else None

    def compare_and_swap_approval(
        self,
        expected: ApprovalGrant,
        replacement: ApprovalGrant,
    ) -> bool:
        if self.current != expected:
            return False
        self.current = replacement
        return True


class MemoryJournal:
    def __init__(self) -> None:
        self.events: list[GovernedTransactionEvent] = []

    def append_event(self, event: GovernedTransactionEvent) -> None:
        if any(item.event_id == event.event_id and item != event for item in self.events):
            raise RuntimeError("event conflict")
        if event not in self.events:
            self.events.append(event)

    def list_events(self, transaction_id: str) -> list[GovernedTransactionEvent]:
        return [
            event for event in self.events if event.transaction_id == transaction_id
        ]


class MemoryReceiptRepository:
    def __init__(self) -> None:
        self.receipt: GovernedTransactionReceipt | None = None

    def get_receipt(
        self,
        transaction_id: str,
    ) -> GovernedTransactionReceipt | None:
        if self.receipt is None or self.receipt.transaction_id != transaction_id:
            return None
        return self.receipt

    def append_receipt(self, receipt: GovernedTransactionReceipt) -> None:
        if self.receipt is not None and self.receipt != receipt:
            raise RuntimeError("receipt conflict")
        self.receipt = receipt


class IdempotentAdapter:
    def __init__(self) -> None:
        self.effects: dict[str, GovernedOperationResult] = {}

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        return self.effects.setdefault(
            plan.transaction_id,
            GovernedOperationResult(
                output_sha256=_hash(f"output:{plan.transaction_id}"),
                metadata={"adapter": "idempotent"},
            ),
        )


def _executor(
    plan: GovernedOperationPlan,
) -> tuple[
    GovernedTransactionExecutor,
    MemoryApprovalRepository,
    MemoryJournal,
    MemoryReceiptRepository,
]:
    approvals = MemoryApprovalRepository(_grant(plan))
    journal = MemoryJournal()
    receipts = MemoryReceiptRepository()
    return (
        GovernedTransactionExecutor(
            approval_repository=approvals,
            journal=journal,
            receipt_repository=receipts,
        ),
        approvals,
        journal,
        receipts,
    )


def test_successful_transaction_consumes_authority_and_commits() -> None:
    plan = _plan()
    executor, approvals, journal, _ = _executor(plan)
    adapter = IdempotentAdapter()

    receipt = executor.execute(plan, approval_id="APR-1", adapter=adapter, now=_now())

    assert receipt.terminal_state == TransactionTerminalState.COMMITTED
    assert receipt.recovery_strategy == RecoveryStrategy.NONE
    assert approvals.current.consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert [event.stage for event in journal.events] == [
        TransactionStage.PLANNED,
        TransactionStage.APPROVAL_RESERVED,
        TransactionStage.APPROVAL_CONSUMED,
        TransactionStage.EFFECT_APPLIED,
        TransactionStage.RECEIPT_PERSISTED,
        TransactionStage.COMMITTED,
    ]


def test_failure_after_reservation_releases_authority_and_receipts_rollback() -> None:
    plan = _plan()
    executor, approvals, journal, receipts = _executor(plan)

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.APPROVAL_RESERVED:
            raise OSError("injected")

    with pytest.raises(OSError, match="injected"):
        executor.execute(
            plan,
            approval_id="APR-1",
            adapter=IdempotentAdapter(),
            now=_now(),
            failure_hook=fail,
        )

    assert approvals.current.consumption_status == ApprovalConsumptionStatus.AVAILABLE
    assert receipts.receipt is not None
    assert receipts.receipt.terminal_state == TransactionTerminalState.ROLLED_BACK
    assert receipts.receipt.recovery_strategy == RecoveryStrategy.RELEASE_RESERVATION
    assert TransactionStage.RESERVATION_RELEASED in {
        event.stage for event in journal.events
    }
    assert TransactionStage.ROLLED_BACK in {event.stage for event in journal.events}


def test_failure_after_consumption_recovers_without_duplicate_effect() -> None:
    plan = _plan()
    executor, approvals, journal, receipts = _executor(plan)
    adapter = IdempotentAdapter()

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.EFFECT_APPLIED:
            raise OSError("receipt boundary failure")

    with pytest.raises(OSError, match="receipt boundary failure"):
        executor.execute(
            plan,
            approval_id="APR-1",
            adapter=adapter,
            now=_now(),
            failure_hook=fail,
        )

    assert approvals.current.consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert receipts.receipt is None
    assert TransactionStage.RECOVERY_REQUIRED in {
        event.stage for event in journal.events
    }

    recovered = executor.execute(
        plan,
        approval_id="APR-1",
        adapter=adapter,
        now=_now(),
    )

    assert recovered.terminal_state == TransactionTerminalState.RECOVERED
    assert recovered.recovery_strategy == RecoveryStrategy.EXACT_RETRY
    assert recovered.exact_retry is True
    assert len(adapter.effects) == 1
    assert TransactionStage.RECOVERY_STARTED in {
        event.stage for event in journal.events
    }
    assert TransactionStage.RECOVERED in {event.stage for event in journal.events}


def test_exact_retry_after_terminal_receipt_does_not_reapply_effect() -> None:
    plan = _plan()
    executor, _, _, _ = _executor(plan)
    adapter = IdempotentAdapter()

    first = executor.execute(plan, approval_id="APR-1", adapter=adapter, now=_now())
    second = executor.execute(plan, approval_id="APR-1", adapter=adapter, now=_now())

    assert first.output_sha256 == second.output_sha256
    assert second.exact_retry is True
    assert len(adapter.effects) == 1


def test_test_request_cannot_consume_production_authority() -> None:
    plan = _plan(context=ExecutionContext.TEST)
    approvals = MemoryApprovalRepository(
        _grant(plan, context=ExecutionContext.PRODUCTION)
    )
    journal = MemoryJournal()
    receipts = MemoryReceiptRepository()
    executor = GovernedTransactionExecutor(
        approval_repository=approvals,
        journal=journal,
        receipt_repository=receipts,
    )

    with pytest.raises(PermissionError, match="execution context does not match"):
        executor.execute(
            plan,
            approval_id="APR-1",
            adapter=IdempotentAdapter(),
            now=_now(),
        )

    assert approvals.current.consumption_status == ApprovalConsumptionStatus.AVAILABLE
    assert receipts.receipt is None
    assert [event.stage for event in journal.events] == [TransactionStage.PLANNED]


def test_terminal_receipt_rejects_cross_plan_replay() -> None:
    plan = _plan()
    executor, _, _, _ = _executor(plan)
    executor.execute(plan, approval_id="APR-1", adapter=IdempotentAdapter(), now=_now())

    conflicting = _plan(content="other")
    with pytest.raises(RuntimeError, match="different plan"):
        executor.execute(
            conflicting,
            approval_id="APR-1",
            adapter=IdempotentAdapter(),
            now=_now(),
        )


def test_json_repository_is_append_only_and_reconstructs_records(tmp_path) -> None:
    repository = JsonGovernedTransactionRepository(tmp_path)
    plan = _plan()
    event = GovernedTransactionEvent(
        event_id="TX-1:0001",
        transaction_id=plan.transaction_id,
        operation_id=plan.operation_id,
        plan_sha256=plan.plan_sha256,
        stage=TransactionStage.PLANNED,
        occurred_at=plan.requested_at,
    )
    receipt = GovernedTransactionReceipt(
        receipt_id="GTR-TX-1",
        operation_id=plan.operation_id,
        transaction_id=plan.transaction_id,
        plan_sha256=plan.plan_sha256,
        approval_id="APR-1",
        execution_context=ExecutionContext.TEST,
        terminal_state=TransactionTerminalState.COMMITTED,
        recovery_strategy=RecoveryStrategy.NONE,
        output_sha256=_hash("output"),
        recorded_at=plan.requested_at,
    )

    repository.append_event(event)
    repository.append_event(event)
    repository.append_receipt(receipt)
    repository.append_receipt(receipt)

    assert repository.list_events(plan.transaction_id) == [event]
    assert repository.get_receipt(plan.transaction_id) == receipt

    changed = event.model_copy(update={"stage": TransactionStage.FAILED})
    with pytest.raises(GovernedTransactionRecordConflictError):
        repository.append_event(changed)

    changed_receipt = receipt.model_copy(
        update={"output_sha256": _hash("different")}
    )
    with pytest.raises(GovernedTransactionRecordConflictError):
        repository.append_receipt(changed_receipt)


def test_receipt_contract_rejects_false_terminal_claims() -> None:
    plan = _plan()
    with pytest.raises(ValueError, match="require output_sha256"):
        GovernedTransactionReceipt(
            receipt_id="GTR-TX-1",
            operation_id=plan.operation_id,
            transaction_id=plan.transaction_id,
            plan_sha256=plan.plan_sha256,
            approval_id="APR-1",
            execution_context=ExecutionContext.TEST,
            terminal_state=TransactionTerminalState.COMMITTED,
            recovery_strategy=RecoveryStrategy.NONE,
            recorded_at=plan.requested_at,
        )

    with pytest.raises(ValueError, match="cannot claim an output"):
        GovernedTransactionReceipt(
            receipt_id="GTR-TX-1",
            operation_id=plan.operation_id,
            transaction_id=plan.transaction_id,
            plan_sha256=plan.plan_sha256,
            approval_id="APR-1",
            execution_context=ExecutionContext.TEST,
            terminal_state=TransactionTerminalState.ROLLED_BACK,
            recovery_strategy=RecoveryStrategy.RELEASE_RESERVATION,
            output_sha256=_hash("impossible"),
            recorded_at=plan.requested_at,
        )
