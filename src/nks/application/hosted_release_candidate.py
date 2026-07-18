"""Deterministic hosted Enki release-candidate and human decision package.

Sprint 36 separates software readiness, hosted architecture validation, the zero-cost
operating envelope, and production deployment readiness.  Missing or blocked evidence
is preserved as such.  The package supports human deployment choices but cannot issue
one itself.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.production_control_readiness import ProductionControl


HOSTED_CANDIDATE_VERSION = "enki-hosted-1.0-rc2"
EVIDENCE_BASELINE_COMMIT = "219bf709b3adae247085f4610bae4fe86059a5f9"


class ConclusionKind(StrEnum):
    SOFTWARE_READINESS = "SOFTWARE_READINESS"
    HOSTED_ARCHITECTURE_VALIDATION = "HOSTED_ARCHITECTURE_VALIDATION"
    ZERO_COST_OPERATING_ENVELOPE = "ZERO_COST_OPERATING_ENVELOPE"
    PRODUCTION_DEPLOYMENT_READINESS = "PRODUCTION_DEPLOYMENT_READINESS"


class ConclusionStatus(StrEnum):
    PASS_TEST = "PASS_TEST"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_READY = "NOT_READY"


class EvidenceStatus(StrEnum):
    COMPLETE = "complete"
    BLOCKED = "blocked"
    PLANNED = "planned"
    SUPERSEDED = "superseded"


class HumanDecisionDisposition(StrEnum):
    APPROVE = "APPROVE"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
    DEFER = "DEFER"
    REJECT = "REJECT"


class DecisionState(StrEnum):
    PENDING_HUMAN_DECISION = "PENDING_HUMAN_DECISION"


class EvidencePointer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    status: EvidenceStatus
    qualification: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "EvidencePointer":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"evidence_sha256"})
        )
        if self.evidence_sha256 != expected:
            raise ValueError("hosted release evidence pointer hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EvidencePointer":
        payload = dict(values)
        payload["evidence_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ReleaseConclusion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ConclusionKind
    status: ConclusionStatus
    evidence_ids: tuple[str, ...]
    blockers: tuple[str, ...] = ()
    statement: str = Field(min_length=1)
    production_claim: Literal[False] = False
    conclusion_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_conclusion(self) -> "ReleaseConclusion":
        if self.kind == ConclusionKind.PRODUCTION_DEPLOYMENT_READINESS:
            if self.status == ConclusionStatus.PASS_TEST:
                raise ValueError("production deployment readiness cannot be satisfied by TEST status")
        if self.status == ConclusionStatus.BLOCKED and not self.blockers:
            raise ValueError("blocked conclusion requires explicit blockers")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"conclusion_sha256"})
        )
        if self.conclusion_sha256 != expected:
            raise ValueError("hosted release conclusion hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ReleaseConclusion":
        payload = dict(values)
        payload["conclusion_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class HumanDeploymentDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    candidate_version: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    supported_dispositions: tuple[HumanDecisionDisposition, ...]
    decision_state: Literal[DecisionState.PENDING_HUMAN_DECISION] = (
        DecisionState.PENDING_HUMAN_DECISION
    )
    decision_authority: Literal["HUMAN"] = "HUMAN"
    selected_disposition: None = None
    request_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_request(self) -> "HumanDeploymentDecisionRequest":
        if set(self.supported_dispositions) != set(HumanDecisionDisposition):
            raise ValueError("human decision request must support all four dispositions")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"request_sha256"})
        )
        if self.request_sha256 != expected:
            raise ValueError("human deployment decision request hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HumanDeploymentDecisionRequest":
        payload = dict(values)
        payload["request_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class HostedReleaseCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    candidate_version: Literal["enki-hosted-1.0-rc2"] = HOSTED_CANDIDATE_VERSION
    evidence_baseline_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    architecture_documents: tuple[str, ...]
    evidence: tuple[EvidencePointer, ...]
    conclusions: tuple[ReleaseConclusion, ...]
    unresolved_production_controls: tuple[ProductionControl, ...]
    package_documents: tuple[str, ...]
    external_services_budget_usd: Literal[0] = 0
    production_deployment_authorized: Literal[False] = False
    production_approval: Literal[False] = False
    decision_state: Literal[DecisionState.PENDING_HUMAN_DECISION] = (
        DecisionState.PENDING_HUMAN_DECISION
    )
    candidate_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_candidate(self) -> "HostedReleaseCandidate":
        expected_architecture = {
            "architecture/enki/enki-split-cloud-reference-architecture.md",
            "architecture/enki/enki-canonical-nine-layer-architecture.md",
        }
        if set(self.architecture_documents) != expected_architecture:
            raise ValueError("hosted release candidate must bind exactly the corrected architecture baseline")

        kinds = [item.kind for item in self.conclusions]
        if set(kinds) != set(ConclusionKind) or len(kinds) != len(set(kinds)):
            raise ValueError("release candidate must contain exactly four separate conclusions")

        evidence_ids = [item.evidence_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("release evidence ids must be unique")
        known_evidence = set(evidence_ids)
        for conclusion in self.conclusions:
            if not set(conclusion.evidence_ids).issubset(known_evidence):
                raise ValueError("release conclusion references undeclared evidence")

        if set(self.unresolved_production_controls) != set(ProductionControl):
            raise ValueError("all seven unresolved production controls must remain explicit")
        if len(self.unresolved_production_controls) != len(set(self.unresolved_production_controls)):
            raise ValueError("production controls must not be duplicated")

        hosted = next(
            item for item in self.conclusions
            if item.kind == ConclusionKind.HOSTED_ARCHITECTURE_VALIDATION
        )
        if hosted.status not in {ConclusionStatus.PARTIAL, ConclusionStatus.BLOCKED}:
            raise ValueError("hosted architecture cannot pass while finalist validation remains incomplete")

        production = next(
            item for item in self.conclusions
            if item.kind == ConclusionKind.PRODUCTION_DEPLOYMENT_READINESS
        )
        if production.status != ConclusionStatus.BLOCKED:
            raise ValueError("production deployment readiness must remain blocked without production control evidence")

        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"candidate_sha256"})
        )
        if self.candidate_sha256 != expected:
            raise ValueError("hosted release candidate hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HostedReleaseCandidate":
        payload = dict(values)
        payload["candidate_sha256"] = canonical_sha256(payload)
        return cls(**payload)


def _evidence(
    evidence_id: str,
    category: str,
    reference: str,
    status: EvidenceStatus,
    qualification: str,
) -> EvidencePointer:
    return EvidencePointer.create(
        evidence_id=evidence_id,
        category=category,
        reference=reference,
        status=status,
        qualification=qualification,
    )


def build_hosted_release_candidate() -> HostedReleaseCandidate:
    evidence = (
        _evidence(
            "ARCH-NINE-LAYER",
            "architecture",
            "architecture/enki/enki-canonical-nine-layer-architecture.md",
            EvidenceStatus.COMPLETE,
            "Corrected product-neutral nine-layer architecture source of truth.",
        ),
        _evidence(
            "ARCH-SPLIT-CLOUD",
            "architecture",
            "architecture/enki/enki-split-cloud-reference-architecture.md",
            EvidenceStatus.COMPLETE,
            "Corrected split-cloud reference architecture source of truth.",
        ),
        _evidence(
            "SPRINT-024",
            "hosting-options",
            "records/sprints/NKS-SPR-024.json",
            EvidenceStatus.COMPLETE,
            "Hosting options and split-cloud exploration completed without production approval.",
        ),
        _evidence(
            "SPRINT-025",
            "hosted-validation-foundation",
            "records/sprints/NKS-SPR-025.json",
            EvidenceStatus.COMPLETE,
            "Comparable TEST-only validation program established for all three finalists.",
        ),
        _evidence(
            "SPRINT-026",
            "hosted-validation",
            "records/sprints/NKS-SPR-026.json",
            EvidenceStatus.BLOCKED,
            "CF-NATIVE hosted TEST campaign blocked by unavailable provider TEST identity, credentials, and teardown authority.",
        ),
        _evidence(
            "SPRINT-027",
            "hosted-validation",
            "records/sprints/NKS-SPR-027.json",
            EvidenceStatus.PLANNED,
            "CF-NEON-R2 hosted TEST campaign not yet executed.",
        ),
        _evidence(
            "SPRINT-028",
            "hosted-validation",
            "records/sprints/NKS-SPR-028.json",
            EvidenceStatus.PLANNED,
            "GCP-NEON-R2 hosted TEST campaign not yet executed.",
        ),
        _evidence(
            "SPRINT-029",
            "hosting-comparison",
            "records/sprints/NKS-SPR-029.json",
            EvidenceStatus.PLANNED,
            "Cross-finalist comparison cannot complete before hosted TEST campaigns.",
        ),
        _evidence(
            "SPRINT-030",
            "hosting-decision",
            "records/sprints/NKS-SPR-030.json",
            EvidenceStatus.PLANNED,
            "Hosting-direction decision package remains pending comparable hosted evidence.",
        ),
        _evidence(
            "SPRINT-015",
            "performance",
            "records/sprints/NKS-SPR-015.json",
            EvidenceStatus.COMPLETE,
            "Repository-local TEST benchmarks exist; they are not production capacity guarantees.",
        ),
        _evidence(
            "SPRINT-016",
            "zero-cost-isolation",
            "records/sprints/NKS-SPR-016.json",
            EvidenceStatus.COMPLETE,
            "Zero-cost repository-local isolation proof completed without paid infrastructure.",
        ),
        _evidence(
            "SPRINT-020",
            "recovery",
            "records/sprints/NKS-SPR-020.json",
            EvidenceStatus.COMPLETE,
            "Concurrency, contention, and distributed recovery TEST contracts completed.",
        ),
        _evidence(
            "SPRINT-031",
            "temporal-authority",
            "records/sprints/NKS-SPR-031.json",
            EvidenceStatus.COMPLETE,
            "Historical truth and current authority are temporally separated and fail closed on conflict.",
        ),
        _evidence(
            "SPRINT-032",
            "retrieval-model-gateway",
            "records/sprints/NKS-SPR-032.json",
            EvidenceStatus.COMPLETE,
            "Governed retrieval, projections, and provider-neutral model gateway completed in TEST.",
        ),
        _evidence(
            "SPRINT-033",
            "downstream-consumers",
            "records/sprints/NKS-SPR-033.json",
            EvidenceStatus.COMPLETE,
            "All three downstream product suites consume Enki through governed TEST-only boundaries.",
        ),
        _evidence(
            "SPRINT-034",
            "multi-consumer-operations",
            "records/sprints/NKS-SPR-034.json",
            EvidenceStatus.COMPLETE,
            "Concurrent multi-consumer isolation, recovery, telemetry, and portability paths completed.",
        ),
        _evidence(
            "SPRINT-035",
            "production-control-readiness",
            "records/sprints/NKS-SPR-035.json",
            EvidenceStatus.COMPLETE,
            "All seven production controls have explicit validation contracts but no qualifying production validation evidence.",
        ),
    )

    software_evidence = (
        "SPRINT-015", "SPRINT-016", "SPRINT-020", "SPRINT-031",
        "SPRINT-032", "SPRINT-033", "SPRINT-034", "SPRINT-035",
    )
    hosted_evidence = (
        "ARCH-NINE-LAYER", "ARCH-SPLIT-CLOUD", "SPRINT-024", "SPRINT-025",
        "SPRINT-026", "SPRINT-027", "SPRINT-028", "SPRINT-029", "SPRINT-030",
    )
    zero_cost_evidence = ("SPRINT-016", "SPRINT-025", "SPRINT-026", "SPRINT-027", "SPRINT-028")
    production_evidence = ("SPRINT-035", "SPRINT-026", "SPRINT-027", "SPRINT-028")

    conclusions = (
        ReleaseConclusion.create(
            kind=ConclusionKind.SOFTWARE_READINESS,
            status=ConclusionStatus.PASS_TEST,
            evidence_ids=software_evidence,
            blockers=(),
            statement=(
                "The provider-neutral Enki software, governance, retrieval, model-use, downstream-consumer, "
                "multi-consumer, recovery, and production-control-readiness contracts pass repository-local TEST validation."
            ),
            production_claim=False,
        ),
        ReleaseConclusion.create(
            kind=ConclusionKind.HOSTED_ARCHITECTURE_VALIDATION,
            status=ConclusionStatus.BLOCKED,
            evidence_ids=hosted_evidence,
            blockers=(
                "CF-NATIVE hosted TEST campaign is blocked on provider TEST identity, credentials, and teardown authority.",
                "CF-NEON-R2 and GCP-NEON-R2 hosted TEST campaigns are not yet executed.",
                "Cross-finalist comparison and hosting-direction decision packages therefore remain incomplete.",
            ),
            statement=(
                "The corrected architecture and common hosted validation contract are complete, but no finalist has completed "
                "the comparable hosted TEST campaign required to validate a hosting architecture."
            ),
            production_claim=False,
        ),
        ReleaseConclusion.create(
            kind=ConclusionKind.ZERO_COST_OPERATING_ENVELOPE,
            status=ConclusionStatus.PARTIAL,
            evidence_ids=zero_cost_evidence,
            blockers=(
                "Repository-local TEST execution is demonstrated at zero external-services cost.",
                "Actual hosted finalist quota, latency, storage, egress, and teardown behavior have not been measured end to end.",
            ),
            statement=(
                "The local and CI TEST path remains within the absolute zero-dollar external-services boundary; "
                "the actual hosted zero-cost operating envelope remains unvalidated."
            ),
            production_claim=False,
        ),
        ReleaseConclusion.create(
            kind=ConclusionKind.PRODUCTION_DEPLOYMENT_READINESS,
            status=ConclusionStatus.BLOCKED,
            evidence_ids=production_evidence,
            blockers=tuple(control.value for control in ProductionControl),
            statement=(
                "Production deployment is not ready: all seven physical production controls have validation contracts "
                "but lack qualifying production-scope evidence, and no production hosting architecture has been selected."
            ),
            production_claim=False,
        ),
    )

    return HostedReleaseCandidate.create(
        schema_version=1,
        candidate_version=HOSTED_CANDIDATE_VERSION,
        evidence_baseline_commit=EVIDENCE_BASELINE_COMMIT,
        architecture_documents=(
            "architecture/enki/enki-split-cloud-reference-architecture.md",
            "architecture/enki/enki-canonical-nine-layer-architecture.md",
        ),
        evidence=evidence,
        conclusions=conclusions,
        unresolved_production_controls=tuple(ProductionControl),
        package_documents=(
            "releases/enki-hosted-1.0-rc2/README.md",
            "releases/enki-hosted-1.0-rc2/readiness-manifest.json",
            "releases/enki-hosted-1.0-rc2/known-limitations.md",
            "releases/enki-hosted-1.0-rc2/operating-runbook.md",
            "releases/enki-hosted-1.0-rc2/rollback-plan.md",
            "releases/enki-hosted-1.0-rc2/migration-path.md",
            "releases/enki-hosted-1.0-rc2/support-boundaries.md",
            "releases/enki-hosted-1.0-rc2/independent-review-checklist.md",
            "releases/enki-hosted-1.0-rc2/human-deployment-decision-request.md",
        ),
        external_services_budget_usd=0,
        production_deployment_authorized=False,
        production_approval=False,
        decision_state=DecisionState.PENDING_HUMAN_DECISION,
    )


def build_human_deployment_decision_request(
    candidate: HostedReleaseCandidate | None = None,
) -> HumanDeploymentDecisionRequest:
    selected = candidate or build_hosted_release_candidate()
    return HumanDeploymentDecisionRequest.create(
        request_id=f"DECISION-{selected.candidate_version}",
        candidate_version=selected.candidate_version,
        candidate_sha256=selected.candidate_sha256,
        supported_dispositions=tuple(HumanDecisionDisposition),
        decision_state=DecisionState.PENDING_HUMAN_DECISION,
        decision_authority="HUMAN",
        selected_disposition=None,
    )


def hosted_release_candidate_fixture() -> dict[str, object]:
    return build_hosted_release_candidate().model_dump(mode="json")


def human_deployment_decision_fixture() -> dict[str, object]:
    return build_human_deployment_decision_request().model_dump(mode="json")
