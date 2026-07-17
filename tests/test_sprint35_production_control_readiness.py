from __future__ import annotations

import pytest
from pydantic import ValidationError

from nks.application.governed_transactions import canonical_sha256
from nks.application.production_control_readiness import (
    EvidenceClass,
    HostingFinalist,
    ProductionControl,
    ProductionControlReadinessPackage,
    ResponsibilityParty,
    ValidationDisposition,
    ValidationEvidence,
    build_production_control_contracts,
    build_production_control_readiness_package,
    evaluate_control_validation,
)
from nks.application.sprint35_path_manifest import sprint35_production_control_readiness_path_manifest
from nks.governance.approvals import ExecutionContext


CONTRACTS = {item.control: item for item in build_production_control_contracts()}


def make_evidence(contract, *, context: ExecutionContext, owner_override=None):
    result = []
    for requirement in contract.evidence_requirements:
        result.append(
            ValidationEvidence(
                evidence_id=f"E-{contract.control.value}-{requirement.requirement_id}",
                requirement_id=requirement.requirement_id,
                evidence_class=requirement.evidence_class,
                execution_context=context,
                owner=owner_override or requirement.owner,
                artifact_sha256=canonical_sha256(
                    {
                        "control": contract.control.value,
                        "requirement": requirement.requirement_id,
                        "context": context.value,
                    }
                ),
                external_effect=False,
                production_credential_material=False,
            )
        )
    return result


def test_readiness_package_contains_exactly_all_seven_controls_and_three_finalists() -> None:
    package = build_production_control_readiness_package()

    assert set(item.control for item in package.contracts) == set(ProductionControl)
    assert len(package.contracts) == 7
    assert set(package.finalists) == set(HostingFinalist)
    assert package.decision == "VALIDATE_MULTIPLE_FINALISTS"
    assert package.production_deployment_authorized is False
    assert package.production_approval is False
    assert package.external_services_budget_usd == 0


def test_every_control_maps_provider_enki_evidence_and_rollback_responsibility_for_all_finalists() -> None:
    for contract in CONTRACTS.values():
        assert {mapping.finalist for mapping in contract.responsibility_mappings} == set(HostingFinalist)
        for mapping in contract.responsibility_mappings:
            assert mapping.provider_responsibilities
            assert mapping.enki_responsibilities
            assert mapping.evidence_owner in set(ResponsibilityParty)
            assert mapping.rollback_owner in set(ResponsibilityParty)
        assert contract.failure_criteria
        assert contract.stop_conditions
        assert contract.rollback_obligations
        assert contract.required_capabilities
        assert any(requirement.production_only for requirement in contract.evidence_requirements)


def test_test_substitute_and_test_evidence_never_satisfy_production_gate() -> None:
    for contract in CONTRACTS.values():
        result = evaluate_control_validation(
            contract,
            requested_context=ExecutionContext.PRODUCTION,
            evidence=make_evidence(contract, context=ExecutionContext.TEST),
            available_capabilities=contract.required_capabilities,
        )
        assert result.production_gate_satisfied is False
        assert result.disposition == ValidationDisposition.FAILED
        assert "TEST_EVIDENCE_CANNOT_SATISFY_PRODUCTION_REQUIREMENT" in result.reason_codes
        assert result.missing_requirement_ids


def test_test_readiness_run_is_explicitly_nonproduction_even_with_substitute_evidence() -> None:
    contract = CONTRACTS[ProductionControl.CLOUD_IAM]
    result = evaluate_control_validation(
        contract,
        requested_context=ExecutionContext.TEST,
        evidence=make_evidence(contract, context=ExecutionContext.TEST),
        available_capabilities=(),
    )

    assert result.disposition == ValidationDisposition.READY_FOR_PRODUCTION_VALIDATION
    assert result.production_gate_satisfied is False
    assert "PRODUCTION_CAPABILITY_NOT_AVAILABLE_IN_TEST" in result.reason_codes


