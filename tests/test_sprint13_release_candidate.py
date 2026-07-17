import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from nks.application.sprint12_recovery import export_portable_state_recoverable
from nks.application.sprint13_release_candidate import (
    FeedbackDisposition,
    FeedbackEnvelope,
    FeedbackProcessor,
    FeedbackProvenance,
    ProofLaneKind,
    ProofLanePlan,
    ReleaseDecisionRequest,
    ReleaseEvidenceManifest,
    SubjectClass,
    build_release_candidate,
    canonical_sha256,
    execute_test_loop,
)


NOW = datetime(2026, 7, 17, tzinfo=timezone.utc)
COMMIT = "a" * 40


def _hash(label: str) -> str:
    return canonical_sha256(label)


def _history_payload() -> dict:
    return {
        "sequence_contract": "ordered-only",
        "transitions": [
            {
                "transition_id": "tr-1",
                "transition_index": 10,
                "knowledge_id": "K-001",
                "from_state_id": None,
                "to_state_id": "S-001",
                "authoritative": False,
                "state_payload": {"status": "historical"},
                "provenance": {"source": "SRC-001"},
                "evidence_associations": [],
                "lineage": {
                    "parent_state_id": None,
                    "supersedes_state_id": None,
                    "branch_id": "main",
                },
            },
            {
                "transition_id": "tr-2",
                "transition_index": 20,
                "knowledge_id": "K-001",
                "from_state_id": "S-001",
                "to_state_id": "S-002",
                "authoritative": True,
                "state_payload": {"status": "current"},
                "provenance": {"source": "SRC-002"},
                "evidence_associations": [],
                "lineage": {
                    "parent_state_id": "S-001",
                    "supersedes_state_id": "S-001",
                    "branch_id": "main",
                },
            },
        ],
    }


