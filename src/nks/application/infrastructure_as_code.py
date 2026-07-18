"""Provider-bound, no-effect Infrastructure-as-Code contracts for Enki Sprint 38.

The selected RC2 architecture is represented as deterministic declarations that can be
validated without provider credentials.  The no-effect adapter proves lifecycle and
drift semantics locally while preserving the boundary that real Cloudflare/Neon
provisioning requires separately supplied TEST credentials and teardown authority.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.deployment_decision_resolution import (
    HOSTED_RC2_SHA256,
    HOSTED_RC2_VERSION,
    REFERENCE_ARCHITECTURE_ID,
)


ARCHITECTURE_LOCK_SHA256 = (
    "sha256:8b79cdbcafd9080a22471fa12e3a176ee1da9963471fa494b90dca62af0d4813"
)


class EnvironmentClass(StrEnum):
    TEST = "TEST"
    PRODUCTION = "PRODUCTION"


class Provider(StrEnum):
    CLOUDFLARE = "CLOUDFLARE"
    NEON = "NEON"


class Service(StrEnum):
    WORKERS = "WORKERS"
    POSTGRES = "POSTGRES"
    R2 = "R2"


class LifecycleOperation(StrEnum):
    PLAN = "PLAN"
    CREATE = "CREATE"
    VERIFY = "VERIFY"
    TEARDOWN = "TEARDOWN"
    REBUILD = "REBUILD"


EXPECTED_SERVICE_SET = frozenset(
    {
        (Provider.CLOUDFLARE, Service.WORKERS),
        (Provider.NEON, Service.POSTGRES),
        (Provider.CLOUDFLARE, Service.R2),
    }
)


class InfrastructureError(RuntimeError):
    """Base fail-closed infrastructure contract error."""


class InfrastructureAuthorityError(InfrastructureError):
    """Raised when an operation lacks environment authority."""


class InfrastructureDriftError(InfrastructureError):
    """Raised when observed infrastructure differs from the declaration."""


class SecretReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    binding_id: str = Field(min_length=1)
    environment: EnvironmentClass
    provider: Provider
    reference: str = Field(pattern=r"^github-actions://[A-Z][A-Z0-9_]*$")


class InfrastructureResource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    resource_id: str = Field(min_length=1)
    provider: Provider
    service: Service
    environment: EnvironmentClass
    role: str = Field(min_length=1)
    declared: Literal[True] = True
    cost_ceiling_usd: Literal[0] = 0
    teardown_required: Literal[True] = True

    @property
    def service_key(self) -> tuple[Provider, Service]:
        return self.provider, self.service


class EnvironmentAuthorityPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    environment: EnvironmentClass
    provider_execution_enabled: bool
    required_authority: str = Field(min_length=1)
    external_services_budget_usd: Literal[0] = 0
    permits_production_data: Literal[False] = False
    permits_production_effects: Literal[False] = False

    @model_validator(mode="after")
    def validate_policy(self) -> "EnvironmentAuthorityPolicy":
        if self.environment == EnvironmentClass.PRODUCTION and self.provider_execution_enabled:
            raise ValueError("production provider execution cannot be enabled by Sprint 38")
        return self


class InfrastructureDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    definition_id: Literal["IAC-enki-hosted-1.0-rc2-CF-NEON-R2-TEST"] = (
        "IAC-enki-hosted-1.0-rc2-CF-NEON-R2-TEST"
    )
    candidate_version: Literal[HOSTED_RC2_VERSION] = HOSTED_RC2_VERSION
    candidate_sha256: Literal[HOSTED_RC2_SHA256] = HOSTED_RC2_SHA256
    architecture_lock_sha256: Literal[ARCHITECTURE_LOCK_SHA256] = ARCHITECTURE_LOCK_SHA256
    architecture_id: Literal[REFERENCE_ARCHITECTURE_ID] = REFERENCE_ARCHITECTURE_ID
    environment: Literal[EnvironmentClass.TEST] = EnvironmentClass.TEST
    resources: tuple[InfrastructureResource, ...]
    secret_references: tuple[SecretReference, ...]
    allowed_services: tuple[str, ...]
    lifecycle_operations: tuple[LifecycleOperation, ...] = (
        LifecycleOperation.PLAN,
        LifecycleOperation.CREATE,
        LifecycleOperation.VERIFY,
        LifecycleOperation.TEARDOWN,
        LifecycleOperation.REBUILD,
    )
    production_execution_authorized: Literal[False] = False
    external_services_budget_usd: Literal[0] = 0
    definition_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_definition(self) -> "InfrastructureDefinition":
        resource_ids = [item.resource_id for item in self.resources]
        if len(resource_ids) != len(set(resource_ids)):
            raise ValueError("infrastructure resource identifiers must be unique")

        actual_services = frozenset(item.service_key for item in self.resources)
        if actual_services != EXPECTED_SERVICE_SET:
            raise ValueError("infrastructure definition does not match CF-NEON-R2 service set")

        if any(item.environment != self.environment for item in self.resources):
            raise ValueError("resource environment does not match infrastructure definition")

        binding_ids = [item.binding_id for item in self.secret_references]
        if len(binding_ids) != len(set(binding_ids)):
            raise ValueError("secret binding identifiers must be unique")
        if any(item.environment != self.environment for item in self.secret_references):
            raise ValueError("secret reference environment does not match infrastructure definition")

        expected_allowed = tuple(
            sorted(f"{provider.value}:{service.value}" for provider, service in EXPECTED_SERVICE_SET)
        )
        if tuple(sorted(self.allowed_services)) != expected_allowed:
            raise ValueError("allowed services must exactly match the locked architecture")

        expected_operations = (
            LifecycleOperation.PLAN,
            LifecycleOperation.CREATE,
            LifecycleOperation.VERIFY,
            LifecycleOperation.TEARDOWN,
            LifecycleOperation.REBUILD,
        )
        if self.lifecycle_operations != expected_operations:
            raise ValueError("infrastructure lifecycle operations are incomplete or reordered")

        expected_hash = canonical_sha256(
            self.model_dump(mode="python", exclude={"definition_sha256"})
        )
        if self.definition_sha256 != expected_hash:
            raise ValueError("infrastructure definition hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "InfrastructureDefinition":
        payload = {
            "schema_version": 1,
            "definition_id": "IAC-enki-hosted-1.0-rc2-CF-NEON-R2-TEST",
            "candidate_version": HOSTED_RC2_VERSION,
            "candidate_sha256": HOSTED_RC2_SHA256,
            "architecture_lock_sha256": ARCHITECTURE_LOCK_SHA256,
            "architecture_id": REFERENCE_ARCHITECTURE_ID,
            "environment": EnvironmentClass.TEST,
            "lifecycle_operations": (
                LifecycleOperation.PLAN,
                LifecycleOperation.CREATE,
                LifecycleOperation.VERIFY,
                LifecycleOperation.TEARDOWN,
                LifecycleOperation.REBUILD,
            ),
            "production_execution_authorized": False,
            "external_services_budget_usd": 0,
            **values,
        }
        payload["definition_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class InfrastructurePackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    package_id: Literal["IAC-PACKAGE-enki-hosted-1.0-rc2"] = (
        "IAC-PACKAGE-enki-hosted-1.0-rc2"
    )
    definition: InfrastructureDefinition
    environment_policies: tuple[EnvironmentAuthorityPolicy, ...]
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_package(self) -> "InfrastructurePackage":
        by_environment = {item.environment: item for item in self.environment_policies}
        if set(by_environment) != {EnvironmentClass.TEST, EnvironmentClass.PRODUCTION}:
            raise ValueError("TEST and PRODUCTION authority policies are both required")
        if by_environment[EnvironmentClass.PRODUCTION].provider_execution_enabled:
            raise ValueError("production provider execution must remain disabled")
        expected_hash = canonical_sha256(
            self.model_dump(mode="python", exclude={"package_sha256"})
        )
        if self.package_sha256 != expected_hash:
            raise ValueError("infrastructure package hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "InfrastructurePackage":
        payload = {
            "schema_version": 1,
            "package_id": "IAC-PACKAGE-enki-hosted-1.0-rc2",
            **values,
        }
        payload["package_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class EnvironmentSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    definition_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    environment: EnvironmentClass
    active_resource_ids: tuple[str, ...]
    service_keys: tuple[str, ...]
    state_fingerprint_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @classmethod
    def create(
        cls,
        definition: InfrastructureDefinition,
        *,
        active_resource_ids: tuple[str, ...],
        service_keys: tuple[str, ...],
    ) -> "EnvironmentSnapshot":
        canonical_resources = tuple(sorted(active_resource_ids))
        canonical_services = tuple(sorted(service_keys))
        fingerprint = canonical_sha256(
            {
                "definition_sha256": definition.definition_sha256,
                "environment": definition.environment,
                "active_resource_ids": canonical_resources,
                "service_keys": canonical_services,
            }
        )
        return cls(
            definition_sha256=definition.definition_sha256,
            environment=definition.environment,
            active_resource_ids=canonical_resources,
            service_keys=canonical_services,
            state_fingerprint_sha256=fingerprint,
        )


class TeardownResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    export_manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    final_snapshot: EnvironmentSnapshot
    external_effect_count: Literal[0] = 0


class ReproducibilityCycle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_snapshot: EnvironmentSnapshot
    verified_snapshot: EnvironmentSnapshot
    teardown: TeardownResult
    rebuilt_snapshot: EnvironmentSnapshot
    rebuilt_verified_snapshot: EnvironmentSnapshot
    deterministic_rebuild: bool
    external_effect_count: Literal[0] = 0
    cycle_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_cycle(self) -> "ReproducibilityCycle":
        expected = self.initial_snapshot.state_fingerprint_sha256 == self.rebuilt_snapshot.state_fingerprint_sha256
        if self.deterministic_rebuild != expected:
            raise ValueError("deterministic rebuild flag does not match observed fingerprints")
        if not self.deterministic_rebuild:
            raise ValueError("clean rebuild did not reproduce the declared environment")
        expected_hash = canonical_sha256(
            self.model_dump(mode="python", exclude={"cycle_sha256"})
        )
        if self.cycle_sha256 != expected_hash:
            raise ValueError("reproducibility cycle hash is invalid")
        return self


class NoEffectInfrastructureAdapter:
    """Credential-free TEST adapter incapable of creating provider-side resources."""

    def __init__(self) -> None:
        self._active_resource_ids: set[str] = set()
        self.external_effect_count = 0

    @staticmethod
    def _service_keys(definition: InfrastructureDefinition) -> tuple[str, ...]:
        return tuple(
            sorted(f"{item.provider.value}:{item.service.value}" for item in definition.resources)
        )

    def _snapshot(self, definition: InfrastructureDefinition) -> EnvironmentSnapshot:
        active = tuple(sorted(self._active_resource_ids))
        active_services = tuple(
            sorted(
                f"{item.provider.value}:{item.service.value}"
                for item in definition.resources
                if item.resource_id in self._active_resource_ids
            )
        )
        return EnvironmentSnapshot.create(
            definition,
            active_resource_ids=active,
            service_keys=active_services,
        )

    @staticmethod
    def _require_test(definition: InfrastructureDefinition) -> None:
        if definition.environment != EnvironmentClass.TEST:
            raise InfrastructureAuthorityError("no-effect Sprint 38 lifecycle is TEST-only")
        if definition.production_execution_authorized:
            raise InfrastructureAuthorityError("production execution authority is prohibited")

    def create(self, definition: InfrastructureDefinition) -> EnvironmentSnapshot:
        self._require_test(definition)
        self._active_resource_ids = {item.resource_id for item in definition.resources}
        return self._snapshot(definition)

    def verify(
        self,
        definition: InfrastructureDefinition,
        *,
        observed_service_keys: tuple[str, ...] | None = None,
    ) -> EnvironmentSnapshot:
        self._require_test(definition)
        expected_resources = {item.resource_id for item in definition.resources}
        if self._active_resource_ids != expected_resources:
            raise InfrastructureDriftError("active resources differ from the declared definition")

        expected_services = set(self._service_keys(definition))
        observed = set(observed_service_keys or self._service_keys(definition))
        if observed != expected_services:
            missing = sorted(expected_services - observed)
            undeclared = sorted(observed - expected_services)
            raise InfrastructureDriftError(
                f"service drift detected; missing={missing} undeclared={undeclared}"
            )
        return self._snapshot(definition)

    def teardown(self, definition: InfrastructureDefinition) -> TeardownResult:
        self._require_test(definition)
        before = self._snapshot(definition)
        export_manifest_sha256 = canonical_sha256(
            {
                "definition_sha256": definition.definition_sha256,
                "active_resource_ids": before.active_resource_ids,
                "service_keys": before.service_keys,
                "purpose": "reconstructable-pre-teardown-export",
            }
        )
        self._active_resource_ids.clear()
        return TeardownResult(
            export_manifest_sha256=export_manifest_sha256,
            final_snapshot=self._snapshot(definition),
            external_effect_count=0,
        )


def execute_reproducibility_cycle(
    definition: InfrastructureDefinition,
    adapter: NoEffectInfrastructureAdapter | None = None,
) -> ReproducibilityCycle:
    """Execute deterministic create/verify/teardown/clean-rebuild with zero external effects."""

    selected_adapter = adapter or NoEffectInfrastructureAdapter()
    initial = selected_adapter.create(definition)
    verified = selected_adapter.verify(definition)
    teardown = selected_adapter.teardown(definition)
    rebuilt = selected_adapter.create(definition)
    rebuilt_verified = selected_adapter.verify(definition)
    deterministic = initial.state_fingerprint_sha256 == rebuilt.state_fingerprint_sha256
    payload = {
        "initial_snapshot": initial,
        "verified_snapshot": verified,
        "teardown": teardown,
        "rebuilt_snapshot": rebuilt,
        "rebuilt_verified_snapshot": rebuilt_verified,
        "deterministic_rebuild": deterministic,
        "external_effect_count": 0,
    }
    return ReproducibilityCycle(
        **payload,
        cycle_sha256=canonical_sha256(payload),
    )
