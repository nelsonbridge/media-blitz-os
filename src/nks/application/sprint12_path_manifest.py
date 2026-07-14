"""Machine-readable path matrix for Sprint 12 reconstruction and portability."""

from __future__ import annotations

from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext


def _path(
    path_id: str,
    *,
    terminal: TransactionTerminalState = TransactionTerminalState.COMMITTED,
    state_changing: bool = False,
    recovery: RecoveryStrategy = RecoveryStrategy.NONE,
) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=state_changing,
        recovery_strategy=recovery,
        prohibited_effects=["production-effect", "authority-escalation"],
    )


def sprint12_path_manifest() -> OperationPathManifest:
    rollback = TransactionTerminalState.ROLLED_BACK
    recovered = TransactionTerminalState.RECOVERED
    return OperationPathManifest(
        operation_family="enki-forensics-portability-work-control",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("reconstruction-complete"),
            _path("reconstruction-incomplete"),
            _path("reconstruction-repairable"),
            _path("reconstruction-rolled-back"),
            _path("reconstruction-conflict", terminal=rollback),
            _path("corrupt-record-hash", terminal=rollback),
            _path("stale-plan-hash", terminal=rollback),
            _path("cross-context-record", terminal=rollback),
            _path("authority-class-mismatch", terminal=rollback),
            _path("all-operation-families"),
            _path("portable-export-import", state_changing=True),
            _path("portable-exact-replay", terminal=recovered, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
            _path("portable-conflicting-import", terminal=rollback),
            _path("test-to-production-import", terminal=rollback),
            _path("clean-room-recovery", state_changing=True),
            _path("disaster-recovery-exact-retry", terminal=recovered, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
            _path("filesystem-github-parity", state_changing=True),
            _path("unsupported-delete-denied", terminal=rollback),
            _path("unsupported-replace-denied", terminal=rollback),
            _path("work-completion-commit", state_changing=True),
            _path("work-completion-missing-evidence", terminal=rollback),
            _path("work-completion-stale-before", terminal=rollback),
            _path("work-completion-before-consumption", terminal=rollback, recovery=RecoveryStrategy.RELEASE_RESERVATION),
            _path("work-completion-after-consumption", terminal=recovered, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
            _path("work-completion-partial-write-recovery", terminal=recovered, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
        ],
    )
