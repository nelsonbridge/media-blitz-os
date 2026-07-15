"""Deterministic hosted-architecture exploration for Enki Sprint 24.

This module records provider facts, architecture candidates, production-prerequisite
implications, cost-model assumptions, and a human-decision shortlist. It performs no
infrastructure provisioning and cannot promote architecture feasibility into production
validation or approval.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256


REQUIRED_PRODUCTION_PREREQUISITES = frozenset(
    {
        "cloud-iam",
        "production-identity-federation",
        "managed-database-row-level-isolation",
        "network-segmentation",
        "per-tenant-production-key-management",
        "production-secrets-management",
        "independent-penetration-testing",
    }
)


class ArchitecturePattern(StrEnum):
    SINGLE_CLOUD = "SINGLE_CLOUD"
    PROVIDER_SPLIT = "PROVIDER_SPLIT"
    CONTROL_DATA_SPLIT = "CONTROL_DATA_SPLIT"
    PORTABILITY_HYBRID = "PORTABILITY_HYBRID"


class DecisionState(StrEnum):
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"


class EvidenceSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    url: str = Field(pattern=r"^https://")
    captured_at: datetime
    facts: list[str] = Field(min_length=1)


class HostingOption(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    option_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    pattern: ArchitecturePattern
    providers: list[str] = Field(min_length=1)
    components: dict[str, str]
    zero_cost_prototype_possible: bool
    estimated_monthly_cost_range_usd: list[float] = Field(min_length=2, max_length=2)
    cost_model_assumptions: list[str] = Field(min_length=1)
    strengths: list[str] = Field(min_length=1)
    risks: list[str] = Field(min_length=1)
    disqualifiers: list[str]
    prerequisite_mapping: dict[str, str]
    production_approved: Literal[False] = False
    infrastructure_provisioned: Literal[False] = False

    @model_validator(mode="after")
    def validate_option(self) -> "HostingOption":
        low, high = self.estimated_monthly_cost_range_usd
        if low < 0 or high < low:
            raise ValueError("hosting cost range is invalid")
        if set(self.prerequisite_mapping) != REQUIRED_PRODUCTION_PREREQUISITES:
            raise ValueError("every production prerequisite must be mapped exactly once")
        if any(value.strip().upper() == "VALIDATED" for value in self.prerequisite_mapping.values()):
            raise ValueError("architecture exploration cannot validate production controls")
        return self


class HostingDecisionPackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    package_version: Literal["enki-hosting-options-v1"] = "enki-hosting-options-v1"
    external_services_budget_usd: Literal[0] = 0
    researched_at: datetime
    evidence_sources: list[EvidenceSource] = Field(min_length=8)
    options: list[HostingOption] = Field(min_length=5)
    shortlist_option_ids: list[str] = Field(min_length=2)
    recommendation: str = Field(min_length=1)
    decision_state: Literal[DecisionState.HUMAN_DECISION_REQUIRED] = (
        DecisionState.HUMAN_DECISION_REQUIRED
    )
    production_approval: Literal[False] = False
    infrastructure_provisioned: Literal[False] = False
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_package(self) -> "HostingDecisionPackage":
        option_by_id = {item.option_id: item for item in self.options}
        if len(option_by_id) != len(self.options):
            raise ValueError("hosting option identifiers must be unique")
        if not set(self.shortlist_option_ids).issubset(option_by_id):
            raise ValueError("shortlist references an unknown hosting option")
        patterns = {item.pattern for item in self.options}
        required_patterns = {
            ArchitecturePattern.SINGLE_CLOUD,
            ArchitecturePattern.PROVIDER_SPLIT,
            ArchitecturePattern.CONTROL_DATA_SPLIT,
            ArchitecturePattern.PORTABILITY_HYBRID,
        }
        if not required_patterns.issubset(patterns):
            raise ValueError("all required hosting architecture patterns must be evaluated")
        shortlist_patterns = {option_by_id[item].pattern for item in self.shortlist_option_ids}
        if ArchitecturePattern.SINGLE_CLOUD not in shortlist_patterns:
            raise ValueError("shortlist must retain at least one single-cloud finalist")
        if not shortlist_patterns.intersection(
            {ArchitecturePattern.PROVIDER_SPLIT, ArchitecturePattern.CONTROL_DATA_SPLIT}
        ):
            raise ValueError("shortlist must retain at least one split-cloud finalist")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"package_sha256"}))
        if self.package_sha256 != expected:
            raise ValueError("hosting decision package hash is invalid")
        return self


def _prerequisite_mapping(*, note: str) -> dict[str, str]:
    return {
        "cloud-iam": f"UNRESOLVED — {note}; provider IAM must be provisioned and validated separately.",
        "production-identity-federation": f"UNRESOLVED — {note}; production federation remains a deployment validation task.",
        "managed-database-row-level-isolation": f"UNRESOLVED — {note}; database isolation must be proven on the selected production data service.",
        "network-segmentation": f"UNRESOLVED — {note}; private-network and segmentation controls require deployed-environment evidence.",
        "per-tenant-production-key-management": f"UNRESOLVED — {note}; production tenant-key custody and rotation require separate validation.",
        "production-secrets-management": f"UNRESOLVED — {note}; production secret lifecycle must be provisioned and tested.",
        "independent-penetration-testing": "UNRESOLVED — architecture selection cannot substitute for independent penetration testing.",
    }


def _source(
    source_id: str,
    provider: str,
    url: str,
    facts: list[str],
) -> EvidenceSource:
    return EvidenceSource(
        source_id=source_id,
        provider=provider,
        url=url,
        captured_at=datetime(2026, 7, 15, 19, 0, tzinfo=timezone.utc),
        facts=facts,
    )


def build_hosting_decision_package() -> HostingDecisionPackage:
    sources = [
        _source(
            "SRC-CF-WORKERS",
            "Cloudflare",
            "https://developers.cloudflare.com/workers/platform/pricing/",
            ["Free plan includes 100,000 requests per day", "Free plan CPU allowance is 10 ms per invocation"],
        ),
        _source(
            "SRC-CF-D1",
            "Cloudflare",
            "https://developers.cloudflare.com/d1/platform/pricing/",
            ["Free allowance includes 5 million rows read per day", "Free allowance includes 100,000 rows written per day", "Free storage allowance is 5 GB total"],
        ),
        _source(
            "SRC-CF-R2",
            "Cloudflare",
            "https://developers.cloudflare.com/r2/pricing/",
            ["Free allowance includes 10 GB-month storage", "Internet egress from R2 is free"],
        ),
        _source(
            "SRC-GCP-CLOUD-RUN",
            "Google Cloud",
            "https://cloud.google.com/run/pricing",
            ["Request-based free tier includes 180,000 vCPU-seconds per month", "Request-based free tier includes 360,000 GiB-seconds per month", "Free tier includes 2 million requests per month"],
        ),
        _source(
            "SRC-GCP-FIRESTORE",
            "Google Cloud",
            "https://cloud.google.com/firestore/pricing",
            ["Free quota includes 1 GiB stored data", "Free quota includes daily read, write, and delete allowances", "PITR, backups, restore, and clone are not included in free usage"],
        ),
        _source(
            "SRC-GCP-STORAGE",
            "Google Cloud",
            "https://cloud.google.com/storage/pricing",
            ["Always Free includes a limited storage and operations allowance in qualifying regions"],
        ),
        _source(
            "SRC-AWS-LAMBDA",
            "AWS",
            "https://aws.amazon.com/lambda/pricing/",
            ["Free tier includes 1 million requests per month", "Free tier includes 400,000 GB-seconds of compute per month"],
        ),
        _source(
            "SRC-AWS-DYNAMODB",
            "AWS",
            "https://aws.amazon.com/dynamodb/pricing/",
            ["Free tier includes 25 GB storage", "Free tier includes provisioned read and write capacity allowances"],
        ),
        _source(
            "SRC-NEON",
            "Neon",
            "https://neon.com/pricing",
            ["Free plan is $0 with no credit card required", "Free plan includes 100 CU-hours per project per month", "Free plan includes 0.5 GB storage per project", "Free compute can scale to zero when inactive"],
        ),
        _source(
            "SRC-SUPABASE",
            "Supabase",
            "https://supabase.com/pricing",
            ["Free plan is $0 with limited database, egress, storage, and active-project allowances", "Inactive free projects may pause"],
        ),
        _source(
            "SRC-AZURE-FUNCTIONS",
            "Microsoft Azure",
            "https://azure.microsoft.com/pricing/details/functions/",
            ["Consumption plan includes a monthly free grant for requests and compute", "Associated storage is billed separately"],
        ),
    ]

    options = [
        HostingOption(
            option_id="CF-NATIVE",
            name="Cloudflare-native single-cloud edge deployment",
            pattern=ArchitecturePattern.SINGLE_CLOUD,
            providers=["Cloudflare"],
            components={
                "compute": "Workers",
                "canonical_data": "D1",
                "evidence_object_store": "R2",
                "identity": "Cloudflare Access or application identity layer",
                "key_custody": "Provider/application key strategy to be selected",
                "secrets": "Workers secrets",
                "network": "Cloudflare edge/service bindings",
                "observability": "Cloudflare logs/analytics with Enki privacy filters",
                "backup_dr": "D1 export/backup design plus R2 evidence copies",
                "support": "Cloudflare platform plus Enki operator runbook",
            },
            zero_cost_prototype_possible=True,
            estimated_monthly_cost_range_usd=[0, 25],
            cost_model_assumptions=[
                "Low-volume architecture rehearsal remains within published free allowances",
                "Estimate is an Enki planning range, not a provider quote or production guarantee",
                "Production backup, security, support, and compliance features may introduce cost",
            ],
            strengths=[
                "Strongest literal zero-cost prototype candidate in the evaluated set",
                "One-provider operational surface and low egress friction between D1/R2/Workers",
                "R2 internet egress model is favorable for portable evidence export",
            ],
            risks=[
                "Current Python/Pydantic service boundary would require runtime adaptation or a service split",
                "D1 SQLite semantics may require data-access redesign relative to a Postgres-oriented deployment",
                "Single-provider failure and control-plane concentration remain material",
            ],
            disqualifiers=[
                "Disqualify if preserving the current Python runtime without adaptation is mandatory",
                "Disqualify if production requirements mandate database capabilities unavailable in the selected D1 design",
            ],
            prerequisite_mapping=_prerequisite_mapping(note="Cloudflare-native architecture selected in principle"),
        ),
        HostingOption(
            option_id="GCP-NATIVE",
            name="Google Cloud single-cloud serverless deployment",
            pattern=ArchitecturePattern.SINGLE_CLOUD,
            providers=["Google Cloud"],
            components={
                "compute": "Cloud Run",
                "canonical_data": "Firestore candidate",
                "evidence_object_store": "Cloud Storage",
                "identity": "Google Cloud IAM / workload identity",
                "key_custody": "Cloud KMS candidate",
                "secrets": "Secret Manager candidate",
                "network": "VPC / private service controls candidate",
                "observability": "Cloud Logging/Monitoring with Enki privacy filters",
                "backup_dr": "Firestore/Cloud Storage backup and restore design",
                "support": "Google Cloud platform plus Enki operator runbook",
            },
            zero_cost_prototype_possible=True,
            estimated_monthly_cost_range_usd=[0, 50],
            cost_model_assumptions=[
                "Low-volume rehearsal remains within published Cloud Run, Firestore, and Storage free allowances",
                "Billing guardrails are mandatory because free quotas are not a production cost ceiling",
                "Firestore backup/PITR/restore features are outside free usage",
            ],
            strengths=[
                "Cloud Run is the closest single-cloud fit for the current Python service shape",
                "Mature IAM, network, key, secret, logging, and managed-service portfolio",
                "Single-provider operational ownership simplifies incident routing",
            ],
            risks=[
                "Firestore requires data-model adaptation and does not preserve relational Postgres semantics",
                "Free quota does not validate production backup, recovery, or isolation controls",
                "Single-provider blast radius and vendor coupling remain",
            ],
            disqualifiers=[
                "Disqualify if canonical storage must retain relational SQL semantics without a managed Postgres cost",
            ],
            prerequisite_mapping=_prerequisite_mapping(note="Google Cloud single-cloud architecture selected in principle"),
        ),
        HostingOption(
            option_id="AWS-NATIVE",
            name="AWS single-cloud serverless deployment",
            pattern=ArchitecturePattern.SINGLE_CLOUD,
            providers=["AWS"],
            components={
                "compute": "Lambda",
                "canonical_data": "DynamoDB candidate",
                "evidence_object_store": "S3 candidate",
                "identity": "IAM",
                "key_custody": "KMS candidate",
                "secrets": "Secrets Manager or Parameter Store candidate",
                "network": "VPC/private endpoints candidate",
                "observability": "CloudWatch with Enki privacy filters",
                "backup_dr": "DynamoDB/S3 backup and restore design",
                "support": "AWS platform plus Enki operator runbook",
            },
            zero_cost_prototype_possible=False,
            estimated_monthly_cost_range_usd=[1, 50],
            cost_model_assumptions=[
                "Lambda and DynamoDB have substantial published free allowances",
                "Strict absolute-zero operation is not assumed because storage, networking, backup, or adjacent services can create charges",
                "Estimate is a low-volume planning range, not a provider quote",
            ],
            strengths=[
                "Broadest mature service portfolio among evaluated single-cloud options",
                "Strong IAM and multi-account isolation patterns are available for later validation",
                "Lambda and DynamoDB support highly elastic low-volume workloads",
            ],
            risks=[
                "Largest application and data-model adaptation among shortlisted single-cloud designs",
                "IAM and account topology can become operationally complex",
                "Managed security, backup, and network controls can violate the absolute-zero constraint",
            ],
            disqualifiers=[
                "Disqualify for the current zero-dollar execution phase if any mandatory component cannot be hard-capped at zero spend",
            ],
            prerequisite_mapping=_prerequisite_mapping(note="AWS single-cloud architecture selected in principle"),
        ),
        HostingOption(
            option_id="CF-NEON-R2",
            name="Provider-split edge runtime with Postgres canonical custody",
            pattern=ArchitecturePattern.PROVIDER_SPLIT,
            providers=["Cloudflare", "Neon"],
            components={
                "compute": "Cloudflare Workers",
                "canonical_data": "Neon Postgres",
                "evidence_object_store": "Cloudflare R2",
                "identity": "Application-scoped identity with provider-specific workload credentials",
                "key_custody": "Provider/application split; production model unresolved",
                "secrets": "Workers secrets plus Neon credentials",
                "network": "Public TLS database path on free-tier prototype; private path unresolved",
                "observability": "Provider telemetry normalized through Enki privacy-safe correlation",
                "backup_dr": "Postgres logical export and governed evidence copies to R2",
                "support": "Two-provider incident and escalation runbook",
            },
            zero_cost_prototype_possible=True,
            estimated_monthly_cost_range_usd=[0, 30],
            cost_model_assumptions=[
                "Prototype remains inside Workers, Neon Free, and R2 free allowances",
                "No paid private networking or premium support is assumed",
                "Cross-provider latency and operational labor are not represented as zero economic cost",
            ],
            strengths=[
                "Separates edge compute from canonical relational data custody",
                "Preserves Postgres semantics for the canonical store",
                "R2 provides a distinct evidence/export plane with favorable egress characteristics",
            ],
            risks=[
                "Workers runtime adaptation remains necessary for the current Python service",
                "Free-tier Neon connectivity does not prove private production networking",
                "Cross-provider identity, secret rotation, incident ownership, and latency become more complex",
            ],
            disqualifiers=[
                "Disqualify if public TLS database connectivity is unacceptable even for non-production validation",
                "Disqualify if two-provider operational ownership exceeds available support capacity",
            ],
            prerequisite_mapping=_prerequisite_mapping(note="Cloudflare/Neon provider split selected in principle"),
        ),
        HostingOption(
            option_id="GCP-NEON-R2",
            name="Control-plane/data-plane split preserving the current Python runtime",
            pattern=ArchitecturePattern.CONTROL_DATA_SPLIT,
            providers=["Google Cloud", "Neon", "Cloudflare"],
            components={
                "compute": "Google Cloud Run",
                "canonical_data": "Neon Postgres",
                "evidence_object_store": "Cloudflare R2",
                "identity": "Google workload identity plus scoped external service credentials",
                "key_custody": "Separated application/data/evidence custody model to be validated",
                "secrets": "Google Secret Manager candidate plus scoped Neon/R2 credentials",
                "network": "Cloud Run outbound TLS to data/evidence providers; private production paths unresolved",
                "observability": "Cloud Run telemetry with Enki correlation and provider-specific evidence",
                "backup_dr": "Postgres export to independent R2 evidence/DR plane",
                "support": "Three-provider failure-domain and escalation runbook",
            },
            zero_cost_prototype_possible=True,
            estimated_monthly_cost_range_usd=[0, 50],
            cost_model_assumptions=[
                "Low-volume rehearsal stays within Cloud Run, Neon Free, and R2 free allowances",
                "Estimate excludes paid private networking, premium support, and independent security testing",
                "Cross-provider egress and request volume must be measured before any production decision",
            ],
            strengths=[
                "Lowest-change split-cloud path for the existing Python/Pydantic application boundary",
                "Canonical Postgres custody is separated from runtime provider",
                "Independent evidence/object plane improves portability and exit options",
            ],
            risks=[
                "Highest provider-count and operational coordination burden among finalists",
                "Cross-cloud egress, latency, secret distribution, and failure correlation require validation",
                "Free-tier connectivity does not establish production private networking or key custody",
            ],
            disqualifiers=[
                "Disqualify if three-provider incident ownership is not operationally supportable",
                "Disqualify if measured cross-cloud latency or egress dominates the workload",
            ],
            prerequisite_mapping=_prerequisite_mapping(note="GCP/Neon/R2 control-data split selected in principle"),
        ),
        HostingOption(
            option_id="PORTABLE-CONTAINER-POSTGRES-OBJECT",
            name="Portability-first container, Postgres, and object-store abstraction",
            pattern=ArchitecturePattern.PORTABILITY_HYBRID,
            providers=["Provider-neutral"],
            components={
                "compute": "OCI-compatible container runtime",
                "canonical_data": "Postgres-compatible managed or self-hosted service",
                "evidence_object_store": "S3-compatible object store",
                "identity": "OIDC/workload identity abstraction",
                "key_custody": "Provider-neutral envelope-encryption interface",
                "secrets": "Provider-neutral secret reference interface",
                "network": "Provider-specific private networking behind portability contract",
                "observability": "OpenTelemetry-compatible privacy-filtered telemetry",
                "backup_dr": "Portable logical backups and immutable object evidence",
                "support": "Explicit provider adapter ownership",
            },
            zero_cost_prototype_possible=True,
            estimated_monthly_cost_range_usd=[0, 75],
            cost_model_assumptions=[
                "Repository-local and free-tier adapters can prove portability contracts at zero spend",
                "Actual hosted implementation inherits the selected providers' costs",
                "Portability reduces exit coupling but increases adapter maintenance cost",
            ],
            strengths=[
                "Best long-term provider exit posture",
                "Preserves current container and relational data assumptions",
                "Makes hosting selection replaceable behind explicit infrastructure contracts",
            ],
            risks=[
                "Abstraction can conceal provider-specific security or reliability semantics",
                "More adapter code and conformance testing are required",
                "Does not eliminate the need to validate one concrete production deployment",
            ],
            disqualifiers=[
                "Disqualify if adapter maintenance cost exceeds the value of portability",
            ],
            prerequisite_mapping=_prerequisite_mapping(note="portable provider-neutral pattern selected in principle"),
        ),
    ]

    payload = {
        "schema_version": 1,
        "package_version": "enki-hosting-options-v1",
        "external_services_budget_usd": 0,
        "researched_at": datetime(2026, 7, 15, 20, 30, tzinfo=timezone.utc),
        "evidence_sources": sources,
        "options": options,
        "shortlist_option_ids": ["CF-NATIVE", "CF-NEON-R2", "GCP-NEON-R2"],
        "recommendation": (
            "Retain three finalists for human direction: CF-NATIVE for the lowest-operations zero-cost prototype, "
            "CF-NEON-R2 for explicit provider separation with relational canonical custody, and GCP-NEON-R2 for "
            "the lowest-change split-cloud path that preserves the current Python runtime. Do not select a winner "
            "until a subsequent validation sprint measures runtime compatibility, cross-provider latency/egress, "
            "failure behavior, and the selected deployment's production-control evidence."
        ),
        "decision_state": DecisionState.HUMAN_DECISION_REQUIRED,
        "production_approval": False,
        "infrastructure_provisioned": False,
    }
    return HostingDecisionPackage(**payload, package_sha256=canonical_sha256(payload))


def hosting_decision_package_dict() -> dict[str, object]:
    return build_hosting_decision_package().model_dump(mode="json")
