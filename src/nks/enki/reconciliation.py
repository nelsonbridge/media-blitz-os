"""Governed reconciliation orchestration.

The engine validates scope, traceability, and objective ownership around a
pluggable strategy. It does not prescribe values, decisions, or outcomes.
"""

from __future__ import annotations

from collections.abc import Sequence

from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    FindingKind,
    ReconciliationFinding,
    ReconciliationRequest,
    ReconciliationResult,
    ReferenceKind,
)
from nks.enki.ports import ReconciliationStrategy


class ReconciliationEngine:
    def __init__(
        self,
        strategy: ReconciliationStrategy,
        *,
        interpretation_version: str,
    ) -> None:
        if not interpretation_version:
            raise ValueError("interpretation_version is required")
        self._strategy = strategy
        self._interpretation_version = interpretation_version

    def execute(self, request: ReconciliationRequest) -> ReconciliationResult:
        self._validate_request_scope(request)
        findings = [
            finding.model_copy(update={"interpretation_version": self._interpretation_version})
            for finding in self._strategy.reconcile(request)
        ]
        self._validate_findings(request, findings)

        referenced_observations = {
            observation_id
            for finding in findings
            for observation_id in finding.observation_ids
        }
        unresolved = sorted(
            observation.observation_id
            for observation in request.observations
            if observation.observation_id not in referenced_observations
        )
        return ReconciliationResult(
            subject=request.subject,
            domain=request.domain,
            findings=findings,
            unresolved_observation_ids=unresolved,
            interpretation_version=self._interpretation_version,
            reconciled_at=request.as_of,
        )

    @staticmethod
    def _validate_request_scope(request: ReconciliationRequest) -> None:
        observation_ids = {item.observation_id for item in request.observations}
        objective_ids = set(request.objective_refs)
        priority_ids = set(request.priority_refs)

        for observation in request.observations:
            if observation.subject != request.subject or observation.domain != request.domain:
                raise ValueError("observation is outside the reconciliation scope")

        for relationship in request.relationships:
            if relationship.subject != request.subject or relationship.domain != request.domain:
                raise ValueError("relationship is outside the reconciliation scope")
            ReconciliationEngine._validate_reference(
                relationship.source_kind,
                relationship.source_id,
                observation_ids,
                objective_ids,
                priority_ids,
            )
            ReconciliationEngine._validate_reference(
                relationship.target_kind,
                relationship.target_id,
                observation_ids,
                objective_ids,
                priority_ids,
            )

    @staticmethod
    def _validate_reference(
        kind: ReferenceKind,
        reference_id: str,
        observation_ids: set[str],
        objective_ids: set[str],
        priority_ids: set[str],
    ) -> None:
        if kind == ReferenceKind.OBSERVATION and reference_id not in observation_ids:
            raise ValueError(f"unknown observation reference: {reference_id}")
        if kind == ReferenceKind.OBJECTIVE and reference_id not in objective_ids:
            raise ValueError(f"unknown objective reference: {reference_id}")
        if kind == ReferenceKind.PRIORITY and reference_id not in priority_ids:
            raise ValueError(f"unknown priority reference: {reference_id}")

    @staticmethod
    def _validate_findings(
        request: ReconciliationRequest,
        findings: Sequence[ReconciliationFinding],
    ) -> None:
        observation_ids = {item.observation_id for item in request.observations}
        relationship_ids = {item.relationship_id for item in request.relationships}
        evidence_ids = {
            evidence.evidence_id
            for observation in request.observations
            for evidence in observation.evidence
        } | {
            evidence.evidence_id
            for relationship in request.relationships
            for evidence in relationship.evidence
        }
        objective_ids = set(request.objective_refs)
        priority_ids = set(request.priority_refs)

        for finding in findings:
            if finding.subject != request.subject or finding.domain != request.domain:
                raise ValueError("finding is outside the reconciliation scope")
            if not set(finding.observation_ids) <= observation_ids:
                raise ValueError("finding references an unknown observation")
            if not set(finding.relationship_ids) <= relationship_ids:
                raise ValueError("finding references an unknown relationship")
            if not set(finding.evidence_ids) <= evidence_ids:
                raise ValueError("finding references unknown evidence")
            if not set(finding.objective_refs) <= objective_ids:
                raise ValueError("strategy attempted hidden objective substitution")
            if not set(finding.priority_refs) <= priority_ids:
                raise ValueError("strategy attempted hidden priority substitution")


class RelationshipFindingStrategy:
    """Create traceable findings from explicitly recorded relationships.

    This baseline strategy does not infer relationships from raw behavior. It
    interprets only relationship assertions supplied to the request, preserving
    room for future strategies without embedding one permanent ontology.
    """

    _ALIGNMENT_TYPES = frozenset({"ALIGNS_WITH", "CONSISTENT_WITH", "SUPPORTS"})
    _DIVERGENCE_TYPES = frozenset({"DIVERGES_FROM", "CONTRADICTS", "CONFLICTS_WITH"})

    def __init__(self, *, strategy_version: str = "relationship-findings/v1") -> None:
        self._strategy_version = strategy_version

    def reconcile(self, request: ReconciliationRequest) -> Sequence[ReconciliationFinding]:
        findings: list[ReconciliationFinding] = []
        for relationship in request.relationships:
            normalized_type = relationship.relationship_type.strip().upper()
            if normalized_type in self._ALIGNMENT_TYPES:
                kind = FindingKind.ALIGNMENT
            elif normalized_type in self._DIVERGENCE_TYPES:
                kind = FindingKind.DIVERGENCE
            else:
                kind = FindingKind.UNCERTAINTY

            evidence_ids = [item.evidence_id for item in relationship.evidence]
            confidence = relationship.confidence
            if not evidence_ids and confidence.level != ConfidenceLevel.UNKNOWN:
                confidence = ConfidenceAssertion(
                    level=ConfidenceLevel.UNKNOWN,
                    rationale="No attributable evidence was attached to the relationship assertion.",
                    evidence_ids=[],
                )

            observation_ids = [
                reference_id
                for reference_kind, reference_id in (
                    (relationship.source_kind, relationship.source_id),
                    (relationship.target_kind, relationship.target_id),
                )
                if reference_kind == ReferenceKind.OBSERVATION
            ]
            findings.append(
                ReconciliationFinding(
                    finding_id=f"RF-{relationship.relationship_id}",
                    subject=request.subject,
                    domain=request.domain,
                    finding_kind=kind,
                    summary=(
                        f"Recorded relationship {relationship.relationship_type} between "
                        f"{relationship.source_kind}:{relationship.source_id} and "
                        f"{relationship.target_kind}:{relationship.target_id}."
                    ),
                    observation_ids=observation_ids,
                    relationship_ids=[relationship.relationship_id],
                    evidence_ids=evidence_ids,
                    objective_refs=list(request.objective_refs),
                    priority_refs=list(request.priority_refs),
                    hypotheses=[],
                    confidence=confidence,
                    created_at=request.as_of,
                    interpretation_version=self._strategy_version,
                    metadata={"relationship_type": relationship.relationship_type},
                )
            )
        return findings
