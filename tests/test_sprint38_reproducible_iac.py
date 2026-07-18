import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.infrastructure_as_code import (
    ARCHITECTURE_LOCK_SHA256,
    EnvironmentAuthorityPolicy,
    EnvironmentClass,
    InfrastructureDefinition,
    InfrastructureDriftError,
    InfrastructurePackage,
    InfrastructureResource,
    LifecycleOperation,
    NoEffectInfrastructureAdapter,
    Provider,
    SecretReference,
    Service,
    execute_reproducibility_cycle,
)
from nks.application.deployment_decision_resolution import HOSTED_RC2_SHA256


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATH = ROOT / "infrastructure/enki-hosted-1.0-rc2/cf-neon-r2-iac.json"


def load_package() -> InfrastructurePackage:
    return InfrastructurePackage(**json.loads(PACKAGE_PATH.read_text(encoding="utf-8")))


def test_persisted_iac_package_binds_exact_approved_candidate_and_architecture_lock():
    package = load_package()

    assert package.definition.candidate_sha256 == HOSTED_RC2_SHA256
    assert package.definition.architecture_lock_sha256 == ARCHITECTURE_LOCK_SHA256
    assert package.definition.architecture_id == "CF-NEON-R2"
    assert package.definition.definition_sha256 == (
        "sha256:8653b4da954ad673ca486117c1085bd2a103310d0250a258892a5918859ae5af"
    )
    assert package.package_sha256 == (
        "sha256:9f782a8e394eb5125a512c213ff83167a0d88a134788ee2712af7ed3e5c275f8"
    )


def test_selected_architecture_has_only_locked_services():
    definition = load_package().definition
    actual = {(item.provider, item.service) for item in definition.resources}

    assert actual == {
        (Provider.CLOUDFLARE, Service.WORKERS),
        (Provider.NEON, Service.POSTGRES),
        (Provider.CLOUDFLARE, Service.R2),
    }
    assert set(definition.allowed_services) == {
        "CLOUDFLARE:WORKERS",
        "NEON:POSTGRES",
        "CLOUDFLARE:R2",
    }


def test_secret_bindings_are_references_only_and_environment_scoped():
    definition = load_package().definition

    assert {item.reference for item in definition.secret_references} == {
        "github-actions://CLOUDFLARE_ACCOUNT_ID",
        "github-actions://CLOUDFLARE_API_TOKEN",
        "github-actions://NEON_DATABASE_URL",
        "github-actions://NEON_API_KEY",
    }
    assert all(item.environment == EnvironmentClass.TEST for item in definition.secret_references)
    serialized = PACKAGE_PATH.read_text(encoding="utf-8")
    assert "password" not in serialized.lower()
    assert "private_key" not in serialized.lower()
    assert "secret_value" not in serialized.lower()


def test_raw_secret_value_cannot_be_substituted_for_governed_reference():
    with pytest.raises(ValidationError):
        SecretReference(
            binding_id="bad-secret",
            environment=EnvironmentClass.TEST,
            provider=Provider.CLOUDFLARE,
            reference="plaintext-secret-value",
        )


def test_test_and_production_authority_policies_are_explicit_and_separate():
    package = load_package()
    policies = {item.environment: item for item in package.environment_policies}

    assert set(policies) == {EnvironmentClass.TEST, EnvironmentClass.PRODUCTION}
    assert policies[EnvironmentClass.TEST].required_authority == (
        "EXTERNAL_TEST_CREDENTIALS_AND_TEARDOWN_AUTHORITY"
    )
    assert policies[EnvironmentClass.PRODUCTION].required_authority == (
        "EXPLICIT_HUMAN_PRODUCTION_AUTHORITY_AND_VALIDATED_PRODUCTION_CONTROLS"
    )
    assert policies[EnvironmentClass.TEST].provider_execution_enabled is False
    assert policies[EnvironmentClass.PRODUCTION].provider_execution_enabled is False
    assert all(item.external_services_budget_usd == 0 for item in policies.values())
    assert all(item.permits_production_data is False for item in policies.values())
    assert all(item.permits_production_effects is False for item in policies.values())


def test_sprint38_cannot_enable_production_provider_execution():
    with pytest.raises(ValidationError, match="production provider execution"):
        EnvironmentAuthorityPolicy(
            environment=EnvironmentClass.PRODUCTION,
            provider_execution_enabled=True,
            required_authority="not-enough",
            external_services_budget_usd=0,
            permits_production_data=False,
            permits_production_effects=False,
        )


