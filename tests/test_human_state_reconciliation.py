from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

import pytest

from nks.application.human_state_reconciliation import ReconcileHumanState
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    HumanStateTransition,
    TemporalStatus,
    TransitionOrigin,
    TransitionType,
)
from nks.enki.contracts import ExpressionOrigin, FindingKind
from nks.enki.reconciliation import ReconciliationEngine, RelationshipFindingStrategy


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _observation(observation_id: str, content: str, now: datetime) -> HumanStateObservation:
    return HumanStateObservation(
        observation_id=observation_id,
        subject_id="PERSON-1",
        content=content,
        content_hash=_hash(content),
        domain="career",
        state_type="decision-context",
        provenance="REAL",
        source_id=f"SOURCE-{observation_id}",
        observed_at=now,
        effective_from=date(2026, 7, 13),
        expression_strength=ExpressionStrength.EXPLICIT,
        confidence="HIGH",
        temporal_status=TemporalStatus.CURRENT,
    )


class MemoryHumanStateReader:
    def __init__(
        self,
        observations: list[HumanStateObservation],
        transitions: list[HumanStateTransition],
    ) -> None:
        self._observations = observations
        self._transitions = transitions

    def list_observations(self, subject_id: str, domain: str) -> list[HumanStateObservation]:
        return [
            item
            for item in self._observations
            if item.subject_id == subject_id and item.domain == domain
        ]

    def list_transitions(self, subject_id: str, domain: str) -> list[HumanStateTransition]:
        return [
            item
            for item in self._transitions
            if item.subject_id == subject_id and item.domain == domain
        ]


def test_human_state_records_run_through_enki_without_objective_substitution() -> None:
    now = datetime(2026, 7, 13, 10, 0, tzinfo=timezone.utc)
    first = _observation("HOBS-1", "Promotion remains an objective.", now)
    second = _observation("HOBS-2", "Promotion is not currently available here.", now)
    transition = HumanStateTransition(
        transition_id="HTR-1",
        subject_id="PERSON-1",
        domain="career",
        from_observation_id=first.observation_id,
        to_observation_id=second.observation_id,
        transition_type=TransitionType.UNRESOLVED_CONTRADICTION,
        origin=TransitionOrigin.HUMAN_REVIEWED,
        detected_at=now,
        durability="current",
        reversibility="revisable",
        confidence="HIGH",
    )
    reader = MemoryHumanStateReader([first, second], [transition])
    use_case = ReconcileHumanState(
        reader,
        ReconciliationEngine(
            RelationshipFindingStrategy(),
            interpretation_version="enki-human-compat/v1",
        ),
    )

    result = use_case.execute(
        subject_id="PERSON-1",
        domain="career",
        expression_origins={
            "HOBS-1": ExpressionOrigin.SELF_DECLARED,
            "HOBS-2": ExpressionOrigin.OBSERVED,
        },
        objective_refs=["OBJ-PROMOTION"],
        priority_refs=["PRI-INCOME", "PRI-FAMILY-TIME"],
        as_of=now,
    )

    assert result.findings[0].finding_kind == FindingKind.UNCERTAINTY
    assert result.findings[0].objective_refs == ["OBJ-PROMOTION"]
    assert result.findings[0].priority_refs == ["PRI-INCOME", "PRI-FAMILY-TIME"]
    assert result.interpretation_version == "enki-human-compat/v1"


def test_human_state_reconciliation_fails_closed_when_origin_is_unknown() -> None:
    now = datetime(2026, 7, 13, 10, 0, tzinfo=timezone.utc)
    observation = _observation("HOBS-1", "Promotion remains an objective.", now)
    use_case = ReconcileHumanState(
        MemoryHumanStateReader([observation], []),
        ReconciliationEngine(
            RelationshipFindingStrategy(),
            interpretation_version="enki-human-compat/v1",
        ),
    )

    with pytest.raises(ValueError, match="expression origin is required"):
        use_case.execute(
            subject_id="PERSON-1",
            domain="career",
            expression_origins={},
            as_of=now,
        )


def test_human_state_reconciliation_requires_at_least_one_observation() -> None:
    now = datetime(2026, 7, 13, 10, 0, tzinfo=timezone.utc)
    use_case = ReconcileHumanState(
        MemoryHumanStateReader([], []),
        ReconciliationEngine(
            RelationshipFindingStrategy(),
            interpretation_version="enki-human-compat/v1",
        ),
    )

    with pytest.raises(ValueError, match="no human-state observations"):
        use_case.execute(
            subject_id="PERSON-1",
            domain="career",
            expression_origins={},
            as_of=now,
        )
