"""Machine-readable path-complete TEST matrix for Enki-native model use."""

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
        prohibited_effects=["unapproved-production-effect"],
    )


def model_use_path_manifest() -> OperationPathManifest:
    rollback = TransactionTerminalState.ROLLED_BACK
    return OperationPathManifest(
        operation_family="enki-model-use",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("exact-include", state_changing=True),
            _path("missing-directive-defer"),
            _path("retracted-withhold"),
            _path("expired-withhold"),
            _path("superseded-withhold"),
            _path("inapplicable-withhold"),
            _path("disputed-defer"),
            _path("consent-denied-withhold"),
            _path("consent-revoked-withhold"),
            _path("consent-unknown-withhold"),
            _path("item-expiry-withhold"),
            _path("item-revocation-withhold"),
            _path("purpose-withhold"),
            _path("internal-external-withhold"),
            _path("private-external-withhold"),
            _path("restricted-withhold"),
            _path("redaction-withhold"),
            _path("transition-choice-required", terminal=rollback),
            _path("transition-explicit-exclusion"),
            _path("transition-explicit-inclusion", state_changing=True),
            _path("duplicate-directive", terminal=rollback),
            _path("absent-item-directive", terminal=rollback),
            _path("directive-purpose-withhold"),
            _path("directive-audience-withhold"),
            _path("directive-context-withhold"),
            _path("directive-expiry-withhold"),
            _path("directive-revocation-withhold"),
            _path("directive-explicit-exclusion"),
            _path("package-context-substitution", terminal=rollback),
            _path("package-tamper", terminal=rollback),
            _path("exact-package-revocation", terminal=rollback),
            _path("revocation-hash-conflict", terminal=rollback),
            _path("test-no-effect-dispatch", state_changing=True),
            _path("test-dispatcher-production-rejection", terminal=rollback),
            _path("production-dispatcher-test-rejection", terminal=rollback),
            _path("production-shaped-fake-transport", state_changing=True),
            _path("test-effect-invariant", terminal=rollback),
            _path("append-only-package-effect-revocation", state_changing=True),
            _path("immutable-package-conflict", terminal=rollback),
            _path("immutable-revocation-conflict", terminal=rollback),
        ],
    )
