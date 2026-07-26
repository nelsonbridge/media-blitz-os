"""Machine-readable path matrix for Sprint 28 GCP-NEON-R2 hosted TEST validation."""

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
            "runtime-boundary-bypass",
            "canonical-authority-escalation",
        ],
    )


def sprint28_gcp_neon_r2_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-gcp-neon-r2-hosted-test-validation",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("three-provider-test-identities-and-credentials-required"),
            _path("ordered-validation-phases-preserved"),
            _path("cloud-run-python-service-boundary-preserved"),
            _path("cross-provider-failure-does-not-duplicate-canonical-effects"),
            _path("cross-provider-latency-egress-quota-trust-evidence-captured"),
            _path("privacy-preserving-observability-preserved"),
            _path("credential-revocation-and-teardown-required"),
            _path("post-teardown-state-reconstructable-from-governed-exports"),
            _path("results-remain-test-evidence-only"),
            _path("missing-hosted-capability-blocks-execution", success=False),
        ],
    )