def test_missing_production_capability_fails_closed_without_reopening_contract() -> None:
    contract = CONTRACTS[ProductionControl.NETWORK_SEGMENTATION]
    evidence = make_evidence(contract, context=ExecutionContext.PRODUCTION)
    result = evaluate_control_validation(
        contract,
        requested_context=ExecutionContext.PRODUCTION,
        evidence=evidence,
        available_capabilities=contract.required_capabilities[:-1],
    )

    assert result.disposition == ValidationDisposition.BLOCKED_MISSING_CAPABILITY
    assert result.production_gate_satisfied is False
    assert result.missing_capabilities == (contract.required_capabilities[-1],)
    assert "MISSING_REQUIRED_PRODUCTION_CAPABILITY" in result.reason_codes
    assert result.control == contract.control


def test_missing_production_evidence_fails_closed() -> None:
    contract = CONTRACTS[ProductionControl.PRODUCTION_SECRETS_MANAGEMENT]
    evidence = make_evidence(contract, context=ExecutionContext.PRODUCTION)[:-1]
    result = evaluate_control_validation(
        contract,
        requested_context=ExecutionContext.PRODUCTION,
        evidence=evidence,
        available_capabilities=contract.required_capabilities,
    )

    assert result.disposition == ValidationDisposition.FAILED
    assert result.production_gate_satisfied is False
    assert len(result.missing_requirement_ids) == 1
    assert "MISSING_REQUIRED_PRODUCTION_EVIDENCE" in result.reason_codes


def test_exact_production_evidence_and_all_capabilities_can_validate_contract_mechanics() -> None:
    for contract in CONTRACTS.values():
        result = evaluate_control_validation(
            contract,
            requested_context=ExecutionContext.PRODUCTION,
            evidence=make_evidence(contract, context=ExecutionContext.PRODUCTION),
            available_capabilities=contract.required_capabilities,
        )
        assert result.disposition == ValidationDisposition.VALIDATED
        assert result.production_gate_satisfied is True
        assert not result.missing_requirement_ids
        assert not result.missing_capabilities


def test_evidence_contract_mismatch_is_rejected_as_unsatisfied() -> None:
    contract = CONTRACTS[ProductionControl.CLOUD_IAM]
    evidence = make_evidence(contract, context=ExecutionContext.PRODUCTION)
    first = evidence[0]
    mismatched = first.model_copy(update={"evidence_class": EvidenceClass.HUMAN_APPROVAL})
    result = evaluate_control_validation(
        contract,
        requested_context=ExecutionContext.PRODUCTION,
        evidence=[mismatched, *evidence[1:]],
        available_capabilities=contract.required_capabilities,
    )

    assert result.production_gate_satisfied is False
    assert result.disposition == ValidationDisposition.FAILED
    assert "EVIDENCE_CONTRACT_MISMATCH" in result.reason_codes
    assert first.requirement_id in result.missing_requirement_ids


def test_evidence_owner_mismatch_is_rejected_as_unsatisfied() -> None:
    contract = CONTRACTS[ProductionControl.PER_TENANT_PRODUCTION_KEY_MANAGEMENT]
    evidence = make_evidence(contract, context=ExecutionContext.PRODUCTION)
    first = evidence[0]
    wrong_owner = first.model_copy(update={"owner": ResponsibilityParty.HUMAN_AUTHORITY})
    result = evaluate_control_validation(
        contract,
        requested_context=ExecutionContext.PRODUCTION,
        evidence=[wrong_owner, *evidence[1:]],
        available_capabilities=contract.required_capabilities,
    )

    assert result.production_gate_satisfied is False
    assert "EVIDENCE_CONTRACT_MISMATCH" in result.reason_codes


def test_independent_penetration_testing_requires_independent_assessment_owner() -> None:
    contract = CONTRACTS[ProductionControl.INDEPENDENT_PENETRATION_TESTING]
    independent_requirement = next(
        item
        for item in contract.evidence_requirements
        if item.evidence_class == EvidenceClass.INDEPENDENT_ASSESSMENT
    )
    assert independent_requirement.owner == ResponsibilityParty.INDEPENDENT_THIRD_PARTY

    evidence = make_evidence(contract, context=ExecutionContext.PRODUCTION)
    self_attested = [
        item.model_copy(update={"owner": ResponsibilityParty.ENKI})
        if item.requirement_id == independent_requirement.requirement_id
        else item
        for item in evidence
    ]
    result = evaluate_control_validation(
        contract,
        requested_context=ExecutionContext.PRODUCTION,
        evidence=self_attested,
        available_capabilities=contract.required_capabilities,
    )

    assert result.production_gate_satisfied is False
    assert independent_requirement.requirement_id in result.missing_requirement_ids


