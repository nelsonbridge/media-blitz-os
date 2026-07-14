from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nks.application.governed_transactions import canonical_sha256
from nks.application.integrated_test_proof import (
    EnkiReleaseCandidate,
    ReleaseCandidateStatus,
)
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "releases" / "enki-0.1.0-rc1"


ARTIFACT_FILES = {
    "calibration-report": "calibration-report.md",
    "evidence-manifest": "evidence-manifest.md",
    "human-release-decision": "human-release-decision.md",
    "known-limitations": "known-limitations.md",
    "nonpublication-loop-receipt-file": "nonpublication-loop-receipt.json",
    "publication-loop-receipt-file": "publication-loop-receipt.json",
    "release-notes": "release-notes.md",
    "rollback-package": "rollback-package.md",
    "runbook": "runbook.md",
    "threat-model": "threat-model.md",
}


def _file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_release_candidate_and_all_artifact_hashes_are_exact() -> None:
    candidate = EnkiReleaseCandidate.model_validate_json(
        (RELEASE / "release-candidate.json").read_text(encoding="utf-8")
    )

    assert candidate.status == ReleaseCandidateStatus.READY_FOR_HUMAN_DECISION
    assert candidate.external_effect is False
    assert candidate.manifest.execution_context == ExecutionContext.TEST
    assert candidate.manifest.source_commit_sha == (
        "cb84fbc8eef6096e8a707e1b922dfa2eddb23e51"
    )
    assert candidate.candidate_sha256 == canonical_sha256(candidate.manifest)
    assert set(candidate.manifest.artifact_hashes) == set(ARTIFACT_FILES)

    for artifact_id, filename in ARTIFACT_FILES.items():
        assert candidate.manifest.artifact_hashes[artifact_id] == _file_sha256(
            RELEASE / filename
        )


def test_adaptive_loop_receipts_are_self_hashing_no_effect_test_evidence() -> None:
    receipt_hashes: set[str] = set()
    lane_kinds: set[str] = set()

    for filename in (
        "publication-loop-receipt.json",
        "nonpublication-loop-receipt.json",
    ):
        payload = json.loads((RELEASE / filename).read_text(encoding="utf-8"))
        claimed = payload.pop("receipt_sha256")
        assert claimed == canonical_sha256(payload)
        assert payload["execution_context"] == "TEST"
        assert payload["external_effect"] is False
        assert payload["terminal_state"] == "COMMITTED"
        assert payload["reconstruction_status"] == "COMPLETE"
        receipt_hashes.add(claimed)
        lane_kinds.add(payload["lane_kind"])

    candidate = EnkiReleaseCandidate.model_validate_json(
        (RELEASE / "release-candidate.json").read_text(encoding="utf-8")
    )
    assert receipt_hashes == set(candidate.manifest.loop_receipt_hashes)
    assert lane_kinds == {"PUBLICATION", "NONPUBLICATION"}


def test_human_decision_request_remains_unresolved_and_nonproduction() -> None:
    decision = (RELEASE / "human-release-decision.md").read_text(encoding="utf-8")

    assert "Decision: **Not recorded**" in decision
    assert "Decided by: **Not recorded**" in decision
    assert "The system cannot issue this decision on its own" in decision
    assert "does not authorize production operation" in decision
