"""Machine-readable path matrix for Sprint 30 hosting direction packaging."""

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
            "production-approval",
            "default-hosting-selection",
            "unvalidated-control-promotion",
            "silent-evidence-substitution",
        ],
    )


def sprint30_hosting_direction_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-hosting-direction-decision-package",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("finalist-evidence-status-explicit"),
            _path("cross-finalist-evaluation-hash-bound"),
            _path("recommendation-separated-from-human-approval"),
            _path("production-prerequisites-explicit"),
            _path("production-control-validation-sequenced"),
            _path("migration-rollback-dr-obligations-explicit"),
            _path("decision-options-select-defer-more-evidence-reject"),
            _path("no-production-deployment-authorized"),
            _path("winner-selection-with-incomplete-evidence-denied", success=False),
            _path("default-selection-without-human-decision-denied", success=False),
        ],
    )
