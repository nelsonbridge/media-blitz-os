"""Machine-readable path matrix for Sprint 32 governed retrieval and model gateway."""

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
            "canonical-mutation",
            "cross-boundary-leakage",
            "projection-authority",
        ],
    )


def sprint32_retrieval_model_gateway_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-governed-retrieval-model-gateway",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("current-authority-retrieval"),
            _path("historical-retrieval"),
            _path("structured-retrieval"),
            _path("semantic-retrieval"),
            _path("deterministic-pagination"),
            _path("noncanonical-projection"),
            _path("policy-filtered-model-package"),
            _path("provider-neutral-model-gateway"),
            _path("model-gateway-receipt"),
            _path("deterministic-replay"),
            _path("tenant-leakage-denied", success=False),
            _path("subject-leakage-denied", success=False),
            _path("audience-leakage-denied", success=False),
            _path("purpose-leakage-denied", success=False),
            _path("stale-state-denied", success=False),
            _path("stale-cursor-denied", success=False),
            _path("invalid-context-hash-denied", success=False),
            _path("test-external-effect-denied", success=False),
            _path("model-output-canonicalization-denied", success=False),
        ],
    )