def test_lifecycle_is_complete_ordered_and_zero_cost():
    definition = load_package().definition

    assert definition.lifecycle_operations == (
        LifecycleOperation.PLAN,
        LifecycleOperation.CREATE,
        LifecycleOperation.VERIFY,
        LifecycleOperation.TEARDOWN,
        LifecycleOperation.REBUILD,
    )
    assert definition.external_services_budget_usd == 0
    assert all(item.cost_ceiling_usd == 0 for item in definition.resources)
    assert all(item.teardown_required is True for item in definition.resources)


def test_create_verify_teardown_and_clean_rebuild_are_deterministic():
    definition = load_package().definition
    adapter = NoEffectInfrastructureAdapter()

    cycle = execute_reproducibility_cycle(definition, adapter)

    assert cycle.deterministic_rebuild is True
    assert cycle.initial_snapshot == cycle.verified_snapshot
    assert cycle.rebuilt_snapshot == cycle.rebuilt_verified_snapshot
    assert (
        cycle.initial_snapshot.state_fingerprint_sha256
        == cycle.rebuilt_snapshot.state_fingerprint_sha256
    )
    assert cycle.teardown.final_snapshot.active_resource_ids == ()
    assert cycle.teardown.final_snapshot.service_keys == ()
    assert cycle.teardown.export_manifest_sha256.startswith("sha256:")
    assert cycle.external_effect_count == 0
    assert cycle.teardown.external_effect_count == 0
    assert adapter.external_effect_count == 0


def test_repeat_cycles_produce_identical_reconstructable_proof():
    definition = load_package().definition

    first = execute_reproducibility_cycle(definition)
    second = execute_reproducibility_cycle(definition)

    assert first.cycle_sha256 == second.cycle_sha256
    assert first.teardown.export_manifest_sha256 == second.teardown.export_manifest_sha256
    assert first.initial_snapshot.state_fingerprint_sha256 == second.initial_snapshot.state_fingerprint_sha256


def test_undeclared_provider_service_fails_closed():
    definition = load_package().definition
    adapter = NoEffectInfrastructureAdapter()
    adapter.create(definition)

    with pytest.raises(InfrastructureDriftError, match="undeclared"):
        adapter.verify(
            definition,
            observed_service_keys=(
                "CLOUDFLARE:WORKERS",
                "CLOUDFLARE:R2",
                "NEON:POSTGRES",
                "CLOUDFLARE:D1",
            ),
        )


def test_missing_provider_service_fails_closed():
    definition = load_package().definition
    adapter = NoEffectInfrastructureAdapter()
    adapter.create(definition)

    with pytest.raises(InfrastructureDriftError, match="missing"):
        adapter.verify(
            definition,
            observed_service_keys=("CLOUDFLARE:WORKERS", "CLOUDFLARE:R2"),
        )


def test_verify_after_teardown_fails_closed_on_missing_resources():
    definition = load_package().definition
    adapter = NoEffectInfrastructureAdapter()
    adapter.create(definition)
    adapter.teardown(definition)

    with pytest.raises(InfrastructureDriftError, match="active resources"):
        adapter.verify(definition)


def test_extra_locked_architecture_service_is_rejected_at_definition_boundary():
    package = load_package()
    definition = package.definition
    payload = definition.model_dump(mode="python", exclude={"definition_sha256"})
    payload["resources"] = tuple(definition.resources) + (
        InfrastructureResource(
            resource_id="undeclared-d1",
            provider=Provider.CLOUDFLARE,
            service=Service.POSTGRES,
            environment=EnvironmentClass.TEST,
            role="undeclared replacement",
            declared=True,
            cost_ceiling_usd=0,
            teardown_required=True,
        ),
    )

    with pytest.raises(ValidationError, match="does not match CF-NEON-R2 service set"):
        InfrastructureDefinition.create(**payload)


def test_definition_hash_tampering_is_rejected():
    definition = load_package().definition
    payload = definition.model_dump(mode="python")
    payload["definition_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(ValidationError, match="definition hash is invalid"):
        InfrastructureDefinition(**payload)


def test_package_hash_tampering_is_rejected():
    package = load_package()
    payload = package.model_dump(mode="python")
    payload["package_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(ValidationError, match="package hash is invalid"):
        InfrastructurePackage(**payload)
