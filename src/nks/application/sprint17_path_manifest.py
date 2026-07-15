"""Machine-readable path matrix for Sprint 17 policy lifecycle."""

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


def sprint17_policy_path_manifest() -> OperationPathManifest:
    committed = TransactionTerminalState.COMMITTED
    rolled_back = TransactionTerminalState.ROLLED_BACK
    return OperationPathManifest(
        operation_family="enki-policy-lifecycle",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("immutable-version-created", terminal=committed, state_changing=True),
            _path("deterministic-comparison", terminal=committed, state_changing=False),
            _path("side-effect-free-simulation", terminal=committed, state_changing=False),
            _path("approval-bound-activation", terminal=committed, state_changing=True),
            _path("approval-bound-rollback", terminal=committed, state_changing=True),
            _path("approval-bound-retirement", terminal=committed, state_changing=True),
            _path("historical-policy-attribution", terminal=committed, state_changing=False),
            _path("exact-retry-idempotent", terminal=committed, state_changing=False),
            _path("invalid-version-link-denied", terminal=rolled_back, state_changing=False),
            _path("bundle-tamper-denied", terminal=rolled_back, state_changing=False),
            _path("cross-boundary-comparison-denied", terminal=rolled_back, state_changing=False),
            _path("production-simulation-denied", terminal=rolled_back, state_changing=False),
            _path("test-activation-of-production-denied", terminal=rolled_back, state_changing=False),
            _path("immutable-conflict-denied", terminal=rolled_back, state_changing=False),
        ],
    )
