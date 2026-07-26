from __future__ import annotations

import json
from pathlib import Path

from nks.application.hosting_validation import (
    HostedExecutionState,
    build_hosting_validation_program,
    evaluate_hosted_preflight,
)
from nks.application.sprint27_path_manifest import sprint27_cf_neon_r2_path_manifest
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]


def test_cf_neon_r2_plan_uses_expected_provider_split() -> None:
    program = build_hosting_validation_program()
    plan = next(item for item in program.plans if item.option_id == "CF-NEON-R2")

    assert plan.providers == ("Cloudflare", "Neon")
    assert program.execution_context == "TEST"
    assert program.production_approval is False


def test_cf_neon_r2_preflight_blocks_without_test_capabilities() -> None:
    preflight = evaluate_hosted_preflight("CF-NEON-R2", {})

    assert preflight.state == HostedExecutionState.BLOCKED_EXTERNAL_CAPABILITY
    assert preflight.missing_capabilities == (
        "provider_test_identity",
        "provider_test_credentials",
        "teardown_authority",
    )


def test_cf_neon_r2_preflight_is_ready_with_full_test_capabilities() -> None:
    preflight = evaluate_hosted_preflight(
        "CF-NEON-R2",
        {
            "provider_test_identity": True,
            "provider_test_credentials": True,
            "teardown_authority": True,
        },
    )

    assert preflight.state == HostedExecutionState.READY
    assert preflight.missing_capabilities == ()


def test_hosting_contract_keeps_cf_neon_r2_test_only_boundary() -> None:
    contract = json.loads(
        (ROOT / "contracts" / "enki-hosting-validation-v1.json").read_text(encoding="utf-8")
    )

    assert contract["execution_context"] == "TEST"
    assert contract["production_approval"] is False
    assert "CF-NEON-R2" in contract["finalists"]


SPRINT27_TESTED_PATHS = {
    "test-identities-and-credentials-required",
    "ordered-validation-phases-preserved",
    "governed-synthetic-import-boundary-preserved",
    "cross-provider-failure-does-not-duplicate-canonical-effects",
    "cross-provider-latency-egress-quota-evidence-captured",
    "credential-revocation-and-teardown-required",
    "post-teardown-state-reconstructable-from-governed-exports",
    "results-remain-test-evidence-only",
    "missing-hosted-capability-blocks-execution",
}


def test_every_declared_sprint27_path_has_automated_coverage() -> None:
    sprint27_cf_neon_r2_path_manifest().assert_complete_coverage(SPRINT27_TESTED_PATHS)


def test_sprint27_paths_are_test_only_and_prohibit_unsafe_effects() -> None:
    manifest = sprint27_cf_neon_r2_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "credential-reuse" in path.prohibited_effects
        assert "teardown-bypass" in path.prohibited_effects
        assert "canonical-authority-escalation" in path.prohibited_effects
