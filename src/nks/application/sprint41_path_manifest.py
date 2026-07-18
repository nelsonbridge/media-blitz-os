from __future__ import annotations
from nks.application.governed_transactions import RecoveryStrategy, TransactionTerminalState
from nks.application.path_manifest import OperationPathExpectation, OperationPathManifest
from nks.governance.approvals import ExecutionContext

def _p(path_id:str,denied:bool=False,recovered:bool=False):
    return OperationPathExpectation(
        path_id=path_id,description=path_id.replace("-"," "),state_changing=False,
        expected_terminal_state=TransactionTerminalState.ROLLED_BACK if denied else TransactionTerminalState.RECOVERED if recovered else TransactionTerminalState.COMMITTED,
        recovery_strategy=RecoveryStrategy.EXACT_RETRY if recovered else RecoveryStrategy.NONE,
        prohibited_effects=["production-effect","object-store-authority","direct-canonical-write","orphan-evidence","noncanonical-promotion"],
    )

def sprint41_evidence_object_plane_path_manifest()->OperationPathManifest:
    paths=[_p(x) for x in [
        "evidence-canonical-hash-link","provider-key-nonauthoritative","publication-manifest-deterministic",
        "model-use-manifest-deterministic","audit-manifest-deterministic","export-manifest-deterministic",
        "backup-manifest-deterministic","recovery-manifest-deterministic","archive-history-preserved",
        "tombstone-history-preserved","deletion-history-preserved","portable-export-deterministic",
        "clean-room-relationship-reconstruction","exact-provider-independent-logical-identity",
    ]]
    paths += [_p(x,denied=True) for x in [
        "orphan-evidence-denied","object-corruption-denied","missing-object-denied","manifest-tamper-denied",
        "illegal-lifecycle-transition-denied","deleted-content-cannot-reappear-as-authority","provider-object-key-cannot-become-authority",
    ]]
    paths += [_p("portable-clean-room-import",recovered=True)]
    return OperationPathManifest(operation_family="enki-evidence-object-plane",execution_context=ExecutionContext.TEST,paths=paths)
