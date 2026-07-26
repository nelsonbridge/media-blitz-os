"""Machine-readable path matrix for Sprint 25 hosted multi-finalist validation foundation."""

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
            "production-credentials",
            "production-data",
            "incomplete-finalist-contract",
        ],
    )


def sprint25_hosted_validation_foundation_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-hosted-multi-finalist-validation-foundation",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("multi-finalist-direction-explicit"),
            _path("all-finalists-covered-in-canonical-order"),
            _path("ordered-validation-phases-complete"),
            _path("boundary-dimensions-complete"),
            _path("production-prerequisites-explicit-and-unresolved"),
            _path("capability-gate-fails-closed-when-missing"),
            _path("test-only-authority-enforced"),
            _path("nonfinalist-validation-rejected", success=False),
            _path("incomplete-phase-contract-rejected", success=False),
        ],
    )
