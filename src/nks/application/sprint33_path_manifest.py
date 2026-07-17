"""Machine-readable path matrix for Sprint 33 hosted downstream integration."""

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
            "direct-canonical-write",
            "cross-product-leakage",
            "authority-reuse",
            "human-agency-bypass",
        ],
    )


def sprint33_hosted_downstream_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-hosted-downstream-consumer-integration",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("media-governed-source-retrieval"),
            _path("media-publication-shaped-no-effect"),
            _path("media-feedback-calibration"),
            _path("career-professional-state-retrieval"),
            _path("career-opportunity-projection"),
            _path("career-external-action-approved-test-path"),
            _path("cognitive-history-retrieval"),
            _path("cognitive-correction-request"),
            _path("cognitive-retraction-request"),
            _path("human-controls-stricter-than-tenant"),
            _path("exact-product-retry-no-effect"),
            _path("cross-product-purpose-denied", success=False),
            _path("cross-product-audience-denied", success=False),
            _path("cross-product-subject-denied", success=False),
            _path("cross-product-tenant-denied", success=False),
            _path("cross-product-intent-denied", success=False),
            _path("career-missing-external-action-approval-denied", success=False),
            _path("career-mismatched-external-action-approval-denied", success=False),
            _path("human-consent-denied", success=False),
            _path("human-revocation-denied", success=False),
            _path("direct-canonical-product-output-denied", success=False),
            _path("production-effect-denied", success=False),
        ],
    )
