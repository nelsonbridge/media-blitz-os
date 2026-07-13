"""Executable traceability for Enki's current constitutional controls.

This registry does not amend the Constitution or prove implementation by
itself. It records where each core invariant is enforced so repository checks
can detect missing or untraceable controls as the architecture evolves.
Product-specific enforcement belongs in product traceability registries.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EnkiInvariant(StrEnum):
    USER_OWNED_OBJECTIVES = "USER_OWNED_OBJECTIVES"
    USER_OWNED_ACCOUNTABILITY = "USER_OWNED_ACCOUNTABILITY"
    ATTRIBUTABLE_HISTORY = "ATTRIBUTABLE_HISTORY"
    NO_HIDDEN_OBJECTIVE_SUBSTITUTION = "NO_HIDDEN_OBJECTIVE_SUBSTITUTION"
    CONTINUOUS_INTERNAL_RECONCILIATION = "CONTINUOUS_INTERNAL_RECONCILIATION"
    GOVERNED_EXTERNAL_DISCLOSURE = "GOVERNED_EXTERNAL_DISCLOSURE"
    NO_COMPULSORY_CORRECTION = "NO_COMPULSORY_CORRECTION"
    CONTEXT_PRESERVATION = "CONTEXT_PRESERVATION"
    RELATIONSHIP_INTEGRITY = "RELATIONSHIP_INTEGRITY"
    CORE_RESTRAINT = "CORE_RESTRAINT"


class ControlStatus(StrEnum):
    IMPLEMENTED = "IMPLEMENTED"
    PARTIAL = "PARTIAL"
    PLANNED = "PLANNED"


class InvariantControl(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    invariant: EnkiInvariant
    description: str = Field(min_length=1)
    status: ControlStatus
    contract_refs: tuple[str, ...] = ()
    service_refs: tuple[str, ...] = ()
    test_refs: tuple[str, ...] = ()
    receipt_fields: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


TRACEABILITY_CONTROLS: tuple[InvariantControl, ...] = (
    InvariantControl(
        invariant=EnkiInvariant.USER_OWNED_OBJECTIVES,
        description="Objectives and priorities enter reconciliation only as supplied references.",
        status=ControlStatus.IMPLEMENTED,
        contract_refs=(
            "nks.enki.contracts.ReconciliationRequest.objective_refs",
            "nks.enki.contracts.ReconciliationRequest.priority_refs",
            "nks.enki.contracts.ReconciliationFinding.objective_refs",
            "nks.enki.contracts.ReconciliationFinding.priority_refs",
        ),
        service_refs=("nks.enki.reconciliation.ReconciliationEngine._validate_findings",),
        test_refs=(
            "tests/test_enki_core.py::test_relationship_strategy_surfaces_divergence_without_reordering_priorities",
            "tests/test_enki_core.py::test_hidden_objective_substitution_fails_closed",
        ),
    ),
    InvariantControl(
        invariant=EnkiInvariant.USER_OWNED_ACCOUNTABILITY,
        description="Core findings inform without supplying decisions, values, or recommendations.",
        status=ControlStatus.PARTIAL,
        contract_refs=("nks.enki.contracts.ReconciliationFinding",),
        service_refs=("nks.enki.reconciliation.RelationshipFindingStrategy",),
        test_refs=(
            "tests/test_enki_core.py::test_relationship_strategy_surfaces_divergence_without_reordering_priorities",
        ),
        limitations=(
            "Consuming products require independent controls against prescriptive objective substitution.",
        ),
    ),
    InvariantControl(
        invariant=EnkiInvariant.ATTRIBUTABLE_HISTORY,
        description="Evidence, interpretation versions, approvals, transactions, and receipts remain attributable.",
        status=ControlStatus.PARTIAL,
        contract_refs=(
            "nks.enki.contracts.EvidenceRef",
            "nks.enki.contracts.ReconciliationFinding.interpretation_version",
            "nks.enki.disclosure.DisclosureReceipt",
            "nks.governance.approvals.ApprovalEvaluation",
        ),
        service_refs=(
            "nks.enki.reconciliation.ReconciliationEngine",
            "nks.enki.disclosure.ConservativeDisclosureService",
        ),
        test_refs=(
            "tests/test_enki_core.py::test_relationship_strategy_surfaces_divergence_without_reordering_priorities",
            "tests/test_enki_disclosure.py::test_external_disclosure_requires_content_bound_approval",
        ),
        receipt_fields=(
            "approval_id",
            "execution_context",
            "transaction_id",
            "content_sha256",
            "policy_version",
        ),
        limitations=(
            "Canonical persistence and migration of reconciliation findings remain unimplemented.",
        ),
    ),
    InvariantControl(
        invariant=EnkiInvariant.NO_HIDDEN_OBJECTIVE_SUBSTITUTION,
        description="A strategy cannot introduce objectives or priorities absent from the request.",
        status=ControlStatus.IMPLEMENTED,
        contract_refs=(
            "nks.enki.contracts.ReconciliationRequest",
            "nks.enki.contracts.ReconciliationFinding",
        ),
        service_refs=("nks.enki.reconciliation.ReconciliationEngine._validate_findings",),
        test_refs=("tests/test_enki_core.py::test_hidden_objective_substitution_fails_closed",),
    ),
    InvariantControl(
        invariant=EnkiInvariant.CONTINUOUS_INTERNAL_RECONCILIATION,
        description="Reconciliation may be executed and recorded independently of external disclosure.",
        status=ControlStatus.PARTIAL,
        contract_refs=("nks.enki.contracts.ReconciliationResult",),
        service_refs=("nks.application.enki_workflow.ReconcileAndRecord",),
        test_refs=(
            "tests/test_enki_workflow.py::test_recording_reconciliation_does_not_imply_disclosure",
        ),
        limitations=(
            "Triggering, scheduling, and longitudinal canonical persistence remain future work.",
        ),
    ),
    InvariantControl(
        invariant=EnkiInvariant.GOVERNED_EXTERNAL_DISCLOSURE,
        description="External disclosure requires exact audience, subject, content, and reserved approval alignment.",
        status=ControlStatus.IMPLEMENTED,
        contract_refs=(
            "nks.enki.disclosure.DisclosureContext",
            "nks.enki.disclosure.DisclosureReceipt",
            "nks.governance.approvals.ApprovalEvaluation",
        ),
        service_refs=(
            "nks.enki.disclosure.ConservativeDisclosureService",
            "nks.application.enki_workflow.DiscloseAndRecord",
        ),
        test_refs=(
            "tests/test_enki_disclosure.py::test_external_disclosure_requires_content_bound_approval",
            "tests/test_enki_disclosure.py::test_external_approval_for_wrong_action_is_withheld",
        ),
        receipt_fields=(
            "content_sha256",
            "approval_id",
            "execution_context",
            "transaction_id",
            "audience",
            "purpose",
        ),
    ),
    InvariantControl(
        invariant=EnkiInvariant.NO_COMPULSORY_CORRECTION,
        description="A divergence is represented as information and carries no corrective command.",
        status=ControlStatus.IMPLEMENTED,
        contract_refs=("nks.enki.contracts.ReconciliationFinding",),
        service_refs=("nks.enki.reconciliation.RelationshipFindingStrategy",),
        test_refs=(
            "tests/test_enki_core.py::test_relationship_strategy_surfaces_divergence_without_reordering_priorities",
        ),
    ),
    InvariantControl(
        invariant=EnkiInvariant.CONTEXT_PRESERVATION,
        description="Subject, domain, time, evidence, purpose, and execution context remain explicit.",
        status=ControlStatus.IMPLEMENTED,
        contract_refs=(
            "nks.enki.contracts.SubjectRef",
            "nks.enki.contracts.TemporalApplicability",
            "nks.governance.approvals.ApprovalRequest",
            "nks.enki.disclosure.DisclosureReceipt",
        ),
        service_refs=(
            "nks.enki.reconciliation.ReconciliationEngine._validate_request_scope",
            "nks.governance.approvals.evaluate_approval",
        ),
        test_refs=(
            "tests/test_enki_core.py::test_unknown_observation_reference_fails_closed",
            "tests/test_governed_approvals.py::test_mismatched_dimension_fails_closed",
        ),
        receipt_fields=(
            "execution_context",
            "transaction_id",
            "content_sha256",
            "purpose",
        ),
    ),
    InvariantControl(
        invariant=EnkiInvariant.RELATIONSHIP_INTEGRITY,
        description="Findings must trace to known observations, relationships, and attributable evidence.",
        status=ControlStatus.IMPLEMENTED,
        contract_refs=(
            "nks.enki.contracts.RelationshipAssertion",
            "nks.enki.contracts.ReconciliationFinding",
        ),
        service_refs=("nks.enki.reconciliation.ReconciliationEngine",),
        test_refs=(
            "tests/test_enki_core.py::test_unknown_observation_reference_fails_closed",
            "tests/test_enki_core.py::test_unknown_relationship_remains_uncertain",
        ),
    ),
    InvariantControl(
        invariant=EnkiInvariant.CORE_RESTRAINT,
        description="Subject and product ontologies remain outside the reconciliation core.",
        status=ControlStatus.IMPLEMENTED,
        contract_refs=("nks.enki",),
        service_refs=("nks.enki.reconciliation.ReconciliationEngine",),
        test_refs=(
            "tests/test_enki_core.py::test_enki_package_does_not_import_bounded_context_domains",
        ),
    ),
)


def validate_traceability(
    controls: tuple[InvariantControl, ...] = TRACEABILITY_CONTROLS,
) -> list[str]:
    """Return structural traceability violations without claiming runtime proof."""

    violations: list[str] = []
    observed = [control.invariant for control in controls]
    duplicates = sorted({item.value for item in observed if observed.count(item) > 1})
    missing = sorted(item.value for item in set(EnkiInvariant) - set(observed))

    if duplicates:
        violations.append(f"duplicate invariant controls: {duplicates}")
    if missing:
        violations.append(f"missing invariant controls: {missing}")

    for control in controls:
        if not control.contract_refs:
            violations.append(f"{control.invariant.value} has no contract references")
        if control.status == ControlStatus.IMPLEMENTED:
            if not control.service_refs:
                violations.append(f"{control.invariant.value} has no service references")
            if not control.test_refs:
                violations.append(f"{control.invariant.value} has no test references")

    return violations
