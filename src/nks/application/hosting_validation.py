"""Governed non-production hosting validation program for Enki.

This module converts the Sprint 24 hosting shortlist and the explicit
VALIDATE_MULTIPLE_FINALISTS decision into deterministic TEST-only validation plans.
It does not provision infrastructure, hold provider credentials, or create production
approval. Hosted execution remains capability-gated on externally supplied TEST credentials.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator


FINALISTS = ("CF-NATIVE", "CF-NEON-R2", "GCP-NEON-R2")
REQUIRED_BOUNDARIES = (
    "namespace",
    "tenant",
    "subject",
    "domain",
    "audience",
    "execution_context",
)
REQUIRED_PRODUCTION_PREREQUISITES = (
    "cloud-iam",
    "production-identity-federation",
    "managed-database-row-level-isolation",
    "network-segmentation",
    "per-tenant-production-key-management",
    "production-secrets-management",
    "independent-penetration-testing",
)


class ValidationPhase(StrEnum):
    PREFLIGHT = "PREFLIGHT"
    DEPLOY_TEST_RUNTIME = "DEPLOY_TEST_RUNTIME"
    IMPORT_SYNTHETIC_FIXTURES = "IMPORT_SYNTHETIC_FIXTURES"
    BOUNDARY_ISOLATION = "BOUNDARY_ISOLATION"
    TRANSACTION_RECOVERY = "TRANSACTION_RECOVERY"
    PORTABILITY_RECONSTRUCTION = "PORTABILITY_RECONSTRUCTION"
    PRIVACY_OBSERVABILITY = "PRIVACY_OBSERVABILITY"
    FAILURE_INJECTION = "FAILURE_INJECTION"
    COST_AND_QUOTA_CAPTURE = "COST_AND_QUOTA_CAPTURE"
    TEARDOWN_AND_RECONSTRUCT = "TEARDOWN_AND_RECONSTRUCT"


class HostedExecutionState(StrEnum):
    READY = "READY_FOR_HOSTED_TEST_EXECUTION"
    BLOCKED_EXTERNAL_CAPABILITY = "BLOCKED_EXTERNAL_CAPABILITY"


class FinalistValidationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    option_id: str = Field(min_length=1)
    providers: tuple[str, ...] = Field(min_length=1)
    phases: tuple[ValidationPhase, ...]
    required_boundaries: tuple[str, ...]
    unresolved_production_prerequisites: tuple[str, ...]
    production_approval: Literal[False] = False

    @model_validator(mode="after")
    def validate_plan(self) -> "FinalistValidationPlan":
        if self.option_id not in FINALISTS:
            raise ValueError("validation plan references a non-finalist architecture")
        if self.phases != tuple(ValidationPhase):
            raise ValueError("every finalist must execute the complete ordered validation phase set")
        if self.required_boundaries != REQUIRED_BOUNDARIES:
            raise ValueError("every finalist must validate the complete boundary set")
        if self.unresolved_production_prerequisites != REQUIRED_PRODUCTION_PREREQUISITES:
            raise ValueError("production prerequisites must remain explicit and unresolved")
        return self


class HostedValidationProgram(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["enki-hosting-validation-v1"] = "enki-hosting-validation-v1"
    decision: Literal["VALIDATE_MULTIPLE_FINALISTS"] = "VALIDATE_MULTIPLE_FINALISTS"
    execution_context: Literal["TEST"] = "TEST"
    external_services_budget_usd: Literal[0] = 0
    hosted_execution_requires_external_credentials: Literal[True] = True
    production_data_allowed: Literal[False] = False
    production_credentials_allowed: Literal[False] = False
    production_approval: Literal[False] = False
    plans: tuple[FinalistValidationPlan, ...] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_program(self) -> "HostedValidationProgram":
        option_ids = tuple(plan.option_id for plan in self.plans)
        if option_ids != FINALISTS:
            raise ValueError("program must validate each finalist exactly once in canonical order")
        return self


class HostedValidationPreflight(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    option_id: str
    state: HostedExecutionState
    missing_capabilities: tuple[str, ...]
    execution_context: Literal["TEST"] = "TEST"
    production_approval: Literal[False] = False


def build_hosting_validation_program() -> HostedValidationProgram:
    providers = {
        "CF-NATIVE": ("Cloudflare",),
        "CF-NEON-R2": ("Cloudflare", "Neon"),
        "GCP-NEON-R2": ("Google Cloud", "Neon", "Cloudflare"),
    }
    phases = tuple(ValidationPhase)
    plans = tuple(
        FinalistValidationPlan(
            option_id=option_id,
            providers=providers[option_id],
            phases=phases,
            required_boundaries=REQUIRED_BOUNDARIES,
            unresolved_production_prerequisites=REQUIRED_PRODUCTION_PREREQUISITES,
        )
        for option_id in FINALISTS
    )
    return HostedValidationProgram(plans=plans)


def evaluate_hosted_preflight(
    option_id: str,
    capabilities: Mapping[str, bool],
) -> HostedValidationPreflight:
    """Evaluate whether a finalist may begin hosted TEST execution.

    Capability names are intentionally provider-neutral. The caller must prove all
    required capabilities with TEST-only credentials before hosted deployment begins.
    """

    if option_id not in FINALISTS:
        raise ValueError(f"unknown hosting finalist: {option_id}")

    required = ("provider_test_identity", "provider_test_credentials", "teardown_authority")
    missing = tuple(name for name in required if not capabilities.get(name, False))
    state = (
        HostedExecutionState.BLOCKED_EXTERNAL_CAPABILITY
        if missing
        else HostedExecutionState.READY
    )
    return HostedValidationPreflight(
        option_id=option_id,
        state=state,
        missing_capabilities=missing,
    )
