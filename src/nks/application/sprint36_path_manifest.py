"""Machine-readable TEST path matrix for Sprint 36 hosted release candidate."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(path_id: str, *, denied: bool = False) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=(
            TransactionTerminalState.ROLLED_BACK if denied else TransactionTerminalState.COMMITTED
        ),
        state_changing=False,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=[
            "production-effect",
            "production-deployment",
            "production-approval",
            "failed-evidence-as-pass",
            "missing-evidence-as-pass",
            "automated-human-decision",
        ],
    )


def sprint36_hosted_release_candidate_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-hosted-release-candidate-decision-package",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("corrected-architecture-baseline-bound"),
            _path("software-readiness-reported-separately"),
            _path("hosted-architecture-validation-reported-separately"),
            _path("zero-cost-envelope-reported-separately"),
            _path("production-deployment-readiness-reported-separately"),
            _path("software-readiness-pass-test-only"),
            _path("hosted-validation-blocked-incomplete-campaigns"),
            _path("local-zero-cost-distinguished-from-hosted-envelope"),
            _path("all-seven-production-controls-remain-unresolved"),
            _path("production-readiness-blocked"),
            _path("blocked-evidence-cannot-be-pass", denied=True),
            _path("planned-evidence-cannot-be-pass", denied=True),
            _path("production-readiness-cannot-use-test-status", denied=True),
            _path("all-four-human-dispositions-supported"),
            _path("decision-remains-pending-human"),
            _path("automation-cannot-select-disposition", denied=True),
            _path("multi-consumer-evidence-bound"),
            _path("recovery-portability-evidence-bound"),
            _path("performance-evidence-qualified-nonproduction"),
            _path("known-limitations-explicit"),
            _path("runbook-explicit"),
            _path("rollback-plan-explicit"),
            _path("migration-path-explicit"),
            _path("support-boundaries-explicit"),
            _path("independent-review-explicit"),
            _path("release-candidate-manifest-deterministic"),
            _path("decision-request-manifest-deterministic"),
            _path("sprint-completion-does-not-authorize-deployment", denied=True),
        ],
    )
