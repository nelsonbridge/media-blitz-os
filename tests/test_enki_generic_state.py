from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from nks.adapters.enki_state import EnkiStateConflictError, JsonEnkiStateRepository
from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    EvidenceRef,
    ExpressionOrigin,
    Observation,
    ReconciliationRequest,
    ReferenceKind,
    RelationshipAssertion,
    SubjectRef,
    TemporalApplicability,
    TemporalStatus,
)
from nks.enki.reconciliation import ReconciliationEngine, RelationshipFindingStrategy


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _state(subject_type: str, suffix: str):
    now = datetime(2026, 7, 14, 11, 0, tzinfo=timezone.utc)
    subject = SubjectRef(
        subject_id=f"{subject_type}-{suffix}",
        subject_type=subject_type,
    )
    evidence = EvidenceRef(
        evidence_id=f"E-{suffix}",
        source_id=f"SOURCE-{suffix}",
        content_hash=_hash(f"evidence-{suffix}"),
        observed_at=now,
        provenance_classification="REAL",
    )
    confidence = ConfidenceAssertion(
        level=ConfidenceLevel.HIGH,
        rationale="Supported by attributable evidence.",
        evidence_ids=[evidence.evidence_id],
    )
    observation = Observation(
        observation_id=f"OBS-{suffix}",
        subject=subject,
        domain="operating-alignment",
        statement="The recorded decision diverges from the supplied objective.",
        content_hash=_hash(f"statement-{suffix}"),
        evidence=[evidence],
        observed_at=now,
        applicability=TemporalApplicability(effective_from=date(2026, 7, 1)),
        context=["test-fixture"],
        expression_origin=ExpressionOrigin.OBSERVED,
        confidence=confidence,
        temporal_status=TemporalStatus.CURRENT,
    )
    relationship = RelationshipAssertion(
        relationship_id=f"REL-{suffix}",
        subject=subject,
        domain="operating-alignment",
        source_kind=ReferenceKind.OBSERVATION,
        source_id=observation.observation_id,
        target_kind=ReferenceKind.OBJECTIVE,
        target_id=f"OBJ-{suffix}",
        relationship_type="DIVERGES_FROM",
        evidence=[evidence],
        confidence=confidence,
        observed_at=now,
        applicability=TemporalApplicability(effective_from=date(2026, 7, 1)),
        context=["test-fixture"],
    )
    return subject, observation, relationship


@pytest.mark.parametrize(
    ("subject_type", "suffix"),
    [
        ("PERSON", "PERSON-1"),
        ("ORGANIZATION", "ORG-1"),
        ("PROJECT", "PROJECT-1"),
    ],
)
def test_same_repository_and_engine_support_subject_classes_without_forks(
    tmp_path: Path,
    subject_type: str,
    suffix: str,
) -> None:
    subject, observation, relationship = _state(subject_type, suffix)
    repository = JsonEnkiStateRepository(tmp_path)
    repository.append_observations([observation])
    repository.append_relationships([relationship])

    request = ReconciliationRequest(
        subject=subject,
        domain="operating-alignment",
        observations=repository.list_observations(subject, "operating-alignment"),
        relationships=repository.list_relationships(subject, "operating-alignment"),
        objective_refs=[relationship.target_id],
        priority_refs=[],
        as_of=observation.observed_at,
    )
    result = ReconciliationEngine(
        RelationshipFindingStrategy(),
        interpretation_version="generic-substrate-test/v1",
    ).execute(request)

    assert len(result.findings) == 1
    assert result.findings[0].subject.subject_type == subject_type
    assert result.findings[0].objective_refs == [relationship.target_id]
    assert type(repository.get_observation(observation.observation_id)) is Observation
    assert type(repository.get_relationship(relationship.relationship_id)) is RelationshipAssertion


def test_subject_classes_share_the_same_collections(tmp_path: Path) -> None:
    repository = JsonEnkiStateRepository(tmp_path)
    fixtures = [
        _state("PERSON", "P"),
        _state("ORGANIZATION", "O"),
        _state("PROJECT", "R"),
    ]

    repository.append_observations(item[1] for item in fixtures)
    repository.append_relationships(item[2] for item in fixtures)

    assert len(list((tmp_path / "records" / "enki-observations").glob("*.json"))) == 3
    assert len(list((tmp_path / "records" / "relationship-assertions").glob("*.json"))) == 3
    assert not (tmp_path / "records" / "person-observations").exists()
    assert not (tmp_path / "records" / "organization-observations").exists()
    assert not (tmp_path / "records" / "project-observations").exists()


def test_generic_state_records_are_append_only_and_idempotent(tmp_path: Path) -> None:
    _, observation, relationship = _state("ORGANIZATION", "ORG")
    repository = JsonEnkiStateRepository(tmp_path)

    repository.append_observations([observation])
    repository.append_observations([observation])
    repository.append_relationships([relationship])
    repository.append_relationships([relationship])

    changed = observation.model_copy(update={"statement": "Different statement."})
    with pytest.raises(EnkiStateConflictError, match="different content"):
        repository.append_observations([changed])
