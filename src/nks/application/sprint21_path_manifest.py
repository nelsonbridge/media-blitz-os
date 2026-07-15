"""Machine-readable path matrix for Sprint 21 consumer compatibility."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(
    path_id: str,
    *,
    terminal: TransactionTerminalState,
    state_changing: bool,
) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=state_changing,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=[
            "repository-shortcut",
            "direct-canonical-write",
            "direct-approval-consumption",
            "unsupported-version-fallback",
        ],
    )


def sprint21_consumer_path_manifest() -> OperationPathManifest:
    committed = TransactionTerminalState.COMMITTED
    rolled_back = TransactionTerminalState.ROLLED_BACK
    return OperationPathManifest(
        operation_family="enki-stable-consumer-contract",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("api-query-authorized", terminal=committed, state_changing=False),
            _path("cli-query-authorized", terminal=committed, state_changing=False),
            _path("api-cli-service-parity", terminal=committed, state_changing=False),
            _path("command-authority-checked", terminal=committed, state_changing=True),
            _path("pagination-deterministic", terminal=committed, state_changing=False),
            _path("exact-idempotent-retry", terminal=committed, state_changing=False),
            _path("idempotency-conflict-denied", terminal=rolled_back, state_changing=False),
            _path("unsupported-version-denied", terminal=rolled_back, state_changing=False),
            _path("ambiguous-version-denied", terminal=rolled_back, state_changing=False),
            _path("authority-mismatch-denied", terminal=rolled_back, state_changing=False),
            _path("repository-shortcut-denied", terminal=rolled_back, state_changing=False),
            _path("direct-operation-denied", terminal=rolled_back, state_changing=False),
            _path("invalid-request-denied", terminal=rolled_back, state_changing=False),
            _path("contract-docs-deterministic", terminal=committed, state_changing=False),
            _path("compatibility-fixture-deterministic", terminal=committed, state_changing=False),
        ],
    )
