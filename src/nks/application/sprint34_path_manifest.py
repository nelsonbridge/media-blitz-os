"""Machine-readable TEST path matrix for Sprint 34 platform operations."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(
    path_id: str,
    *,
    terminal: TransactionTerminalState = TransactionTerminalState.COMMITTED,
    recovery: RecoveryStrategy = RecoveryStrategy.NONE,
) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=False,
        recovery_strategy=recovery,
        prohibited_effects=[
            "production-effect",
            "direct-canonical-write",
            "cross-product-authority-widening",
            "cross-tenant-leakage",
            "cross-subject-leakage",
            "protected-payload-telemetry",
        ],
    )


def sprint34_multi_consumer_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-multi-consumer-platform-operations",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("three-suite-concurrent-success"),
            _path("tenant-isolation-under-concurrency"),
            _path("namespace-isolation-under-concurrency"),
            _path("subject-isolation-under-concurrency"),
            _path("domain-isolation-under-concurrency"),
            _path("audience-isolation-under-concurrency"),
            _path("purpose-isolation-under-concurrency"),
            _path("execution-context-isolation-under-concurrency"),
            _path("queue-pressure-detected"),
            _path("contention-detected"),
            _path("duplicate-work-reuses-exact-product-receipt"),
            _path(
                "transient-failure-exact-retry-recovers",
                terminal=TransactionTerminalState.RECOVERED,
                recovery=RecoveryStrategy.EXACT_RETRY,
            ),
            _path(
                "persistent-consumer-failure-rolls-back-no-effect",
                terminal=TransactionTerminalState.ROLLED_BACK,
                recovery=RecoveryStrategy.NONE,
            ),
            _path("consumer-failure-does-not-widen-peer-authority"),
            _path("consumer-failure-does-not-change-canonical-fingerprint"),
            _path("privacy-safe-queue-telemetry"),
            _path("privacy-safe-incident-evidence"),
            _path("portable-bundle-deterministic"),
            _path("portable-bundle-reconstruction-exact"),
            _path("tampered-portable-bundle-denied", terminal=TransactionTerminalState.ROLLED_BACK),
            _path("production-boundary-denied", terminal=TransactionTerminalState.ROLLED_BACK),
        ],
    )
