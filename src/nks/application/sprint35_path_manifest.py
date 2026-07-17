"""Machine-readable TEST path matrix for Sprint 35 control readiness."""

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
            "test-evidence-as-production-proof",
            "production-credential-persistence",
            "paid-external-service",
        ],
    )


def sprint35_production_control_readiness_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-production-control-validation-readiness",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("all-seven-production-controls-contracted"),
            _path("all-finalists-responsibility-mapped"),
            _path("provider-neutral-contracts-without-hosting-selection"),
            _path("test-substitute-remains-nonproduction"),
            _path("test-evidence-cannot-satisfy-production-gate", denied=True),
            _path("missing-production-capability-blocks-closed", denied=True),
            _path("missing-production-evidence-fails-closed", denied=True),
            _path("production-validation-requires-exact-evidence-contract"),
            _path("production-validation-requires-exact-evidence-owner"),
            _path("production-validation-requires-all-capabilities"),
            _path("cloud-iam-contract-ready"),
            _path("production-identity-federation-contract-ready"),
            _path("managed-database-isolation-contract-ready"),
            _path("network-segmentation-contract-ready"),
            _path("per-tenant-key-management-contract-ready"),
            _path("production-secrets-management-contract-ready"),
            _path("independent-penetration-testing-contract-ready"),
            _path("independent-penetration-test-cannot-self-attest", denied=True),
            _path("rollback-obligations-present"),
            _path("stop-conditions-present"),
            _path("production-credentials-rejected-from-evidence", denied=True),
            _path("zero-dollar-boundary-preserved"),
            _path("sprint-completion-does-not-authorize-production", denied=True),
            _path("readiness-package-deterministic"),
        ],
    )
