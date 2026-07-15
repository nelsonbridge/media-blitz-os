"""Machine-readable path matrix for Sprint 22 downstream product proofs."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(path_id: str, *, success: bool) -> OperationPathExpectation:
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
            "direct-canonical-write",
            "direct-approval-consumption",
            "cross-product-leakage",
            "authority-reuse",
            "audience-widening",
        ],
    )


def sprint22_downstream_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-downstream-product-boundary-proof",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("media-blitz-end-to-end-no-effect", success=True),
            _path("career-intelligence-end-to-end-no-effect", success=True),
            _path("cognitive-continuity-end-to-end-no-effect", success=True),
            _path("provenance-context-privacy-authority-preserved", success=True),
            _path("exact-package-retry-no-effect", success=True),
            _path("cross-product-data-leakage-denied", success=False),
            _path("cross-product-authority-reuse-denied", success=False),
            _path("audience-widening-denied", success=False),
            _path("direct-canonical-product-output-denied", success=False),
            _path("unpermitted-output-kind-denied", success=False),
            _path("production-context-denied", success=False),
        ],
    )