def _portable_archive(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    history_dir = source / "records" / "history"
    history_dir.mkdir(parents=True)
    (history_dir / "transitions.json").write_text(
        json.dumps(_history_payload(), indent=2), encoding="utf-8"
    )
    archive = tmp_path / "portable.zip"
    export_portable_state_recoverable(source, archive)
    return source, archive


def _publication_lane() -> ProofLanePlan:
    return ProofLanePlan(
        lane_id="PUB-TEST-001",
        lane_kind=ProofLaneKind.PUBLICATION,
        subject_class=SubjectClass.PERSON,
        subject_id="PERSON-001",
        purpose="publication-shaped no-effect proof",
        artifact_hashes={
            "content": _hash("content"),
            "configuration": _hash("configuration"),
            "identity": _hash("identity"),
            "byline": _hash("byline"),
            "brand": _hash("brand"),
            "channel": _hash("channel"),
            "review": _hash("review"),
            "visual:hero": _hash("visual"),
        },
        requested_at=NOW,
    )


def _nonpublication_lane() -> ProofLanePlan:
    return ProofLanePlan(
        lane_id="OPS-TEST-001",
        lane_kind=ProofLaneKind.NONPUBLICATION,
        subject_class=SubjectClass.ORGANIZATION,
        subject_id="ORG-001",
        purpose="nonpublication no-effect proof",
        artifact_hashes={"payload": _hash("payload")},
        requested_at=NOW,
    )


def _feedback(
    feedback_id: str,
    provenance: FeedbackProvenance,
    subject_id: str,
    content: str,
    **kwargs,
) -> FeedbackEnvelope:
    return FeedbackEnvelope(
        feedback_id=feedback_id,
        provenance=provenance,
        source_id=f"SRC-{feedback_id}",
        target_subject_id=subject_id,
        content=content,
        content_sha256=canonical_sha256(content),
        received_at=NOW,
        **kwargs,
    )


def test_publication_and_nonpublication_lanes_are_test_only_and_no_effect():
    publication = execute_test_loop(
        _publication_lane(),
        [
            _feedback(
                "FB-SYN-1",
                FeedbackProvenance.SYNTHETIC_TEST,
                "PERSON-001",
                "supportive synthetic response",
            ),
            _feedback(
                "FB-REAL-1",
                FeedbackProvenance.REAL_TEST,
                "PERSON-001",
                "controlled human evaluation",
            ),
        ],
    )
    nonpublication = execute_test_loop(
        _nonpublication_lane(),
        [
            _feedback(
                "FB-REP-1",
                FeedbackProvenance.REPLAY_TEST,
                "ORG-001",
                "immutable replay case",
                replay_of="FB-ARCHIVE-001",
            )
        ],
    )

    assert publication.receipt.execution_context == "TEST"
    assert publication.receipt.external_effect is False
    assert nonpublication.receipt.execution_context == "TEST"
    assert nonpublication.receipt.external_effect is False


def test_production_proof_lane_is_rejected():
    with pytest.raises(ValueError, match="TEST-only"):
        ProofLanePlan(
            lane_id="PUB-PROD-001",
            lane_kind=ProofLaneKind.NONPUBLICATION,
            subject_class=SubjectClass.PROJECT,
            subject_id="PROJECT-001",
            purpose="must fail",
            artifact_hashes={"payload": _hash("payload")},
            requested_at=NOW,
            execution_context="PRODUCTION",
        )


def test_feedback_processor_classifies_duplicate_conflict_and_unauthorized():
    processor = FeedbackProcessor()
    accepted = _feedback(
        "FB-1",
        FeedbackProvenance.SYNTHETIC_TEST,
        "PERSON-001",
        "first",
    )
    duplicate = processor.process("PERSON-001", accepted)
    duplicate_again = processor.process("PERSON-001", accepted)
    conflict = processor.process(
        "PERSON-001",
        _feedback(
            "FB-1",
            FeedbackProvenance.SYNTHETIC_TEST,
            "PERSON-001",
            "different",
        ),
    )
    unauthorized = processor.process(
        "PERSON-001",
        _feedback(
            "FB-2",
            FeedbackProvenance.REAL_TEST,
            "PERSON-001",
            "production-scoped feedback",
            execution_context="PRODUCTION",
        ),
    )

    assert duplicate.disposition == FeedbackDisposition.ACCEPTED
    assert duplicate_again.disposition == FeedbackDisposition.DUPLICATE
    assert conflict.disposition == FeedbackDisposition.CONFLICT
    assert unauthorized.disposition == FeedbackDisposition.UNAUTHORIZED


def test_replay_feedback_requires_immutable_source_reference():
    with pytest.raises(ValueError, match="replay_of"):
        _feedback(
            "FB-REP-INVALID",
            FeedbackProvenance.REPLAY_TEST,
            "ORG-001",
            "replay without source",
        )


def test_zero_response_is_explicit_and_cannot_be_combined_with_feedback():
    processor = FeedbackProcessor()
    result = processor.process_batch("PERSON-001", [], zero_response=True)
    assert result[0].disposition == FeedbackDisposition.ZERO_RESPONSE

    with pytest.raises(ValueError, match="cannot be combined"):
        processor.process_batch(
            "PERSON-001",
            [
                _feedback(
                    "FB-SYN-2",
                    FeedbackProvenance.SYNTHETIC_TEST,
                    "PERSON-001",
                    "response",
                )
            ],
            zero_response=True,
        )


def test_release_candidate_is_hash_bound_and_requires_three_test_provenances(tmp_path: Path):
    source, archive = _portable_archive(tmp_path)
    publication = execute_test_loop(
        _publication_lane(),
        [
            _feedback(
                "FB-SYN-3",
                FeedbackProvenance.SYNTHETIC_TEST,
                "PERSON-001",
                "synthetic",
            ),
            _feedback(
                "FB-REAL-3",
                FeedbackProvenance.REAL_TEST,
                "PERSON-001",
                "human",
            ),
        ],
    )
    nonpublication = execute_test_loop(
        _nonpublication_lane(),
        [
            _feedback(
                "FB-REP-3",
                FeedbackProvenance.REPLAY_TEST,
                "ORG-001",
                "replay",
                replay_of="FB-ARCHIVE-003",
            )
        ],
    )
    evidence = ReleaseEvidenceManifest.from_paths(
        [source / "records" / "history" / "transitions.json"], root=source
    )

    candidate = build_release_candidate(
        version="enki-0.1.0-rc1",
        implementation_commit=COMMIT,
        portable_archive=archive,
        evidence_manifest=evidence,
        loop_results=[publication, nonpublication],
    )

    assert candidate.production_authorized is False
    assert candidate.status.value == "READY_FOR_HUMAN_DECISION"
    assert set(candidate.feedback_provenance) == {
        FeedbackProvenance.SYNTHETIC_TEST,
        FeedbackProvenance.REPLAY_TEST,
        FeedbackProvenance.REAL_TEST,
    }
    assert len(set(candidate.subject_classes)) == 2


def test_release_candidate_rejects_missing_real_test_feedback(tmp_path: Path):
    source, archive = _portable_archive(tmp_path)
    publication = execute_test_loop(
        _publication_lane(),
        [
            _feedback(
                "FB-SYN-4",
                FeedbackProvenance.SYNTHETIC_TEST,
                "PERSON-001",
                "synthetic",
            )
        ],
    )
    nonpublication = execute_test_loop(
        _nonpublication_lane(),
        [
            _feedback(
                "FB-REP-4",
                FeedbackProvenance.REPLAY_TEST,
                "ORG-001",
                "replay",
                replay_of="FB-ARCHIVE-004",
            )
        ],
    )
    evidence = ReleaseEvidenceManifest.from_paths(
        [source / "records" / "history" / "transitions.json"], root=source
    )

    with pytest.raises(ValueError, match="REAL/TEST"):
        build_release_candidate(
            version="enki-0.1.0-rc1",
            implementation_commit=COMMIT,
            portable_archive=archive,
            evidence_manifest=evidence,
            loop_results=[publication, nonpublication],
        )


def test_release_evidence_manifest_is_deterministic(tmp_path: Path):
    root = tmp_path / "evidence"
    root.mkdir()
    a = root / "a.txt"
    b = root / "b.txt"
    a.write_text("A", encoding="utf-8")
    b.write_text("B", encoding="utf-8")

    first = ReleaseEvidenceManifest.from_paths([a, b], root=root)
    second = ReleaseEvidenceManifest.from_paths([b, a], root=root)

    assert first == second
    assert first.manifest_sha256 == second.manifest_sha256


def test_release_decision_request_remains_unresolved_by_machine():
    request = ReleaseDecisionRequest(
        candidate_sha256=_hash("candidate"),
        requested_at=NOW,
        requested_from="human-governing-authority",
    )

    assert request.decision is None
    assert request.options == ["APPROVE", "APPROVE_WITH_CONDITIONS", "DEFER", "REJECT"]
