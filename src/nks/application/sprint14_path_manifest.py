"""Machine-readable path matrix for Sprint 14 release integrity."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(
    path_id: str,
    *,
    terminal: TransactionTerminalState = TransactionTerminalState.COMMITTED,
    state_changing: bool = False,
) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=state_changing,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=[
            "production-credential-use",
            "external-effect",
            "release-self-approval",
            "artifact-rewrite",
            "authority-escalation",
        ],
    )


def sprint14_path_manifest() -> OperationPathManifest:
    denied = TransactionTerminalState.ROLLED_BACK
    return OperationPathManifest(
        operation_family="enki-reproducible-release-supply-chain-integrity",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("clean-room-success"),
            _path("exact-candidate-regeneration"),
            _path("dependency-inventory-deterministic"),
            _path("workflow-inventory-deterministic"),
            _path("sbom-deterministic"),
            _path("attestation-deterministic"),
            _path("artifact-substitution", terminal=denied),
            _path("missing-artifact", terminal=denied),
            _path("dependency-drift", terminal=denied),
            _path("workflow-drift", terminal=denied),
            _path("missing-source-provenance", terminal=denied),
            _path("source-provenance-mismatch", terminal=denied),
            _path("candidate-hash-tamper", terminal=denied),
            _path("loop-receipt-tamper", terminal=denied),
            _path("loop-receipt-manifest-mismatch", terminal=denied),
            _path("secret-aws", terminal=denied),
            _path("secret-github", terminal=denied),
            _path("secret-openai", terminal=denied),
            _path("private-key-leak", terminal=denied),
            _path("release-decision-populated", terminal=denied),
            _path("production-credential-not-required"),
            _path("test-evidence-cannot-authorize-release", terminal=denied),
        ],
    )
