"""Machine-readable path matrix for Sprint 26 CF-NATIVE hosted TEST validation block state."""

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
            "credential-reuse",
            "teardown-bypass",
            "simulated-hosted-success-without-capabilities",
        ],
    )


def sprint26_cf_native_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-cf-native-hosted-test-validation",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("external-test-capabilities-required"),
            _path("missing-capabilities-fail-closed"),
            _path("blocked-reason-explicit-and-attributable"),
            _path("production-credential-substitution-prohibited", success=False),
            _path("hosted-success-claim-without-capabilities-prohibited", success=False),
        ],
    )
