import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from nks.application.sprint13_hardening import (
    ChaosDrillName,
    HardeningReport,
    ReleaseArtifactBundle,
    build_release_artifact_bundle,
    execute_recovery_chaos_drills,
    write_release_artifact_bundle,
)
from nks.application.sprint13_release_candidate import (
    FeedbackProvenance,
    ReleaseCandidate,
    ReleaseDecisionRequest,
    SubjectClass,
    canonical_sha256,
)


NOW = datetime(2026, 7, 17, tzinfo=timezone.utc)


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


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    history = source / "records" / "history"
    history.mkdir(parents=True)
    (history / "transitions.json").write_text(
        json.dumps(_history_payload(), indent=2),
        encoding="utf-8",
    )
    (source / "events").mkdir()
    (source / "events" / "EVT-001.json").write_text(
        json.dumps({"event_id": "EVT-001", "type": "test"}),
        encoding="utf-8",
    )
    return source


def _candidate() -> ReleaseCandidate:
    return ReleaseCandidate(
        version="enki-0.1.0-rc1",
        implementation_commit="b" * 40,
        portable_package_sha256=canonical_sha256("portable-package"),
        evidence_manifest_sha256=canonical_sha256("evidence-manifest"),
        lane_result_sha256s=[canonical_sha256("lane-1"), canonical_sha256("lane-2")],
        subject_classes=[SubjectClass.PERSON, SubjectClass.ORGANIZATION],
        feedback_provenance=[
            FeedbackProvenance.SYNTHETIC_TEST,
            FeedbackProvenance.REPLAY_TEST,
            FeedbackProvenance.REAL_TEST,
        ],
    )


def test_sprint13_chaos_drills_recover_without_effect_or_authority_escalation(tmp_path: Path):
    candidate = _candidate()
    report = execute_recovery_chaos_drills(
        source_root=_source(tmp_path),
        work_root=tmp_path / "chaos",
        candidate_sha256=canonical_sha256(candidate),
    )

    assert report.all_passed is True
    assert {item.drill for item in report.drills} == set(ChaosDrillName)
    assert all(item.passed and item.recovered for item in report.drills)
    assert all(item.external_effect is False for item in report.drills)
    assert all(item.authority_escalated is False for item in report.drills)
    assert all(item.duplicate_effect is False for item in report.drills)


def test_hardening_report_is_deterministic_for_identical_drill_evidence(tmp_path: Path):
    candidate = _candidate()
    first = execute_recovery_chaos_drills(
        source_root=_source(tmp_path),
        work_root=tmp_path / "first",
        candidate_sha256=canonical_sha256(candidate),
    )
    second = execute_recovery_chaos_drills(
        source_root=tmp_path / "source",
        work_root=tmp_path / "second",
        candidate_sha256=canonical_sha256(candidate),
    )

    assert first.report_sha256 == second.report_sha256
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_release_artifact_bundle_preserves_human_only_production_gate(tmp_path: Path):
    candidate = _candidate()
    report = execute_recovery_chaos_drills(
        source_root=_source(tmp_path),
        work_root=tmp_path / "chaos",
        candidate_sha256=canonical_sha256(candidate),
    )
    bundle = build_release_artifact_bundle(
        candidate=candidate,
        hardening_report=report,
        generated_at=NOW,
        requested_from="human-governing-authority",
    )

    assert bundle.candidate.production_authorized is False
    assert bundle.decision_request.decision is None
    assert bundle.production_readiness["production_approval_status"] == "PENDING_HUMAN_DECISION"
    assert "no production validation is claimed" in bundle.limitations["limitations"]
    assert "production transport authorization" in bundle.production_readiness["remaining_sprint3_ownership"]


def test_release_artifact_bundle_rejects_false_production_approval(tmp_path: Path):
    candidate = _candidate()
    report = execute_recovery_chaos_drills(
        source_root=_source(tmp_path),
        work_root=tmp_path / "chaos",
        candidate_sha256=canonical_sha256(candidate),
    )
    request = ReleaseDecisionRequest(
        candidate_sha256=canonical_sha256(candidate),
        requested_at=NOW,
        requested_from="human-governing-authority",
    )

    with pytest.raises(ValueError, match="pending human decision"):
        ReleaseArtifactBundle(
            candidate=candidate,
            hardening_report=report,
            threat_model={"execution_context": "TEST"},
            runbook={"gate": "human"},
            limitations={"limitations": []},
            rollback_package={"procedure": []},
            release_notes={"status": "READY_FOR_HUMAN_DECISION"},
            production_readiness={"production_approval_status": "APPROVED"},
            decision_request=request,
        )


def test_release_artifact_writer_is_deterministic_and_hash_bound(tmp_path: Path):
    candidate = _candidate()
    report = execute_recovery_chaos_drills(
        source_root=_source(tmp_path),
        work_root=tmp_path / "chaos",
        candidate_sha256=canonical_sha256(candidate),
    )
    bundle = build_release_artifact_bundle(
        candidate=candidate,
        hardening_report=report,
        generated_at=NOW,
        requested_from="human-governing-authority",
    )

    first_root = tmp_path / "release-a"
    second_root = tmp_path / "release-b"
    first = write_release_artifact_bundle(bundle, first_root)
    second = write_release_artifact_bundle(bundle, second_root)

    assert first == second
    assert first.manifest_sha256 == second.manifest_sha256
    assert sorted(first.files) == [
        "hardening-report.json",
        "limitations.json",
        "production-readiness.json",
        "release-candidate.json",
        "release-decision-request.json",
        "release-notes.json",
        "rollback-package.json",
        "runbook.json",
        "threat-model.json",
    ]
    assert (first_root / "evidence-manifest.json").exists()
    assert json.loads((first_root / "release-candidate.json").read_text(encoding="utf-8"))[
        "production_authorized"
    ] is False
