"""Declared path-complete TEST matrices for governed Enki operation families."""

from __future__ import annotations

from nks.application.governed_transactions import (
    RecoveryStrategy,
    TransactionTerminalState,
)
from nks.application.path_manifest import (
    OperationPathExpectation,
    OperationPathManifest,
)
from nks.governance.approvals import ExecutionContext


def _path(
    path_id: str,
    *,
    terminal: TransactionTerminalState,
    state_changing: bool,
    recovery: RecoveryStrategy,
) -> OperationPathExpectation:
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=terminal,
        state_changing=state_changing,
        recovery_strategy=recovery,
        prohibited_effects=["production-effect"],
    )


def state_write_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-state-write",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("person-success", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("organization-success", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("project-success", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("partial-write", terminal=TransactionTerminalState.RECOVERED, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
            _path("unknown-reference", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("subject-leakage", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("plan-tamper", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
        ],
    )


def human_migration_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="human-state-migration",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("success", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("partial-write", terminal=TransactionTerminalState.RECOVERED, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
            _path("consent-denied", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("consent-unknown", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("purpose-mismatch", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("policy-expired", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("policy-revoked", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("missing-origin", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("unknown-transition-endpoint", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("semantic-tamper", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
        ],
    )


def reconciliation_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-reconciliation",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("applicable", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("future", terminal=TransactionTerminalState.COMMITTED, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("retracted", terminal=TransactionTerminalState.COMMITTED, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("historical", terminal=TransactionTerminalState.COMMITTED, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("disputed", terminal=TransactionTerminalState.COMMITTED, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("context-mismatch", terminal=TransactionTerminalState.COMMITTED, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("ineligible-endpoint", terminal=TransactionTerminalState.COMMITTED, state_changing=False, recovery=RecoveryStrategy.NONE),
            _path("persistence-interruption", terminal=TransactionTerminalState.RECOVERED, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
        ],
    )


def disclosure_path_manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="enki-disclosure",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("subject-requested", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("subject-not-requested", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("consent-revoked", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("private-public", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("redaction-required", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("policy-revoked", terminal=TransactionTerminalState.COMMITTED, state_changing=True, recovery=RecoveryStrategy.NONE),
            _path("receipt-interruption", terminal=TransactionTerminalState.RECOVERED, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
            _path("approval-hash-mismatch", terminal=TransactionTerminalState.ROLLED_BACK, state_changing=False, recovery=RecoveryStrategy.NONE),
        ],
    )
