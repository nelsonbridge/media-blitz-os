"""Machine-readable path matrix for Sprint 24 hosted-architecture exploration."""

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
            "infrastructure-provisioning",
            "unvalidated-control-promotion",
            "paid-external-service",
            "default-hosting-selection",
        ],
    )


def sprint24_hosting_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-hosted-architecture-exploration",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("official-pricing-sources-recorded"),
            _path("single-cloud-options-compared"),
            _path("provider-split-options-compared"),
            _path("control-data-split-compared"),
            _path("portability-hybrid-compared"),
            _path("single-cloud-reference-architecture-present"),
            _path("split-cloud-reference-architecture-present"),
            _path("threat-trust-failure-analysis-present"),
            _path("cost-model-zero-dollar-boundary"),
            _path("production-prerequisite-mapping-explicit"),
            _path("migration-rollback-explicit"),
            _path("shortlist-present"),
            _path("human-decision-unresolved"),
            _path("production-provisioning-prohibited"),
            _path("unsupported-production-validation-claim-denied", success=False),
            _path("default-hosting-selection-denied", success=False),
        ],
    )
