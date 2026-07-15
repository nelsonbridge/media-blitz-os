"""Machine-readable path matrix for Sprint 23 readiness decision packaging."""

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
            "self-certification",
            "multitenancy-accreditation",
            "unvalidated-control-promotion",
        ],
    )


def sprint23_readiness_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-1.0-readiness-decision-package",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("all-prior-sprint-evidence-anchored"),
            _path("campaign-matrix-explicit"),
            _path("known-limitations-complete"),
            _path("production-prerequisites-explicit"),
            _path("zero-external-services-budget-preserved"),
            _path("local-test-proof-not-production-certification"),
            _path("operating-runbook-present"),
            _path("rollback-plan-present"),
            _path("support-boundaries-present"),
            _path("independent-review-no-self-certification"),
            _path("enki-1.0-candidate-versioned"),
            _path("human-decision-request-unresolved"),
            _path("manifest-tamper-denied", success=False),
            _path("validated-control-without-evidence-denied", success=False),
        ],
    )
