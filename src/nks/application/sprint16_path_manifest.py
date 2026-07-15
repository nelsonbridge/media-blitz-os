"""Machine-readable path matrix for Sprint 16 isolation proof."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(path_id: str, *, terminal: TransactionTerminalState, state_changing: bool) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=state_changing,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=["production-effect"],
    )


def sprint16_isolation_path_manifest() -> OperationPathManifest:
    committed = TransactionTerminalState.COMMITTED
    rolled_back = TransactionTerminalState.ROLLED_BACK
    return OperationPathManifest(
        operation_family="enki-boundary-isolation",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("shared-store-success", terminal=committed, state_changing=True),
            _path("separated-store-success", terminal=committed, state_changing=True),
            _path("same-id-different-tenant", terminal=committed, state_changing=True),
            _path("cross-tenant-denied", terminal=rolled_back, state_changing=False),
            _path("cross-subject-denied", terminal=rolled_back, state_changing=False),
            _path("cross-domain-denied", terminal=rolled_back, state_changing=False),
            _path("cross-audience-denied", terminal=rolled_back, state_changing=False),
            _path("test-to-production-denied", terminal=rolled_back, state_changing=False),
            _path("boundary-tamper-denied", terminal=rolled_back, state_changing=False),
            _path("export-import-preserves-boundary", terminal=committed, state_changing=True),
            _path("duplicate-delivery-idempotent", terminal=committed, state_changing=False),
            _path("conflicting-duplicate-denied", terminal=rolled_back, state_changing=False),
            _path("recovery-mismatch-denied", terminal=rolled_back, state_changing=False),
            _path("path-traversal-denied", terminal=rolled_back, state_changing=False),
            _path("forged-envelope-denied", terminal=rolled_back, state_changing=False),
            _path("local-process-cross-tenant-denied", terminal=rolled_back, state_changing=False),
            _path("human-policy-stricter", terminal=rolled_back, state_changing=False),
            _path("diagnostic-redaction", terminal=committed, state_changing=False),
        ],
    )
