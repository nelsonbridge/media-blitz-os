"""Machine-readable path matrix for Sprint 13 integrated TEST proof."""

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
        prohibited_effects=[
            "production-effect",
            "external-publication",
            "external-model-dispatch",
            "audience-widening",
            "authority-escalation",
        ],
    )


def sprint13_path_manifest() -> OperationPathManifest:
    rollback = TransactionTerminalState.ROLLED_BACK
    recovered = TransactionTerminalState.RECOVERED
    return OperationPathManifest(
        operation_family="enki-integrated-test-proof-release-candidate",
        execution_context=ExecutionContext.TEST,
        paths=[
            _path("publication-loop-success", state_changing=True),
            _path("nonpublication-loop-success", state_changing=True),
            _path("publication-missing-artifact", terminal=rollback),
            _path("publication-no-visual", terminal=rollback),
            _path("nonpublication-missing-payload", terminal=rollback),
            _path("production-context-denied", terminal=rollback),
            _path("plan-tamper-denied", terminal=rollback),
            _path("cross-plan-replay-denied", terminal=rollback),
            _path("duplicate-effect-idempotent", state_changing=True),
            _path("interruption-before-consumption", terminal=rollback, recovery=RecoveryStrategy.RELEASE_RESERVATION),
            _path("interruption-after-effect", terminal=recovered, state_changing=True, recovery=RecoveryStrategy.EXACT_RETRY),
            _path("synthetic-feedback-accepted"),
            _path("controlled-real-test-feedback-accepted"),
            _path("replay-feedback-attributed"),
            _path("replay-feedback-missing-origin", terminal=rollback),
            _path("duplicate-feedback"),
            _path("conflicting-feedback-id", terminal=rollback),
            _path("irrelevant-feedback"),
            _path("malformed-feedback", terminal=rollback),
            _path("contradictory-feedback"),
            _path("adversarial-feedback", terminal=rollback),
            _path("unauthorized-feedback", terminal=rollback),
            _path("mismatched-feedback", terminal=rollback),
            _path("zero-response-window"),
            _path("forensic-reconstruction-complete"),
            _path("forensic-reconstruction-tamper", terminal=rollback),
            _path("release-candidate-two-lane"),
            _path("release-candidate-single-lane-denied", terminal=rollback),
            _path("release-candidate-missing-artifact", terminal=rollback),
            _path("release-candidate-bad-commit", terminal=rollback),
            _path("release-candidate-hash-tamper", terminal=rollback),
            _path("release-decision-human-only"),
            _path("test-evidence-cannot-satisfy-production", terminal=rollback),
        ],
    )
