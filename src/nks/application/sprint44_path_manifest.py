from __future__ import annotations
from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext

def _p(path_id: str, denied: bool=False, recovered: bool=False):
    return OperationPathExpectation(
        path_id=path_id,
        description=path_id.replace("-", " "),
        expected_terminal_state=(TransactionTerminalState.ROLLED_BACK if denied else TransactionTerminalState.RECOVERED if recovered else TransactionTerminalState.COMMITTED),
        state_changing=False,
        recovery_strategy=RecoveryStrategy.EXACT_RETRY if recovered else RecoveryStrategy.NONE,
        prohibited_effects=["production-effect","authority-widening","noncanonical-promotion"],
    )

def sprint44_provider_exit_path_manifest() -> OperationPathManifest:
    names = [
        "coordinated-state-object-backup","point-in-time-backup","open-deterministic-export",
        "independent-manifest-verification","authority-semantics-preserved","policy-consent-temporal-lineage-preserved",
        "receipts-preserved","noncanonical-artifacts-inventoried-not-restored",
    ]
    paths=[_p(name) for name in names]
    paths += [_p("clean-room-exact-restore", recovered=True),_p("source-provider-outage-restore", recovered=True),_p("provider-exit-to-independent-destination", recovered=True),_p("recovery-retry-deterministic", recovered=True)]
    paths += [_p("tampered-manifest-denied", denied=True),_p("interrupted-after-state-rolls-back", denied=True),_p("interrupted-after-objects-rolls-back", denied=True),_p("projection-cannot-become-canonical", denied=True),_p("cache-cannot-become-canonical", denied=True),_p("replica-cannot-become-canonical", denied=True),_p("test-proof-cannot-claim-real-provider-validation", denied=True)]
    return OperationPathManifest(operation_family="enki-provider-exit-recovery",execution_context=ExecutionContext.TEST,paths=paths)
