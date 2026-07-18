"""Machine-readable TEST path matrix for Sprint 46 observability."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(path_id: str, *, denied: bool = False) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=(
            TransactionTerminalState.ROLLED_BACK if denied else TransactionTerminalState.COMMITTED
        ),
        state_changing=False,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=[
            "production-effect",
            "direct-canonical-write",
            "recovery-authorization",
            "protected-payload-telemetry",
            "secret-telemetry",
            "authority-widening",
        ],
    )


def sprint46_operational_observability_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-operational-observability-incident-management",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("bounded-metrics-traces-diagnostics-health"),
            _path("stable-correlation-identifiers"),
            _path("protected-content-denied", denied=True),
            _path("secret-telemetry-denied", denied=True),
            _path("queue-pressure-observable"),
            _path("saturation-observable"),
            _path("latency-observable"),
            _path("failure-observable"),
            _path("retry-observable"),
            _path("recovery-observable"),
            _path("provider-degradation-observable"),
            _path("incident-authority-lineage-hash-bound"),
            _path("incident-evidence-lineage-hash-bound"),
            _path("incident-recovery-lineage-hash-bound"),
            _path("telemetry-loss-detected"),
            _path("telemetry-duplicate-conflict-detected"),
            _path("telemetry-correlation-mismatch-detected"),
            _path("missing-incident-lineage-denied", denied=True),
            _path("health-report-deterministic"),
            _path("incident-reconstruction-deterministic"),
            _path("observability-cannot-mutate-canonical-state", denied=True),
            _path("observability-cannot-authorize-recovery", denied=True),
        ],
    )
