"""Compatibility projection from temporal human state into Enki core.

This adapter deliberately lives outside ``nks.enki``. It permits the current
human-state reference implementation to exercise the generic reconciliation
contracts without making human identity or legacy Boolean approval part of the
core ontology.
"""

from __future__ import annotations

from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    HumanStateTransition,
)
from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    EvidenceRef,
    ExpressionOrigin,
    Observation,
    ReferenceKind,
    RelationshipAssertion,
    SubjectRef,
    TemporalApplicability,
    TemporalStatus,
)


def _legacy_confidence(value: str, *, evidence_ids: list[str]) -> ConfidenceAssertion:
    normalized = value.strip().upper()
    level = {
        "UNKNOWN": ConfidenceLevel.UNKNOWN,
        "LOW": ConfidenceLevel.LOW,
        "MODERATE": ConfidenceLevel.MODERATE,
        "MEDIUM": ConfidenceLevel.MODERATE,
        "HIGH": ConfidenceLevel.HIGH,
    }.get(normalized, ConfidenceLevel.UNKNOWN)
    return ConfidenceAssertion(
        level=level,
        rationale=f"Projected from legacy confidence value {value!r}.",
        evidence_ids=evidence_ids,
    )


def project_human_observation(
    record: HumanStateObservation,
    *,
    expression_origin: ExpressionOrigin,
) -> Observation:
    """Project one human observation without inferring who authored it.

    ``ExpressionStrength.EXPLICIT`` does not prove self-declaration, so the
    caller must supply the semantically correct Enki expression origin.
    """

    evidence_id = f"{record.observation_id}:source"
    evidence = EvidenceRef(
        evidence_id=evidence_id,
        source_id=record.source_id,
        content_hash=record.content_hash,
        observed_at=record.observed_at,
        provenance_classification=record.provenance,
        metadata={"legacy_record_type": "HumanStateObservation"},
    )
    return Observation(
        observation_id=record.observation_id,
        subject=SubjectRef(subject_id=record.subject_id, subject_type="PERSON"),
        domain=record.domain,
        statement=record.content,
        content_hash=record.content_hash,
        evidence=[evidence],
        observed_at=record.observed_at,
        applicability=TemporalApplicability(
            effective_from=record.effective_from,
            effective_until=record.effective_until,
        ),
        context=list(record.context),
        expression_origin=expression_origin,
        confidence=_legacy_confidence(record.confidence, evidence_ids=[evidence_id]),
        temporal_status=TemporalStatus(record.temporal_status.value),
        metadata={
            **record.metadata,
            "legacy_record_type": "HumanStateObservation",
            "legacy_state_type": record.state_type,
            "legacy_expression_strength": record.expression_strength.value,
            "legacy_supersedes_observation_id": record.supersedes_observation_id,
        },
    )


def project_human_transition(record: HumanStateTransition) -> RelationshipAssertion:
    """Project a transition as a relationship assertion.

    Legacy ``approved_for_model_feedback`` and ``approved_by`` fields are
    intentionally not projected. They are compatibility inputs, not governed
    authority under ADR-0001.
    """

    origin = (
        ExpressionOrigin.GOVERNED_INFERENCE
        if record.expression_origin == ExpressionStrength.INFERRED
        else ExpressionOrigin.OBSERVED
    ) if hasattr(record, "expression_origin") else None
    del origin  # Transition origin is preserved as metadata, not reinterpreted.

    return RelationshipAssertion(
        relationship_id=record.transition_id,
        subject=SubjectRef(subject_id=record.subject_id, subject_type="PERSON"),
        domain=record.domain,
        source_kind=ReferenceKind.OBSERVATION,
        source_id=record.from_observation_id,
        target_kind=ReferenceKind.OBSERVATION,
        target_id=record.to_observation_id,
        relationship_type=record.transition_type.value,
        evidence=[],
        confidence=ConfidenceAssertion(
            level=ConfidenceLevel.UNKNOWN,
            rationale=(
                "Legacy transition confidence is preserved for review but has no "
                "attributable evidence reference in the legacy contract."
            ),
            evidence_ids=[],
        ),
        observed_at=record.detected_at,
        applicability=TemporalApplicability(effective_from=record.detected_at.date()),
        context=[],
        metadata={
            **record.metadata,
            "legacy_record_type": "HumanStateTransition",
            "legacy_transition_origin": record.origin.value,
            "legacy_stated_reason": record.stated_reason,
            "legacy_inferred_causes": list(record.inferred_causes),
            "legacy_durability": record.durability,
            "legacy_reversibility": record.reversibility,
            "legacy_confidence": record.confidence,
            "authority_note": (
                "Legacy model-feedback approval fields were intentionally excluded; "
                "governed approval must be evaluated separately."
            ),
        },
    )
