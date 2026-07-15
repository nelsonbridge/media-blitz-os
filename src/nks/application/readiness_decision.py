"""Deterministic Enki 1.0 readiness decision package.

Sprint 23 consolidates TEST evidence for independent human review. It does not
self-certify production readiness, infrastructure isolation, multitenancy, or go-live
approval. Physical production controls remain explicit prerequisites unless separately
validated by qualifying external evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256


PRIOR_EVIDENCE_COMMIT = "a967cc58adc5183420ed99d11fd82f83396c5766"
CANDIDATE_VERSION = "1.0-rc1"


class ProductionControlStatus(StrEnum):
    VALIDATED = "VALIDATED"
    DEFERRED = "DEFERRED"
    UNAVAILABLE = "UNAVAILABLE"
    UNRESOLVED = "UNRESOLVED"


class CampaignStatus(StrEnum):
    PASS_TEST = "PASS_TEST"
    ACCEPTED_FINDING = "ACCEPTED_FINDING"


class DecisionState(StrEnum):
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"


class SprintEvidencePointer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sprint_id: str = Field(pattern=r"^NKS-SPR-\d{3}$")
    record_path: str = Field(min_length=1)
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    status: Literal["complete", "superseded"]
    evidence_count: int = Field(ge=1)


class CampaignEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    campaign: str = Field(min_length=1)
    status: CampaignStatus
    evidence_sprints: list[str] = Field(min_length=1)
    qualification: Literal["TEST_EVIDENCE_ONLY"] = "TEST_EVIDENCE_ONLY"
    notes: str = Field(min_length=1)


class ProductionPrerequisite(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    control: str = Field(min_length=1)
    status: ProductionControlStatus
    evidence_refs: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def validated_requires_evidence(self) -> "ProductionPrerequisite":
        if self.status == ProductionControlStatus.VALIDATED and not self.evidence_refs:
            raise ValueError("validated production control requires qualifying evidence")
        return self


class ReadinessManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    candidate_version: Literal["1.0-rc1"] = CANDIDATE_VERSION
    prior_evidence_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    external_services_budget_usd: Literal[0] = 0
    prior_sprint_evidence: list[SprintEvidencePointer] = Field(min_length=22, max_length=22)
    campaigns: list[CampaignEvidence] = Field(min_length=7)
    production_prerequisites: list[ProductionPrerequisite] = Field(min_length=7, max_length=7)
    package_documents: list[str] = Field(min_length=5)
    local_test_scope_statement: str = Field(min_length=1)
    production_certification: Literal[False] = False
    multitenancy_accreditation: Literal[False] = False
    production_approval: Literal[False] = False
    decision_state: Literal[DecisionState.HUMAN_DECISION_REQUIRED] = (
        DecisionState.HUMAN_DECISION_REQUIRED
    )
    generated_at: datetime
    manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_manifest(self) -> "ReadinessManifest":
        expected_sprints = {f"NKS-SPR-{index:03d}" for index in range(1, 23)}
        actual_sprints = {item.sprint_id for item in self.prior_sprint_evidence}
        if actual_sprints != expected_sprints:
            raise ValueError("readiness manifest must reference every prior sprint exactly once")
        if any(item.source_commit != self.prior_evidence_commit for item in self.prior_sprint_evidence):
            raise ValueError("prior sprint evidence must resolve through one exact source commit")
        required_controls = {
            "cloud-iam",
            "production-identity-federation",
            "managed-database-row-level-isolation",
            "network-segmentation",
            "per-tenant-production-key-management",
            "production-secrets-management",
            "independent-penetration-testing",
        }
        controls = {item.control for item in self.production_prerequisites}
        if controls != required_controls:
            raise ValueError("all physical production prerequisites must be explicitly represented")
        expected_hash = canonical_sha256(
            self.model_dump(mode="python", exclude={"manifest_sha256"})
        )
        if self.manifest_sha256 != expected_hash:
            raise ValueError("readiness manifest hash is invalid")
        return self


def _sprint_pointer(index: int, evidence_count: int) -> SprintEvidencePointer:
    sprint_id = f"NKS-SPR-{index:03d}"
    return SprintEvidencePointer(
        sprint_id=sprint_id,
        record_path=f"records/sprints/{sprint_id}.json",
        source_commit=PRIOR_EVIDENCE_COMMIT,
        status="superseded" if index == 3 else "complete",
        evidence_count=evidence_count,
    )


def build_readiness_manifest() -> ReadinessManifest:
    evidence_counts = [
        1, 2, 1, 5, 3, 4, 3, 4, 4, 5, 5, 5, 6, 6, 5, 6, 5, 5, 5, 10, 8, 5
    ]
    pointers = [
        _sprint_pointer(index, evidence_counts[index - 1])
        for index in range(1, 23)
    ]
    campaigns = [
        CampaignEvidence(
            campaign="adversarial",
            status=CampaignStatus.PASS_TEST,
            evidence_sprints=["NKS-SPR-013", "NKS-SPR-016", "NKS-SPR-020", "NKS-SPR-022"],
            notes="Repository-local TEST adversarial paths pass; this is not external penetration certification.",
        ),
        CampaignEvidence(
            campaign="chaos",
            status=CampaignStatus.PASS_TEST,
            evidence_sprints=["NKS-SPR-013", "NKS-SPR-020"],
            notes="TEST interruption, contention, partition-shaped failure, rollback, and recovery paths pass.",
        ),
        CampaignEvidence(
            campaign="recovery",
            status=CampaignStatus.PASS_TEST,
            evidence_sprints=[
                "NKS-SPR-005", "NKS-SPR-007", "NKS-SPR-008", "NKS-SPR-009",
                "NKS-SPR-010", "NKS-SPR-012", "NKS-SPR-020"
            ],
            notes="Journaled, exact-retry, rollback, forensic, portability, and distributed recovery TEST evidence passes.",
        ),
        CampaignEvidence(
            campaign="privacy",
            status=CampaignStatus.PASS_TEST,
            evidence_sprints=[
                "NKS-SPR-008", "NKS-SPR-009", "NKS-SPR-011", "NKS-SPR-016",
                "NKS-SPR-018", "NKS-SPR-019", "NKS-SPR-022"
            ],
            notes="Consent, purpose, disclosure, isolation, observability, retention, and downstream privacy TEST controls pass.",
        ),
        CampaignEvidence(
            campaign="logical-isolation",
            status=CampaignStatus.PASS_TEST,
            evidence_sprints=["NKS-SPR-016", "NKS-SPR-020", "NKS-SPR-022"],
            notes="Logical and repository-local physical-separation semantics pass in TEST only.",
        ),
        CampaignEvidence(
            campaign="compatibility",
            status=CampaignStatus.PASS_TEST,
            evidence_sprints=["NKS-SPR-006", "NKS-SPR-021", "NKS-SPR-022"],
            notes="Core, stable consumer, CLI/API, and downstream compatibility contracts pass in TEST.",
        ),
        CampaignEvidence(
            campaign="supply-chain",
            status=CampaignStatus.PASS_TEST,
            evidence_sprints=["NKS-SPR-014"],
            notes="Clean-room reproducibility, dependency inventory, SBOM, provenance, and TEST attestation checks pass.",
        ),
    ]
    unresolved = [
        ("cloud-iam", "No production cloud IAM environment or qualifying external validation exists under the zero-dollar boundary."),
        ("production-identity-federation", "Production identity federation has not been provisioned or independently validated."),
        ("managed-database-row-level-isolation", "Managed production database row-level isolation has not been provisioned or independently validated."),
        ("network-segmentation", "Production network segmentation has not been provisioned or independently validated."),
        ("per-tenant-production-key-management", "Production per-tenant key management has not been provisioned or independently validated."),
        ("production-secrets-management", "Production secrets management has not been provisioned or independently validated."),
        ("independent-penetration-testing", "No independent external penetration test has been performed."),
    ]
    prerequisites = [
        ProductionPrerequisite(
            control=control,
            status=ProductionControlStatus.UNRESOLVED,
            evidence_refs=[],
            rationale=rationale,
        )
        for control, rationale in unresolved
    ]
    payload = {
        "schema_version": 1,
        "candidate_version": CANDIDATE_VERSION,
        "prior_evidence_commit": PRIOR_EVIDENCE_COMMIT,
        "external_services_budget_usd": 0,
        "prior_sprint_evidence": pointers,
        "campaigns": campaigns,
        "production_prerequisites": prerequisites,
        "package_documents": [
            "releases/enki-1.0-candidate/README.md",
            "releases/enki-1.0-candidate/known-limitations.md",
            "releases/enki-1.0-candidate/operating-runbook.md",
            "releases/enki-1.0-candidate/rollback-plan.md",
            "releases/enki-1.0-candidate/support-boundaries.md",
            "releases/enki-1.0-candidate/independent-review-checklist.md",
            "releases/enki-1.0-candidate/human-decision-request.md",
        ],
        "local_test_scope_statement": (
            "Sprint 16 proves logical boundary enforcement and repository-local physical-separation semantics only. "
            "It is not production infrastructure certification, independent security certification, or multitenancy accreditation."
        ),
        "production_certification": False,
        "multitenancy_accreditation": False,
        "production_approval": False,
        "decision_state": DecisionState.HUMAN_DECISION_REQUIRED,
        "generated_at": datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc),
    }
    return ReadinessManifest(**payload, manifest_sha256=canonical_sha256(payload))


def readiness_manifest_dict() -> dict[str, object]:
    return build_readiness_manifest().model_dump(mode="json")
