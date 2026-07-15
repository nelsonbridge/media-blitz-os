"""Machine-readable path matrix for Sprint 18 observability."""

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
        prohibited_effects=["production-effect", "protected-content-telemetry"],
    )


def sprint18_observability_path_manifest() -> OperationPathManifest:
    committed = TransactionTerminalState.COMMITTED
    rolled_back = TransactionTerminalState.ROLLED_BACK
    return OperationPathManifest(
        operation_family="enki-privacy-observability",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("health-event", terminal=committed),
            _path("metric-event", terminal=committed),
            _path("trace-event", terminal=committed),
            _path("diagnostic-event", terminal=committed),
            _path("stable-correlation", terminal=committed),
            _path("loss-detected", terminal=committed),
            _path("duplicate-detected", terminal=committed),
            _path("hash-conflict-detected", terminal=committed),
            _path("correlation-break-detected", terminal=committed),
            _path("incident-reconstructed", terminal=committed),
            _path("exact-duplicate-idempotent", terminal=committed),
            _path("protected-content-denied", terminal=rolled_back),
            _path("human-state-denied", terminal=rolled_back),
            _path("secret-denied", terminal=rolled_back),
            _path("unbounded-metadata-denied", terminal=rolled_back),
            _path("production-context-denied", terminal=rolled_back),
            _path("identity-conflict-denied", terminal=rolled_back),
            _path("telemetry-tamper-denied", terminal=rolled_back),
        ],
    )
