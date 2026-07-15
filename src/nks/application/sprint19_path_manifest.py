"""Machine-readable path matrix for Sprint 19 retention and continuity."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(path_id: str, *, terminal: TransactionTerminalState, state_changing: bool) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=state_changing,
        recovery_strategy=RecoveryStrategy.NONE,
        prohibited_effects=["production-effect", "historical-rewrite"],
    )


def sprint19_retention_path_manifest() -> OperationPathManifest:
    committed = TransactionTerminalState.COMMITTED
    rolled_back = TransactionTerminalState.ROLLED_BACK
    return OperationPathManifest(
        operation_family="enki-retention-continuity",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("versioned-policy-created", terminal=committed, state_changing=True),
            _path("archive-receipted", terminal=committed, state_changing=True),
            _path("restriction-receipted", terminal=committed, state_changing=True),
            _path("redaction-receipted", terminal=committed, state_changing=True),
            _path("tombstone-receipted", terminal=committed, state_changing=True),
            _path("expiration-receipted", terminal=committed, state_changing=True),
            _path("revocation-receipted", terminal=committed, state_changing=True),
            _path("restore-allowed-state", terminal=committed, state_changing=True),
            _path("exact-retry-idempotent", terminal=committed, state_changing=False),
            _path("historical-lineage-preserved", terminal=committed, state_changing=False),
            _path("downstream-control-denied", terminal=committed, state_changing=False),
            _path("hash-continuity-proved", terminal=committed, state_changing=True),
            _path("hash-tamper-detected", terminal=rolled_back, state_changing=False),
            _path("unsupported-algorithm-denied", terminal=rolled_back, state_changing=False),
            _path("premature-archive-denied", terminal=rolled_back, state_changing=False),
            _path("premature-expiry-denied", terminal=rolled_back, state_changing=False),
            _path("authority-mismatch-denied", terminal=rolled_back, state_changing=False),
            _path("purpose-mismatch-denied", terminal=rolled_back, state_changing=False),
            _path("boundary-mismatch-denied", terminal=rolled_back, state_changing=False),
            _path("unpermitted-action-denied", terminal=rolled_back, state_changing=False),
            _path("terminal-state-rewrite-denied", terminal=rolled_back, state_changing=False),
            _path("immutable-conflict-denied", terminal=rolled_back, state_changing=False),
        ],
    )
