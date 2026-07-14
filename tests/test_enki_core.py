from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    EvidenceRef,
    ExpressionOrigin,
    FindingKind,
    Observation,
    ReconciliationFinding,
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


def _confidence(level: ConfidenceLevel = ConfidenceLevel.HIGH) -> ConfidenceAssertion:
    return ConfidenceAssertion(
        level=level,
        rationale="Supported by attributable evidence.",
        evidence_ids=["E-1"],
    )


def _request(relationship_type: str = "DIVERGES_FROM") -> ReconciliationRequest:
    now = datetime(2026, 7, 13, 8, 0, tzinfo=timezone.utc)
    subject = SubjectRef(subject_id="SUBJECT-1", subject_type="PERSON")
    evidence = EvidenceRef(
        evidence_id="E-1",
        source_id="SOURCE-1",
        content_hash=_hash("evidence"),
        observed_at=now,
        provenance_classification="REAL",
    )
    first = Observation(
        observation_id="OBS-1",
        subject=subject,
        domain="career",
        statement="Promotion is a stated objective.",
        content_hash=_hash("Promotion is a stated objective."),
        evidence=[evidence],
        observed_at=now,
        applicability=TemporalApplicability(effective_from=date(2026, 1, 1)),
        expression_origin=ExpressionOrigin.SELF_DECLARED,
        confidence=_confidence(),
        temporal_status=TemporalStatus.CURRENT,
    )
    second = Observation(
        observation_id="OBS-2",
        subject=subject,
        domain="career",
        statement="Current organizational conditions do not support promotion.",
        content_hash=_hash("Current organizational conditions do not support promotion."),
        evidence=[evidence],
        observed_at=now,
        applicability=TemporalApplicability(effective_from=date(2026, 1, 1)),
        expression_origin=ExpressionOrigin.OBSERVED,
        confidence=_confidence(),
        temporal_status=TemporalStatus.CURRENT,
    )
    relationship = RelationshipAssertion(
        relationship_id="REL-1",
        subject=subject,
        domain="career",
        source_kind=ReferenceKind.OBSERVATION,
        source_id=first.observation_id,
        target_kind=ReferenceKind.OBSERVATION,
        target_id=second.observation_id,
        relationship_type=relationship_type,
        evidence=[evidence],
        confidence=_confidence(),
        observed_at=now,
        applicability=TemporalApplicability(effective_from=date(2026, 1, 1)),
    )
    return ReconciliationRequest(
        subject=subject,
        domain="career",
        observations=[first, second],
        relationships=[relationship],
        objective_refs=["OBJ-PROMOTION"],
        priority_refs=["PRI-INCOME", "PRI-FAMILY-TIME"],
        as_of=now,
    )


def test_relationship_strategy_surfaces_divergence_without_reordering_priorities() -> None:
    request = _request()
    engine = ReconciliationEngine(
        RelationshipFindingStrategy(),
        interpretation_version="enki-test/v1",
    )

    result = engine.execute(request)

    assert result.unresolved_observation_ids == []
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.finding_kind == FindingKind.DIVERGENCE
    assert finding.objective_refs == request.objective_refs
    assert finding.priority_refs == request.priority_refs
    assert finding.interpretation_version == "enki-test/v1"
    assert "recommendation" not in ReconciliationFinding.model_fields


def test_unknown_relationship_remains_uncertain() -> None:
    request = _request("MAY_AFFECT")
    engine = ReconciliationEngine(
        RelationshipFindingStrategy(),
        interpretation_version="enki-test/v1",
    )

    result = engine.execute(request)

    assert result.findings[0].finding_kind == FindingKind.UNCERTAINTY


def test_unknown_observation_reference_fails_closed() -> None:
    request = _request()
    request.relationships[0].target_id = "OBS-MISSING"
    engine = ReconciliationEngine(
        RelationshipFindingStrategy(),
        interpretation_version="enki-test/v1",
    )

    with pytest.raises(ValueError, match="unknown observation reference"):
        engine.execute(request)


def test_hidden_objective_substitution_fails_closed() -> None:
    request = _request()

    class SubstitutingStrategy:
        def reconcile(self, supplied: ReconciliationRequest) -> list[ReconciliationFinding]:
            relationship = supplied.relationships[0]
            return [
                ReconciliationFinding(
                    finding_id="RF-HIDDEN",
                    subject=supplied.subject,
                    domain=supplied.domain,
                    finding_kind=FindingKind.DIVERGENCE,
                    summary="Attempts to substitute an objective not supplied by the user.",
                    observation_ids=["OBS-1", "OBS-2"],
                    relationship_ids=[relationship.relationship_id],
                    evidence_ids=["E-1"],
                    objective_refs=["OBJ-HIDDEN"],
                    priority_refs=list(supplied.priority_refs),
                    confidence=_confidence(),
                    created_at=supplied.as_of,
                    interpretation_version="substituting/v1",
                )
            ]

    engine = ReconciliationEngine(
        SubstitutingStrategy(),
        interpretation_version="enki-test/v1",
    )

    with pytest.raises(ValueError, match="hidden objective substitution"):
        engine.execute(request)


def test_enki_package_does_not_import_product_or_human_state_domains() -> None:
    package_root = Path(__file__).resolve().parents[1] / "src" / "nks" / "enki"
    prohibited = (
        "human_state",
        "person_object",
        "erikson",
        "eoa",
        "executive_profile",
    )

    for path in package_root.glob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for token in prohibited:
            assert token not in source, f"{path} leaked bounded-context token {token}"
