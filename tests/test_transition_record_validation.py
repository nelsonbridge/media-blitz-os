from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from nks.enki.contracts import SubjectRef
from nks.enki.transitions import (
    StateSnapshot,
    TransitionRecord,
    TransitionType,
)
from nks.governance.approvals import ExecutionContext
from nks.validation.transition_records import validate_transition_record


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _snapshot(state_id: str) -> StateSnapshot:
    return StateSnapshot(
        state_id=state_id,
        subject=SubjectRef(subject_id="PROJECT-1", subject_type="PROJECT"),
        domain="operations",
        content_sha256=_hash(state_id),
        observation_ids=[f"OBS-{state_id}"],
        temporal_status="CURRENT",
    )


def _transition() -> TransitionRecord:
    source = _snapshot("A")
    target = _snapshot("B")
    return TransitionRecord(
        transition_id="TR-1",
        transition_type=TransitionType.REFINEMENT,
        subject=source.subject,
        domain=source.domain,
        from_states=[source],
        to_states=[target],
        before_sha256=_hash("before"),
        after_sha256=_hash("after"),
        reason="Refine the recorded state.",
        evidence_ids=["E-1"],
        provenance_classification="REAL",
        authority_class="SUBJECT",
        interpretation_version="transition-test/v1",
        execution_context=ExecutionContext.TEST,
        transaction_id="TX-1",
        occurred_at=datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc),
    )


def test_valid_snapshot_and_transition_records_pass_runtime_validation() -> None:
    snapshot = _snapshot("A")
    transition = _transition()

    assert validate_transition_record(
        "enki-state-snapshots",
        snapshot.model_dump(mode="json"),
    ) == []
    assert validate_transition_record(
        "enki-transitions",
        transition.model_dump(mode="json"),
    ) == []


def test_malformed_snapshot_reports_deterministic_violations() -> None:
    payload = _snapshot("A").model_dump(mode="json")
    payload["content_sha256"] = "not-a-hash"
    payload["observation_ids"] = []

    violations = validate_transition_record("enki-state-snapshots", payload)

    assert any(item.startswith("content_sha256:") for item in violations)
    assert any("a state snapshot must reference canonical state" in item for item in violations)


def test_malformed_transition_reports_unknown_enum_and_missing_subject() -> None:
    payload = _transition().model_dump(mode="json")
    payload["transition_type"] = "INVENTED"
    payload.pop("subject")

    violations = validate_transition_record("enki-transitions", payload)

    assert any(item.startswith("subject:") for item in violations)
    assert any(item.startswith("transition_type:") for item in violations)


def test_unknown_collection_is_not_silently_reinterpreted() -> None:
    assert validate_transition_record("other-records", {"anything": True}) == []
