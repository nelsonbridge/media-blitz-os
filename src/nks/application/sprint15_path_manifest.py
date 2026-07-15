"""Machine-readable path matrix for Sprint 15 performance boundaries."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(path_id: str, *, terminal: TransactionTerminalState) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=False,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=["production-effect"],
    )


def sprint15_performance_path_manifest() -> OperationPathManifest:
    committed = TransactionTerminalState.COMMITTED
    rolled_back = TransactionTerminalState.ROLLED_BACK
    return OperationPathManifest(
        operation_family="enki-performance-boundaries",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("transaction-benchmark", terminal=committed),
            _path("state-write-benchmark", terminal=committed),
            _path("reconciliation-benchmark", terminal=committed),
            _path("transition-benchmark", terminal=committed),
            _path("model-use-benchmark", terminal=committed),
            _path("reconstruction-benchmark", terminal=committed),
            _path("portability-benchmark", terminal=committed),
            _path("latency-budget", terminal=committed),
            _path("throughput-budget", terminal=committed),
            _path("memory-budget", terminal=committed),
            _path("storage-growth-budget", terminal=committed),
            _path("recovery-cost-budget", terminal=committed),
            _path("error-rate-budget", terminal=committed),
            _path("overload-denied", terminal=rolled_back),
            _path("private-data-denied", terminal=rolled_back),
            _path("production-data-denied", terminal=rolled_back),
            _path("production-context-denied", terminal=rolled_back),
            _path("production-capacity-claim-denied", terminal=rolled_back),
        ],
    )
