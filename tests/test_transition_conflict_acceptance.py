from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.enki.contracts import SubjectRef
from nks.enki.transitions import (
    ConflictKind,
    StateSnapshot,
    TransitionPayload,
    TransitionType,
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _snapshot(state_id: str) -> StateSnapshot:
    subject = SubjectRef(subject_id="PROJECT-1", subject_type="PROJECT")
    return StateSnapshot(
        state_id=state_id,
        subject=subject,
        domain="operations",
        content_sha256=_hash(state_id),
        observation_ids=[f"OBS-{state_id}"],
        temporal_status="CURRENT",
    )


@pytest.mark.parametrize(
    "conflict",
    [
        ConflictKind.CYCLE,
        ConflictKind.STALE_INPUT,
        ConflictKind.CONTRADICTION,
    ],
)
def test_structural_integrity_conflicts_can_never_be_accepted(
    conflict: ConflictKind,
) -> None:
    source = _snapshot("A")
    target = _snapshot("B")
    with pytest.raises(ValidationError, match="can never be accepted"):
        TransitionPayload(
            transition_id="TR-1",
            transition_type=TransitionType.REFINEMENT,
            subject=source.subject,
            domain=source.domain,
            from_states=[source],
            to_states=[target],
            reason="Attempt to accept an integrity violation.",
            evidence_ids=["E-1"],
            provenance_classification="REAL",
            authority_class="SUBJECT",
            interpretation_version="transition-test/v1",
            required_context=set(),
            accepted_conflicts={conflict},
            occurred_at=datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc),
        )
