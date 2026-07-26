"""Machine-readable path matrix for Sprint 29 cross-finalist evaluation."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(path_id: str, *, success: bool = True) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=(
            TransactionTerminalState.COMMITTED
            if success
            else TransactionTerminalState.ROLLED_BACK
        ),
        state_changing=False,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=[
            "production-effect",
            "default-hosting-selection",
            "silent-evidence-substitution",
            "unvalidated-control-promotion",
        ],
    )


def sprint29_cross_finalist_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-cross-finalist-comparative-evaluation",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("all-finalists-reported-in-canonical-order"),
            _path("comparison-dimensions-explicit"),
            _path("incomplete-evidence-preserves-deferral"),
            _path("recommendation-separate-from-human-decision"),
            _path("evaluation-hash-bound"),
            _path("production-prerequisites-remain-unresolved"),
            _path("winner-selection-with-incomplete-evidence-denied", success=False),
            _path("non-defer-recommendation-with-incomplete-evidence-denied", success=False),
        ],
    )
