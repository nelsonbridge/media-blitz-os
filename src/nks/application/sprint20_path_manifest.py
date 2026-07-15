"""Machine-readable path matrix for Sprint 20 concurrency and recovery."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(
    path_id: str,
    *,
    terminal: TransactionTerminalState,
    state_changing: bool,
    recovery: RecoveryStrategy = RecoveryStrategy.NONE,
) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=state_changing,
        recovery_strategy=recovery,
        prohibited_effects=["production-effect", "split-authority", "duplicate-effect"],
    )


def sprint20_concurrency_path_manifest() -> OperationPathManifest:
    committed = TransactionTerminalState.COMMITTED
    rolled_back = TransactionTerminalState.ROLLED_BACK
    recovered = TransactionTerminalState.RECOVERED
    return OperationPathManifest(
        operation_family="enki-concurrency-recovery",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("exclusive-lease-acquired", terminal=committed, state_changing=True),
            _path("concurrent-cas-one-winner", terminal=committed, state_changing=True),
            _path("competing-cas-conflict", terminal=rolled_back, state_changing=False),
            _path("split-authority-denied", terminal=rolled_back, state_changing=False),
            _path("stale-lease-denied", terminal=rolled_back, state_changing=False),
            _path("exact-duplicate-no-effect", terminal=committed, state_changing=False),
            _path("delivery-id-conflict", terminal=rolled_back, state_changing=False),
            _path("intent-id-conflict", terminal=rolled_back, state_changing=False),
            _path("partition-delivery-deferred", terminal=committed, state_changing=False),
            _path("out-of-order-delivery-reordered", terminal=committed, state_changing=True),
            _path("partition-healed", terminal=committed, state_changing=True),
            _path("partition-contention-receipted", terminal=rolled_back, state_changing=False),
            _path(
                "interrupted-after-effect-recovered",
                terminal=recovered,
                state_changing=True,
                recovery=RecoveryStrategy.EXACT_RETRY,
            ),
            _path("lost-receipt-detected", terminal=rolled_back, state_changing=False),
            _path("complete-reconstruction", terminal=committed, state_changing=False),
            _path("pending-reconstruction", terminal=committed, state_changing=False),
            _path("conflict-reconstruction", terminal=committed, state_changing=False),
            _path("repairable-reconstruction", terminal=committed, state_changing=False),
            _path("filesystem-github-adapter-parity", terminal=committed, state_changing=True),
            _path("adapter-exact-retry-idempotent", terminal=committed, state_changing=False),
            _path(
                "github-adapter-interruption-recovered",
                terminal=recovered,
                state_changing=True,
                recovery=RecoveryStrategy.EXACT_RETRY,
            ),
            _path("adapter-immutable-conflict-denied", terminal=rolled_back, state_changing=False),
            _path("adapter-incomplete-reconstruction", terminal=rolled_back, state_changing=False),
            _path("intent-tamper-denied", terminal=rolled_back, state_changing=False),
            _path("production-context-denied", terminal=rolled_back, state_changing=False),
        ],
    )
