"""Provider-neutral production-control validation readiness for Enki.

Sprint 35 prepares exact validation contracts without manufacturing production
evidence. TEST substitutes may exercise contract mechanics, but can never satisfy a
PRODUCTION gate. Missing external capabilities fail closed as explicit blockers rather
than reopening architecture design or silently weakening controls.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext


class HostingFinalist(StrEnum):
    CF_NATIVE = "CF-NATIVE"
    CF_NEON_R2 = "CF-NEON-R2"
    GCP_NEON_R2 = "GCP-NEON-R2"


class ProductionControl(StrEnum):
    CLOUD_IAM = "cloud-iam"
    PRODUCTION_IDENTITY_FEDERATION = "production-identity-federation"
    MANAGED_DATABASE_ROW_LEVEL_ISOLATION = "managed-database-row-level-isolation"
    NETWORK_SEGMENTATION = "network-segmentation"
    PER_TENANT_PRODUCTION_KEY_MANAGEMENT = "per-tenant-production-key-management"
    PRODUCTION_SECRETS_MANAGEMENT = "production-secrets-management"
    INDEPENDENT_PENETRATION_TESTING = "independent-penetration-testing"


class ResponsibilityParty(StrEnum):
    PROVIDER = "PROVIDER"
    ENKI = "ENKI"
    SHARED = "SHARED"
    INDEPENDENT_THIRD_PARTY = "INDEPENDENT_THIRD_PARTY"
    HUMAN_AUTHORITY = "HUMAN_AUTHORITY"


class EvidenceClass(StrEnum):
    CONFIGURATION_EXPORT = "CONFIGURATION_EXPORT"
    POLICY_EXPORT = "POLICY_EXPORT"
    ACCESS_TEST = "ACCESS_TEST"
    DENIAL_TEST = "DENIAL_TEST"
    ROTATION_TEST = "ROTATION_TEST"
    RECOVERY_TEST = "RECOVERY_TEST"
    PROVIDER_ATTESTATION = "PROVIDER_ATTESTATION"
    INDEPENDENT_ASSESSMENT = "INDEPENDENT_ASSESSMENT"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class ValidationDisposition(StrEnum):
    READY_FOR_PRODUCTION_VALIDATION = "READY_FOR_PRODUCTION_VALIDATION"
    BLOCKED_MISSING_CAPABILITY = "BLOCKED_MISSING_CAPABILITY"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class EvidenceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    requirement_id: str = Field(min_length=1)
    evidence_class: EvidenceClass
    owner: ResponsibilityParty
    production_only: bool
    description: str = Field(min_length=1)


class ResponsibilityMapping(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    finalist: HostingFinalist
    provider_responsibilities: tuple[str, ...] = Field(min_length=1)
    enki_responsibilities: tuple[str, ...] = Field(min_length=1)
    evidence_owner: ResponsibilityParty
    rollback_owner: ResponsibilityParty


class ProductionControlValidationContract(BaseModel):
    """Exact contract for one production control."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    control: ProductionControl
    objective: str = Field(min_length=1)
    test_substitute: str = Field(min_length=1)
    production_validation_steps: tuple[str, ...] = Field(min_length=1)
    evidence_requirements: tuple[EvidenceRequirement, ...] = Field(min_length=1)
    responsibility_mappings: tuple[ResponsibilityMapping, ...] = Field(min_length=1)
    failure_criteria: tuple[str, ...] = Field(min_length=1)
    stop_conditions: tuple[str, ...] = Field(min_length=1)
    rollback_obligations: tuple[str, ...] = Field(min_length=1)
    required_capabilities: tuple[str, ...] = Field(min_length=1)
    contract_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_contract(self) -> "ProductionControlValidationContract":
        finalists = {item.finalist for item in self.responsibility_mappings}
        if finalists != set(HostingFinalist):
            raise ValueError("control contract must map every hosting finalist")
        requirement_ids = [item.requirement_id for item in self.evidence_requirements]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("evidence requirement ids must be unique")
        if not any(item.production_only for item in self.evidence_requirements):
            raise ValueError("production control requires production-only evidence")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"contract_sha256"})
        )
        if self.contract_sha256 != expected:
            raise ValueError("production-control contract hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ProductionControlValidationContract":
        payload = dict(values)
        payload["contract_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ValidationEvidence(BaseModel):
    """Hash-bound evidence reference; raw credentials and protected content are forbidden."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=1)
    requirement_id: str = Field(min_length=1)
    evidence_class: EvidenceClass
    execution_context: ExecutionContext
    owner: ResponsibilityParty
    artifact_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    external_effect: bool = False
    production_credential_material: bool = False

    @model_validator(mode="after")
    def reject_secret_material(self) -> "ValidationEvidence":
        if self.production_credential_material:
            raise ValueError("validation evidence cannot embed production credential material")
        return self


class ControlValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    control: ProductionControl
    requested_context: ExecutionContext
    disposition: ValidationDisposition
    satisfied_requirement_ids: tuple[str, ...]
    missing_requirement_ids: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    reason_codes: tuple[str, ...]
    production_gate_satisfied: bool
    result_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_result(self) -> "ControlValidationResult":
        if self.requested_context == ExecutionContext.TEST and self.production_gate_satisfied:
            raise ValueError("TEST result cannot satisfy a production gate")
        if self.disposition == ValidationDisposition.VALIDATED and not self.production_gate_satisfied:
            raise ValueError("VALIDATED production control requires satisfied production gate")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"result_sha256"})
        )
        if self.result_sha256 != expected:
            raise ValueError("control validation result hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ControlValidationResult":
        payload = dict(values)
        payload["result_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ProductionControlReadinessPackage(BaseModel):
    """Deterministic readiness package for later production validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: str = Field(min_length=1)
    finalists: tuple[HostingFinalist, ...]
    contracts: tuple[ProductionControlValidationContract, ...]
    production_deployment_authorized: bool = False
    production_approval: bool = False
    external_services_budget_usd: int = 0
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_package(self) -> "ProductionControlReadinessPackage":
        if set(self.finalists) != set(HostingFinalist):
            raise ValueError("unresolved hosting direction must preserve all finalists")
        controls = [item.control for item in self.contracts]
        if set(controls) != set(ProductionControl) or len(controls) != len(set(controls)):
            raise ValueError("readiness package must contain exactly all seven controls")
        if self.production_deployment_authorized or self.production_approval:
            raise ValueError("Sprint 35 cannot authorize production deployment")
        if self.external_services_budget_usd != 0:
            raise ValueError("Sprint 35 preserves the zero-dollar external-services boundary")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"package_sha256"})
        )
        if self.package_sha256 != expected:
            raise ValueError("production-control readiness package hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ProductionControlReadinessPackage":
        payload = dict(values)
        payload["package_sha256"] = canonical_sha256(payload)
        return cls(**payload)


def evaluate_control_validation(
    contract: ProductionControlValidationContract,
    *,
    requested_context: ExecutionContext,
    evidence: Iterable[ValidationEvidence],
    available_capabilities: Iterable[str],
) -> ControlValidationResult:
    """Evaluate a control without allowing TEST evidence to satisfy PRODUCTION."""

    available = set(available_capabilities)
    missing_capabilities = tuple(sorted(set(contract.required_capabilities) - available))
    requirements = {item.requirement_id: item for item in contract.evidence_requirements}
    satisfied: set[str] = set()
    reason_codes: set[str] = set()

    for item in evidence:
        requirement = requirements.get(item.requirement_id)
        if requirement is None:
            reason_codes.add("UNDECLARED_EVIDENCE_REQUIREMENT")
            continue
        if item.evidence_class != requirement.evidence_class or item.owner != requirement.owner:
            reason_codes.add("EVIDENCE_CONTRACT_MISMATCH")
            continue
        if requirement.production_only and item.execution_context != ExecutionContext.PRODUCTION:
            reason_codes.add("TEST_EVIDENCE_CANNOT_SATISFY_PRODUCTION_REQUIREMENT")
            continue
        if requested_context == ExecutionContext.TEST and item.execution_context != ExecutionContext.TEST:
            reason_codes.add("PRODUCTION_EVIDENCE_NOT_CONSUMED_BY_TEST_GATE")
            continue
        satisfied.add(item.requirement_id)

    required_ids = set(requirements)
    missing_requirements = tuple(sorted(required_ids - satisfied))

    if requested_context == ExecutionContext.TEST:
        disposition = ValidationDisposition.READY_FOR_PRODUCTION_VALIDATION
        production_gate_satisfied = False
        if missing_capabilities:
            reason_codes.add("PRODUCTION_CAPABILITY_NOT_AVAILABLE_IN_TEST")
    elif missing_capabilities:
        disposition = ValidationDisposition.BLOCKED_MISSING_CAPABILITY
        production_gate_satisfied = False
        reason_codes.add("MISSING_REQUIRED_PRODUCTION_CAPABILITY")
    elif missing_requirements:
        disposition = ValidationDisposition.FAILED
        production_gate_satisfied = False
        reason_codes.add("MISSING_REQUIRED_PRODUCTION_EVIDENCE")
    else:
        disposition = ValidationDisposition.VALIDATED
        production_gate_satisfied = True
        reason_codes.add("PRODUCTION_CONTROL_VALIDATED")

    return ControlValidationResult.create(
        control=contract.control,
        requested_context=requested_context,
        disposition=disposition,
        satisfied_requirement_ids=tuple(sorted(satisfied)),
        missing_requirement_ids=missing_requirements,
        missing_capabilities=missing_capabilities,
        reason_codes=tuple(sorted(reason_codes)),
        production_gate_satisfied=production_gate_satisfied,
    )


def _mapping(
    finalist: HostingFinalist,
    *,
    provider: tuple[str, ...],
    enki: tuple[str, ...],
    evidence_owner: ResponsibilityParty = ResponsibilityParty.SHARED,
    rollback_owner: ResponsibilityParty = ResponsibilityParty.ENKI,
) -> ResponsibilityMapping:
    return ResponsibilityMapping(
        finalist=finalist,
        provider_responsibilities=provider,
        enki_responsibilities=enki,
        evidence_owner=evidence_owner,
        rollback_owner=rollback_owner,
    )


def _requirements(prefix: str, *, independent: bool = False) -> tuple[EvidenceRequirement, ...]:
    owner = (
        ResponsibilityParty.INDEPENDENT_THIRD_PARTY
        if independent
        else ResponsibilityParty.SHARED
    )
    primary_class = (
        EvidenceClass.INDEPENDENT_ASSESSMENT
        if independent
        else EvidenceClass.CONFIGURATION_EXPORT
    )
    return (
        EvidenceRequirement(
            requirement_id=f"{prefix}-configuration",
            evidence_class=primary_class,
            owner=owner,
            production_only=True,
            description="Production-context configuration or independent assessment evidence.",
        ),
        EvidenceRequirement(
            requirement_id=f"{prefix}-denial-test",
            evidence_class=EvidenceClass.DENIAL_TEST,
            owner=ResponsibilityParty.SHARED,
            production_only=True,
            description="Production-context negative test proving the protected boundary fails closed.",
        ),
        EvidenceRequirement(
            requirement_id=f"{prefix}-rollback-test",
            evidence_class=EvidenceClass.RECOVERY_TEST,
            owner=ResponsibilityParty.ENKI,
            production_only=True,
            description="Production-context rollback or recovery evidence bound to the tested control version.",
        ),
    )


def build_production_control_contracts() -> tuple[ProductionControlValidationContract, ...]:
    """Build deterministic contracts for all unresolved Sprint 35 controls."""

    contracts: list[ProductionControlValidationContract] = []

    common_failure = (
        "required production evidence is missing, stale, unbound, or contradictory",
        "negative test demonstrates boundary widening or unauthorized access",
        "rollback cannot restore the last known governed state",
    )
    common_stop = (
        "stop before production traffic when any required capability is unavailable",
        "stop when evidence cannot be bound to the exact deployed configuration",
        "stop on authority escalation, cross-tenant leakage, or unrecoverable state",
    )
    common_rollback = (
        "revoke newly introduced production authority",
        "restore the last validated configuration",
        "preserve immutable evidence and incident lineage",
    )

    specifications: dict[ProductionControl, dict[str, object]] = {
        ProductionControl.CLOUD_IAM: {
            "objective": "Prove least-privilege cloud identities and deny unauthorized control-plane actions.",
            "test_substitute": "Local TEST authorization matrices and forged-identity denial paths.",
            "steps": ("export effective IAM policy", "exercise allow and deny matrix", "revoke identity and repeat denial test"),
            "capabilities": ("production-cloud-account", "production-iam-admin", "production-audit-log-access"),
        },
        ProductionControl.PRODUCTION_IDENTITY_FEDERATION: {
            "objective": "Prove production workload and human identities federate through an approved trust boundary.",
            "test_substitute": "TEST boundary signer and synthetic identity claims.",
            "steps": ("bind production issuer and audience", "exercise valid, expired, forged, and wrong-audience tokens", "revoke trust and verify denial"),
            "capabilities": ("production-identity-provider", "production-federation-configuration", "production-audit-log-access"),
        },
        ProductionControl.MANAGED_DATABASE_ROW_LEVEL_ISOLATION: {
            "objective": "Prove production canonical persistence prevents cross-tenant row access and mutation.",
            "test_substitute": "Provider-neutral tenant and subject boundary tests over synthetic records.",
            "steps": ("enable production row-level policy", "exercise cross-tenant read and write denials", "verify privileged bypass is separately controlled"),
            "capabilities": ("production-managed-database", "production-database-admin", "production-policy-introspection"),
        },
        ProductionControl.NETWORK_SEGMENTATION: {
            "objective": "Prove only explicitly authorized network paths can reach protected production services.",
            "test_substitute": "Local adapter allowlists and denied endpoint simulations.",
            "steps": ("capture production network policy", "probe allowed paths", "probe denied east-west and public paths"),
            "capabilities": ("production-network-control", "production-network-probe", "production-flow-logs"),
        },
        ProductionControl.PER_TENANT_PRODUCTION_KEY_MANAGEMENT: {
            "objective": "Prove tenant-scoped production keys cannot be reused across tenants and can be rotated and revoked.",
            "test_substitute": "Disposable per-tenant TEST HMAC keys with cross-tenant verification denial.",
            "steps": ("create tenant-scoped production keys", "exercise cross-tenant misuse denial", "rotate and revoke keys with recovery validation"),
            "capabilities": ("production-key-management-service", "production-key-admin", "production-key-audit-log"),
        },
        ProductionControl.PRODUCTION_SECRETS_MANAGEMENT: {
            "objective": "Prove production secrets are externally managed, scoped, rotatable, and absent from repository and telemetry.",
            "test_substitute": "Disposable TEST secrets plus repository and telemetry leak scanning.",
            "steps": ("bind secret references without embedding values", "rotate production secret", "verify revoked secret denial and telemetry redaction"),
            "capabilities": ("production-secrets-manager", "production-secret-rotation", "production-secret-audit-log"),
        },
        ProductionControl.INDEPENDENT_PENETRATION_TESTING: {
            "objective": "Obtain independent adversarial assessment of the deployed production boundary without self-attestation.",
            "test_substitute": "Internal TEST adversarial and chaos suites; explicitly non-substitutable for independent assessment.",
            "steps": ("define authorized production test scope", "execute independent assessment", "remediate findings and obtain retest evidence"),
            "capabilities": ("independent-security-assessor", "authorized-production-test-window", "production-scope-approval"),
            "independent": True,
        },
    }

    for control in ProductionControl:
        spec = specifications[control]
        independent = bool(spec.get("independent", False))
        mappings = tuple(
            _mapping(
                finalist,
                provider=(
                    "provide and operate the provider-native control surface",
                    "expose configuration and audit evidence needed for validation",
                ),
                enki=(
                    "configure least privilege and exact Enki boundary policy",
                    "run negative tests, bind evidence, and execute rollback obligations",
                ),
                evidence_owner=(
                    ResponsibilityParty.INDEPENDENT_THIRD_PARTY
                    if independent
                    else ResponsibilityParty.SHARED
                ),
                rollback_owner=(
                    ResponsibilityParty.SHARED
                    if control in {ProductionControl.NETWORK_SEGMENTATION, ProductionControl.MANAGED_DATABASE_ROW_LEVEL_ISOLATION}
                    else ResponsibilityParty.ENKI
                ),
            )
            for finalist in HostingFinalist
        )
        contracts.append(
            ProductionControlValidationContract.create(
                control=control,
                objective=spec["objective"],
                test_substitute=spec["test_substitute"],
                production_validation_steps=spec["steps"],
                evidence_requirements=_requirements(control.value, independent=independent),
                responsibility_mappings=mappings,
                failure_criteria=common_failure,
                stop_conditions=common_stop,
                rollback_obligations=common_rollback,
                required_capabilities=spec["capabilities"],
            )
        )
    return tuple(contracts)


def build_production_control_readiness_package() -> ProductionControlReadinessPackage:
    return ProductionControlReadinessPackage.create(
        decision="VALIDATE_MULTIPLE_FINALISTS",
        finalists=tuple(HostingFinalist),
        contracts=build_production_control_contracts(),
        production_deployment_authorized=False,
        production_approval=False,
        external_services_budget_usd=0,
    )


def production_control_readiness_fixture() -> dict[str, object]:
    """Deterministic machine-readable contract fixture for repository comparison."""

    return build_production_control_readiness_package().model_dump(mode="json")
