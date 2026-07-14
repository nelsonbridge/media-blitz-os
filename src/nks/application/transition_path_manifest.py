"""Machine-readable path-complete TEST matrix for governed transitions."""

from __future__ import annotations

from nks.application.governed_transactions import (
    RecoveryStrategy,
    TransactionTerminalState,
)
from nks.application.path_manifest import (
    OperationPathExpectation,
    OperationPathManifest,
)
from nks.governance.approvals import ExecutionContext


def _path(
    path_id: str,
    *,
    terminal: TransactionTerminalState,
    state_changing: bool,
    recovery: RecoveryStrategy,
) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=state_changing,
        recovery_strategy=recovery,
        prohibited_effects=["production-effect"],
    )


def transition_path_manifest() -> OperationPathManifest:
    """Declare every automated terminal path required for Sprint 10."""

    committed = TransactionTerminalState.COMMITTED
    rolled_back = TransactionTerminalState.ROLLED_BACK
    recovered = TransactionTerminalState.RECOVERED
    none = RecoveryStrategy.NONE

    return OperationPathManifest(
        operation_family="enki-transition",
        execution_context=ExecutionContext.TEST,
        paths=[
            *[
                _path(
                    f"type-{transition_type}",
                    terminal=committed,
                    state_changing=True,
                    recovery=none,
                )
                for transition_type in (
                    "correction",
                    "refinement",
                    "supersession",
                    "retraction",
                    "reversal",
                    "expansion",
                    "restriction",
                    "confidence-change",
                    "context-shift",
                    "merge",
                    "split",
                    "deprecation",
                )
            ],
            _path(
                "invalid-cardinality",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "unknown-from-state",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "stale-input",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "branch-denied",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "branch-accepted",
                terminal=committed,
                state_changing=True,
                recovery=none,
            ),
            _path(
                "overlap-accepted",
                terminal=committed,
                state_changing=True,
                recovery=none,
            ),
            _path(
                "authority-conflict-denied",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "authority-conflict-accepted",
                terminal=committed,
                state_changing=True,
                recovery=none,
            ),
            _path(
                "cycle",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "contradiction",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "context-mismatch",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "test-production-authority-mismatch",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "plan-tamper",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "persistence-interruption",
                terminal=recovered,
                state_changing=True,
                recovery=RecoveryStrategy.EXACT_RETRY,
            ),
            _path(
                "cross-transaction-replay",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "immutable-record-conflict",
                terminal=rolled_back,
                state_changing=False,
                recovery=none,
            ),
            _path(
                "person-regression",
                terminal=committed,
                state_changing=True,
                recovery=none,
            ),
            *[
                _path(
                    f"reconstruction-{status}",
                    terminal=committed,
                    state_changing=False,
                    recovery=none,
                )
                for status in (
                    "complete",
                    "incomplete",
                    "repairable",
                    "conflict",
                    "rolled-back",
                )
            ],
        ],
    )
