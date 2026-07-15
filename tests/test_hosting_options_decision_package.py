from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.hosting_options import (
    ArchitecturePattern,
    HostingDecisionPackage,
    HostingOption,
    REQUIRED_PRODUCTION_PREREQUISITES,
    build_hosting_decision_package,
)
from nks.application.sprint24_path_manifest import sprint24_hosting_path_manifest
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "releases" / "enki-hosting-options"


def test_decision_package_is_deterministic_and_zero_cost() -> None:
    first = build_hosting_decision_package()
    second = build_hosting_decision_package()

    assert first == second
    assert first.package_sha256 == second.package_sha256
    assert first.external_services_budget_usd == 0
    assert first.production_approval is False
    assert first.infrastructure_provisioned is False
    assert first.decision_state.value == "HUMAN_DECISION_REQUIRED"


def test_all_required_architecture_patterns_are_compared() -> None:
    package = build_hosting_decision_package()
    patterns = {item.pattern for item in package.options}

    assert patterns == {
        ArchitecturePattern.SINGLE_CLOUD,
        ArchitecturePattern.PROVIDER_SPLIT,
        ArchitecturePattern.CONTROL_DATA_SPLIT,
        ArchitecturePattern.PORTABILITY_HYBRID,
    }
    assert len(package.options) >= 5


def test_shortlist_retains_single_cloud_and_split_cloud_without_default_winner() -> None:
    package = build_hosting_decision_package()
    options = {item.option_id: item for item in package.options}
    shortlist_patterns = {options[item].pattern for item in package.shortlist_option_ids}

    assert "CF-NATIVE" in package.shortlist_option_ids
    assert "CF-NEON-R2" in package.shortlist_option_ids
    assert "GCP-NEON-R2" in package.shortlist_option_ids
    assert ArchitecturePattern.SINGLE_CLOUD in shortlist_patterns
    assert shortlist_patterns.intersection(
        {ArchitecturePattern.PROVIDER_SPLIT, ArchitecturePattern.CONTROL_DATA_SPLIT}
    )
    assert "Do not select a winner" in package.recommendation


def test_every_option_maps_all_production_prerequisites_as_unresolved() -> None:
    package = build_hosting_decision_package()

    for option in package.options:
        assert set(option.prerequisite_mapping) == REQUIRED_PRODUCTION_PREREQUISITES
        assert all("UNRESOLVED" in value for value in option.prerequisite_mapping.values())
        assert option.production_approved is False
        assert option.infrastructure_provisioned is False


def test_architecture_exploration_rejects_fake_production_validation() -> None:
    base = build_hosting_decision_package().options[0].model_dump(mode="python")
    mapping = dict(base["prerequisite_mapping"])
    mapping["cloud-iam"] = "VALIDATED"
    base["prerequisite_mapping"] = mapping

    with pytest.raises(ValidationError, match="cannot validate production controls"):
        HostingOption.model_validate(base)


def test_package_hash_tamper_fails_closed() -> None:
    package = build_hosting_decision_package()
    payload = package.model_dump(mode="python")
    payload["package_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(ValidationError, match="hosting decision package hash is invalid"):
        HostingDecisionPackage.model_validate(payload)


def test_official_provider_sources_are_recorded() -> None:
    package = build_hosting_decision_package()
    providers = {item.provider for item in package.evidence_sources}
    urls = {item.url for item in package.evidence_sources}

    assert {"Cloudflare", "Google Cloud", "AWS", "Neon", "Supabase", "Microsoft Azure"}.issubset(providers)
    assert all(url.startswith("https://") for url in urls)
    assert any("developers.cloudflare.com" in url for url in urls)
    assert any("cloud.google.com" in url for url in urls)
    assert any("aws.amazon.com" in url for url in urls)
    assert any("neon.com" in url for url in urls)


def test_machine_readable_contract_matches_package_boundary() -> None:
    contract = json.loads(
        (ROOT / "contracts" / "enki-hosting-options-v1.json").read_text(encoding="utf-8")
    )
    package = build_hosting_decision_package()

    assert contract["external_services_budget_usd"] == package.external_services_budget_usd
    assert contract["decision_state"] == package.decision_state.value
    assert contract["production_approval"] is False
    assert contract["infrastructure_provisioned"] is False
    assert set(contract["evaluated_options"]) == {item.option_id for item in package.options}
    assert contract["shortlist"] == package.shortlist_option_ids
    assert set(contract["required_production_prerequisites"]) == REQUIRED_PRODUCTION_PREREQUISITES


def test_required_review_documents_exist_and_preserve_decision_boundary() -> None:
    required = {
        "README.md",
        "options-matrix.md",
        "single-cloud-reference-architecture.md",
        "split-cloud-reference-architecture.md",
        "threat-trust-failure-analysis.md",
        "cost-model.md",
        "migration-rollback.md",
        "hosting-direction-decision-request.md",
    }
    for filename in required:
        path = PACKAGE / filename
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()

    overview = (PACKAGE / "README.md").read_text(encoding="utf-8")
    matrix = (PACKAGE / "options-matrix.md").read_text(encoding="utf-8")
    single = (PACKAGE / "single-cloud-reference-architecture.md").read_text(encoding="utf-8")
    split = (PACKAGE / "split-cloud-reference-architecture.md").read_text(encoding="utf-8")
    threat = (PACKAGE / "threat-trust-failure-analysis.md").read_text(encoding="utf-8")
    cost = (PACKAGE / "cost-model.md").read_text(encoding="utf-8")
    migration = (PACKAGE / "migration-rollback.md").read_text(encoding="utf-8")
    decision = (PACKAGE / "hosting-direction-decision-request.md").read_text(encoding="utf-8")

    assert "HUMAN_DECISION_REQUIRED" in overview
    assert "CF-NATIVE" in matrix and "GCP-NEON-R2" in matrix
    assert "Trust boundaries" in single
    assert "Trust boundaries" in split
    assert "Independent penetration testing" in threat
    assert "$0 external services" in cost
    assert "Rollback invariants" in migration
    assert "Decision state: **UNRESOLVED**" in decision
    assert "Silence is not approval" in decision
    assert "does not authorize production deployment" in decision


SPRINT24_TESTED_PATHS = {
    "official-pricing-sources-recorded",
    "single-cloud-options-compared",
    "provider-split-options-compared",
    "control-data-split-compared",
    "portability-hybrid-compared",
    "single-cloud-reference-architecture-present",
    "split-cloud-reference-architecture-present",
    "threat-trust-failure-analysis-present",
    "cost-model-zero-dollar-boundary",
    "production-prerequisite-mapping-explicit",
    "migration-rollback-explicit",
    "shortlist-present",
    "human-decision-unresolved",
    "production-provisioning-prohibited",
    "unsupported-production-validation-claim-denied",
    "default-hosting-selection-denied",
}


def test_every_declared_sprint24_path_has_automated_coverage() -> None:
    sprint24_hosting_path_manifest().assert_complete_coverage(SPRINT24_TESTED_PATHS)


def test_sprint24_paths_are_test_only_and_prohibit_production_or_spend() -> None:
    manifest = sprint24_hosting_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "infrastructure-provisioning" in path.prohibited_effects
        assert "unvalidated-control-promotion" in path.prohibited_effects
        assert "paid-external-service" in path.prohibited_effects
        assert "default-hosting-selection" in path.prohibited_effects
