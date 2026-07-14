from __future__ import annotations

import pytest
from pydantic import ValidationError

from nks.application.governed_transactions import (
    RecoveryStrategy,
    TransactionTerminalState,
)
from nks.application.path_manifest import (
    OperationPathExpectation,
    OperationPathManifest,
)
from nks.governance.approvals import ExecutionContext


IMPLEMENTED_PATH_IDS = {
    "success",
    "authority-denied",
    "context-mismatch",
    "reservation-interruption",
    "post-consumption-interruption",
    "effect-interruption",
    "exact-retry",
    "duplicate-terminal-retry",
    "cross-plan-replay",
    "immutable-record-conflict",
}


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


def _manifest() -> OperationPathManifest:
    return OperationPathManifest(
        operation_family="governed-transaction",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path(
                "success",
                terminal=TransactionTerminalState.COMMITTED,
                state_changing=True,
                recovery=RecoveryStrategy.NONE,
            ),
            _path(
                "authority-denied",
                terminal=TransactionTerminalState.ROLLED_BACK,
                state_changing=False,
                recovery=RecoveryStrategy.NONE,
            ),
            _path(
                "context-mismatch",
                terminal=TransactionTerminalState.ROLLED_BACK,
                state_changing=False,
                recovery=RecoveryStrategy.NONE,
            ),
            _path(
                "reservation-interruption",
                terminal=TransactionTerminalState.ROLLED_BACK,
                state_changing=True,
                recovery=RecoveryStrategy.RELEASE_RESERVATION,
            ),
            _path(
                "post-consumption-interruption",
                terminal=TransactionTerminalState.RECOVERED,
                state_changing=True,
                recovery=RecoveryStrategy.EXACT_RETRY,
            ),
            _path(
                "effect-interruption",
                terminal=TransactionTerminalState.RECOVERED,
                state_changing=True,
                recovery=RecoveryStrategy.EXACT_RETRY,
            ),
            _path(
                "exact-retry",
                terminal=TransactionTerminalState.RECOVERED,
                state_changing=True,
                recovery=RecoveryStrategy.EXACT_RETRY,
            ),
            _path(
                "duplicate-terminal-retry",
                terminal=TransactionTerminalState.COMMITTED,
                state_changing=False,
                recovery=RecoveryStrategy.NONE,
            ),
            _path(
                "cross-plan-replay",
                terminal=TransactionTerminalState.ROLLED_BACK,
                state_changing=False,
                recovery=RecoveryStrategy.NONE,
            ),
            _path(
                "immutable-record-conflict",
                terminal=TransactionTerminalState.ROLLED_BACK,
                state_changing=False,
                recovery=RecoveryStrategy.NONE,
            ),
        ],
    )


def test_sprint_5_path_manifest_has_executable_coverage() -> None:
    _manifest().assert_complete_coverage(IMPLEMENTED_PATH_IDS)


def test_path_manifest_fails_when_declared_path_is_untested() -> None:
    with pytest.raises(AssertionError, match="missing paths: success"):
        _manifest().assert_complete_coverage(IMPLEMENTED_PATH_IDS - {"success"})


def test_path_manifest_fails_when_test_claims_undeclared_path() -> None:
    with pytest.raises(AssertionError, match="undeclared paths: invented"):
        _manifest().assert_complete_coverage(IMPLEMENTED_PATH_IDS | {"invented"})


def test_test_manifest_requires_explicit_production_effect_prohibition() -> None:
    with pytest.raises(ValidationError, match="prohibit production-effect"):
        OperationPathManifest(
            operation_family="invalid",
            execution_context=ExecutionContext.TEST,
            paths=[
                OperationPathExpectation(
                    path_id="success",
                    description="invalid fixture",
                    expected_terminal_state=TransactionTerminalState.COMMITTED,
                    state_changing=True,
                    recovery_strategy=RecoveryStrategy.NONE,
                )
            ],
        )


def test_path_manifest_rejects_duplicate_ids() -> None:
    path = _path(
        "duplicate",
        terminal=TransactionTerminalState.COMMITTED,
        state_changing=True,
        recovery=RecoveryStrategy.NONE,
    )
    with pytest.raises(ValidationError, match="path ids must be unique"):
        OperationPathManifest(
            operation_family="invalid",
            execution_context=ExecutionContext.TEST,
            paths=[path, path],
        )
