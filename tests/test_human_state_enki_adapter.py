from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from nks.adapters.human_state_enki import project_human_observation, project_human_transition
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    HumanStateTransition,
    TemporalStatus as HumanTemporalStatus,
    TransitionOrigin,
    TransitionType,
)
from nks.enki.contracts import ConfidenceLevel, ExpressionOrigin, TemporalStatus


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_human_observation_projection_requires_explicit_origin_choice() -> None:
    now = datetime(2026, 7, 13, 9, 0, tzinfo=timezone.utc)
    record = HumanStateObservation(
        observation_id="HOBS-1",
        subject_id="PERSON-1",
        content="I intend to pursue promotion.",
        content_hash=_hash("I intend to pursue promotion."),
        domain="career",
        state_type="objective",
        provenance="REAL",
        source_id="CONVERSATION-1",
        observed_at=now,
        effective_from=date(2026, 7, 13),
        context=["current-role"],
        expression_strength=ExpressionStrength.EXPLICIT,
        confidence="HIGH",
        temporal_status=HumanTemporalStatus.CURRENT,
    )

    projected = project_human_observation(
        record,
        expression_origin=ExpressionOrigin.SELF_DECLARED,
    )

    assert projected.subject.subject_type == "PERSON"
    assert projected.expression_origin == ExpressionOrigin.SELF_DECLARED
    assert projected.temporal_status == TemporalStatus.CURRENT
    assert projected.confidence.level == ConfidenceLevel.HIGH
    assert projected.evidence[0].source_id == "CONVERSATION-1"
    assert projected.metadata["legacy_expression_strength"] == "EXPLICIT"


def test_transition_projection_does_not_promote_legacy_boolean_approval() -> None:
    now = datetime(2026, 7, 13, 9, 0, tzinfo=timezone.utc)
    record = HumanStateTransition(
        transition_id="HTR-1",
        subject_id="PERSON-1",
        domain="career",
        from_observation_id="HOBS-1",
        to_observation_id="HOBS-2",
        transition_type=TransitionType.REFINEMENT,
        origin=TransitionOrigin.HUMAN_REVIEWED,
        detected_at=now,
        stated_reason="The objective was clarified.",
        durability="persistent",
        reversibility="revisable",
        confidence="HIGH",
        approved_for_model_feedback=True,
        approved_by="STEWARD-1",
    )

    projected = project_human_transition(record)

    assert projected.relationship_type == "REFINEMENT"
    assert projected.confidence.level == ConfidenceLevel.UNKNOWN
    assert "approved_for_model_feedback" not in projected.metadata
    assert "approved_by" not in projected.metadata
    assert "governed approval must be evaluated separately" in projected.metadata["authority_note"]
