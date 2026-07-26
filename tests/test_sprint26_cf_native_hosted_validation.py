from __future__ import annotations

import json
from pathlib import Path

from nks.application.hosting_validation import HostedExecutionState, evaluate_hosted_preflight
from nks.application.sprint26_path_manifest import sprint26_cf_native_path_manifest
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]


def _record(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_cf_native_preflight_fails_closed_without_external_capabilities() -> None:
    preflight = evaluate_hosted_preflight("CF-NATIVE", {})

    assert preflight.state == HostedExecutionState.BLOCKED_EXTERNAL_CAPABILITY
    assert preflight.missing_capabilities == (
        "provider_test_identity",
        "provider_test_credentials",
        "teardown_authority",
    )


def test_cf_native_records_remain_explicitly_blocked_with_reason() -> None:
    sprint = _record("records/sprints/NKS-SPR-026.json")
    work_item = _record("records/work-items/BL-026.json")

    assert sprint["status"] == "blocked"
    assert work_item["status"] == "blocked"
    assert "TEST credentials" in work_item["blocked_reason"]
    assert "teardown authority" in work_item["blocked_reason"]
    assert "teardown authority" in sprint["blocked_reason"]


SPRINT26_TESTED_PATHS = {
    "external-test-capabilities-required",
    "missing-capabilities-fail-closed",
    "blocked-reason-explicit-and-attributable",
    "production-credential-substitution-prohibited",
    "hosted-success-claim-without-capabilities-prohibited",
}


def test_every_declared_sprint26_path_has_automated_coverage() -> None:
    sprint26_cf_native_path_manifest().assert_complete_coverage(SPRINT26_TESTED_PATHS)


def test_sprint26_paths_are_test_only_and_prohibit_unsafe_effects() -> None:
    manifest = sprint26_cf_native_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "credential-reuse" in path.prohibited_effects
        assert "teardown-bypass" in path.prohibited_effects
        assert "simulated-hosted-success-without-capabilities" in path.prohibited_effects
