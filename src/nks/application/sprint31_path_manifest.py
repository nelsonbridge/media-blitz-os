"""Machine-readable path matrix for Sprint 31 temporal authority hardening."""

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
            "historical-rewrite",
            "authority-escalation",
            "unsupported-supersession",
        ],
    )


def sprint31_temporal_authority_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-temporal-authority-hardening",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("historical-truth-preserved"),
            _path("current-authority-resolved"),
            _path("effective-time-separated-from-recorded-time"),
            _path("authority-valid-time-explicit"),
            _path("supersession-chain-reconstructable"),
            _path("revocation-terminal-state-explicit"),
            _path("consumption-terminal-state-explicit"),
            _path("retraction-terminal-state-explicit"),
            _path("deterministic-timeline-hash"),
            _path("deterministic-resolution-hash"),
            _path("legacy-migration-preserves-lineage"),
            _path("ambiguous-current-authority-denied", success=False),
            _path("invalid-temporal-window-denied", success=False),
            _path("cross-authority-supersession-denied", success=False),
            _path("missing-terminal-evidence-denied", success=False),
            _path("supersession-cycle-denied", success=False),
        ],
    )
