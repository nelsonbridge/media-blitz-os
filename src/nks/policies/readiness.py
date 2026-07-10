"""Governance-as-code validators for NKS publication readiness."""

from __future__ import annotations

from dataclasses import dataclass

from nks.domain.models import (
    GateStatus,
    NarrativeRecord,
    ProofRecord,
    PublicationRecord,
    SourceRecord,
    VisualPackageRecord,
)


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    failures: tuple[str, ...]


def validate_source_lineage(source: SourceRecord | None) -> ValidationResult:
    failures: list[str] = []
    if source is None:
        failures.append("source record is missing")
    elif not source.source_location.strip():
        failures.append("source location is missing")
    return ValidationResult(not failures, tuple(failures))


def validate_proof_posture(proof: ProofRecord | None) -> ValidationResult:
    failures: list[str] = []
    if proof is None:
        failures.append("proof record is missing")
    elif proof.gate_status not in {GateStatus.READY, GateStatus.APPROVED, GateStatus.WAIVED}:
        failures.append(f"proof gate is {proof.gate_status}")
    return ValidationResult(not failures, tuple(failures))


def validate_narrative_arc(narrative: NarrativeRecord | None) -> ValidationResult:
    failures: list[str] = []
    if narrative is None:
        failures.append("narrative record is missing")
        return ValidationResult(False, tuple(failures))

    for field in (
        "recognition",
        "reframe",
        "framework",
        "proof",
        "application",
        "consequence",
        "invitation",
    ):
        if not getattr(narrative, field).strip():
            failures.append(f"narrative segment missing: {field}")
    if narrative.gate_status not in {GateStatus.READY, GateStatus.APPROVED}:
        failures.append(f"narrative gate is {narrative.gate_status}")
    return ValidationResult(not failures, tuple(failures))


def validate_visual_package(visual: VisualPackageRecord | None) -> ValidationResult:
    failures: list[str] = []
    if visual is None:
        failures.append("visual package is missing")
    else:
        if not visual.signature_diagram_id:
            failures.append("signature diagram is missing")
        if visual.gate_status not in {GateStatus.READY, GateStatus.APPROVED, GateStatus.WAIVED}:
            failures.append(f"visual gate is {visual.gate_status}")
    return ValidationResult(not failures, tuple(failures))


def validate_publication_readiness(
    publication: PublicationRecord,
    source: SourceRecord | None,
    proof: ProofRecord | None,
    narrative: NarrativeRecord | None,
    visual: VisualPackageRecord | None,
) -> ValidationResult:
    failures: list[str] = []
    for result in (
        validate_source_lineage(source),
        validate_proof_posture(proof),
        validate_narrative_arc(narrative),
        validate_visual_package(visual),
    ):
        failures.extend(result.failures)

    if publication.editorial_status not in {GateStatus.READY, GateStatus.APPROVED}:
        failures.append(f"editorial gate is {publication.editorial_status}")
    if publication.user_approval is not GateStatus.APPROVED:
        failures.append(f"user approval is {publication.user_approval}")

    return ValidationResult(not failures, tuple(failures))
