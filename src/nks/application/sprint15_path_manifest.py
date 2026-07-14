"""Machine-readable path matrix for Sprint 15 performance boundaries."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(
    path_id: str,
    *,
    terminal: TransactionTerminalState = TransactionTerminalState.COMMITTED,
) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=False,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=[
            "production-effect",
            "production-data-use",
            "private-data-use",
            "production-capacity-claim",
            "authority-escalation",
        ],
    )


def sprint15_path_manifest() -> OperationPathManifest:
    denied = TransactionTerminalState.ROLLED_BACK
    paths = [
        _path("transaction-small"),
        _path("transaction-medium"),
        _path("state-write-small"),
        _path("state-write-medium"),
        _path("reconciliation-small"),
        _path("reconciliation-medium"),
        _path("transition-small"),
        _path("transition-medium"),
        _path("model-use-small"),
        _path("model-use-medium"),
        _path("reconstruction-small"),
        _path("reconstruction-medium"),
        _path("export-import-small"),
        _path("export-import-medium"),
        _path("recovery-cost-measured"),
        _path("storage-growth-measured"),
        _path("memory-peak-measured"),
        _path("throughput-measured"),
        _path("latency-percentiles-measured"),
        _path("overload-budget-failure", terminal=denied),
        _path("error-rate-budget-failure", terminal=denied),
        _path("mismatched-budget-denied", terminal=denied),
        _path("production-context-denied", terminal=denied),
        _path("private-data-denied", terminal=denied),
        _path("production-data-denied", terminal=denied),
        _path("production-capacity-claim-denied", terminal=denied),
        _path("incomplete-family-coverage-denied", terminal=denied),
        _path("deterministic-report-hash"),
    ]
    return OperationPathManifest(
        operation_family="enki-performance-capacity-resource-boundaries",
        execution_context=ExecutionContext.TEST,
        paths=paths,
    )
