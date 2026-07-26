"""Machine-readable path matrix for Sprint 27 CF-NEON-R2 hosted TEST validation."""

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
            "canonical-authority-escalation",
        ],
    )


def sprint27_cf_neon_r2_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-cf-neon-r2-hosted-test-validation",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("test-identities-and-credentials-required"),
            _path("ordered-validation-phases-preserved"),
            _path("governed-synthetic-import-boundary-preserved"),
            _path("cross-provider-failure-does-not-duplicate-canonical-effects"),
            _path("cross-provider-latency-egress-quota-evidence-captured"),
            _path("credential-revocation-and-teardown-required"),
            _path("post-teardown-state-reconstructable-from-governed-exports"),
            _path("results-remain-test-evidence-only"),
            _path("missing-hosted-capability-blocks-execution", success=False),
        ],
    )