def test_validation_evidence_rejects_embedded_production_credentials() -> None:
    contract = CONTRACTS[ProductionControl.PRODUCTION_SECRETS_MANAGEMENT]
    requirement = contract.evidence_requirements[0]
    with pytest.raises(ValidationError, match="production credential material"):
        ValidationEvidence(
            evidence_id="E-SECRET-LEAK-DENIED",
            requirement_id=requirement.requirement_id,
            evidence_class=requirement.evidence_class,
            execution_context=ExecutionContext.PRODUCTION,
            owner=requirement.owner,
            artifact_sha256="sha256:" + "0" * 64,
            external_effect=False,
            production_credential_material=True,
        )


def test_readiness_package_cannot_authorize_production_or_spending() -> None:
    package = build_production_control_readiness_package()
    payload = package.model_dump(mode="python")
    payload["production_deployment_authorized"] = True
    payload["package_sha256"] = canonical_sha256(
        {key: value for key, value in payload.items() if key != "package_sha256"}
    )
    with pytest.raises(ValidationError, match="cannot authorize production"):
        ProductionControlReadinessPackage.model_validate(payload)

    payload = package.model_dump(mode="python")
    payload["external_services_budget_usd"] = 1
    payload["package_sha256"] = canonical_sha256(
        {key: value for key, value in payload.items() if key != "package_sha256"}
    )
    with pytest.raises(ValidationError, match="zero-dollar"):
        ProductionControlReadinessPackage.model_validate(payload)


def test_readiness_package_is_deterministic() -> None:
    first = build_production_control_readiness_package()
    second = build_production_control_readiness_package()
    assert second == first
    assert second.package_sha256 == first.package_sha256
    assert [item.contract_sha256 for item in second.contracts] == [
        item.contract_sha256 for item in first.contracts
    ]


EXPECTED_CONTROL_PATHS = {
    ProductionControl.CLOUD_IAM: "cloud-iam-contract-ready",
    ProductionControl.PRODUCTION_IDENTITY_FEDERATION: "production-identity-federation-contract-ready",
    ProductionControl.MANAGED_DATABASE_ROW_LEVEL_ISOLATION: "managed-database-isolation-contract-ready",
    ProductionControl.NETWORK_SEGMENTATION: "network-segmentation-contract-ready",
    ProductionControl.PER_TENANT_PRODUCTION_KEY_MANAGEMENT: "per-tenant-key-management-contract-ready",
    ProductionControl.PRODUCTION_SECRETS_MANAGEMENT: "production-secrets-management-contract-ready",
    ProductionControl.INDEPENDENT_PENETRATION_TESTING: "independent-penetration-testing-contract-ready",
}

SPRINT35_TESTED_PATHS = {
    "all-seven-production-controls-contracted",
    "all-finalists-responsibility-mapped",
    "provider-neutral-contracts-without-hosting-selection",
    "test-substitute-remains-nonproduction",
    "test-evidence-cannot-satisfy-production-gate",
    "missing-production-capability-blocks-closed",
    "missing-production-evidence-fails-closed",
    "production-validation-requires-exact-evidence-contract",
    "production-validation-requires-exact-evidence-owner",
    "production-validation-requires-all-capabilities",
    *EXPECTED_CONTROL_PATHS.values(),
    "independent-penetration-test-cannot-self-attest",
    "rollback-obligations-present",
    "stop-conditions-present",
    "production-credentials-rejected-from-evidence",
    "zero-dollar-boundary-preserved",
    "sprint-completion-does-not-authorize-production",
    "readiness-package-deterministic",
}


def test_every_declared_sprint35_path_has_automated_coverage() -> None:
    sprint35_production_control_readiness_path_manifest().assert_complete_coverage(
        SPRINT35_TESTED_PATHS
    )


def test_sprint35_paths_are_test_only_and_prohibit_production_shortcuts() -> None:
    manifest = sprint35_production_control_readiness_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-deployment" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "test-evidence-as-production-proof" in path.prohibited_effects
        assert "production-credential-persistence" in path.prohibited_effects
        assert "paid-external-service" in path.prohibited_effects
