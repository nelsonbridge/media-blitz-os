from __future__ import annotations

from nks.application.hosting_validation import (
    FINALISTS,
    REQUIRED_BOUNDARIES,
    REQUIRED_PRODUCTION_PREREQUISITES,
    HostedExecutionState,
    ValidationPhase,
    build_hosting_validation_program,
    evaluate_hosted_preflight,
)
from nks.application.sprint25_path_manifest import (
    sprint25_hosted_validation_foundation_path_manifest,
)
from nks.governance.approvals import ExecutionContext


def test_sprint25_program_is_test_only_and_multi_finalist() -> None:
    program = build_hosting_validation_program()

    assert program.execution_context == "TEST"
    assert program.decision == "VALIDATE_MULTIPLE_FINALISTS"
    assert program.production_approval is False
    assert tuple(plan.option_id for plan in program.plans) == FINALISTS


def test_sprint25_all_finalists_use_full_contract() -> None:
    program = build_hosting_validation_program()

    for plan in program.plans:
        assert plan.phases == tuple(ValidationPhase)
        assert plan.required_boundaries == REQUIRED_BOUNDARIES
        assert plan.unresolved_production_prerequisites == REQUIRED_PRODUCTION_PREREQUISITES


def test_sprint25_capability_gate_fails_closed() -> None:
    denied = evaluate_hosted_preflight("CF-NATIVE", {})
    ready = evaluate_hosted_preflight(
        "CF-NATIVE",
        {
            "provider_test_identity": True,
            "provider_test_credentials": True,
            "teardown_authority": True,
        },
    )

    assert denied.state == HostedExecutionState.BLOCKED_EXTERNAL_CAPABILITY
    assert ready.state == HostedExecutionState.READY


SPRINT25_TESTED_PATHS = {
    "multi-finalist-direction-explicit",
    "all-finalists-covered-in-canonical-order",
    "ordered-validation-phases-complete",
    "boundary-dimensions-complete",
    "production-prerequisites-explicit-and-unresolved",
    "capability-gate-fails-closed-when-missing",
    "test-only-authority-enforced",
    "nonfinalist-validation-rejected",
    "incomplete-phase-contract-rejected",
}


def test_every_declared_sprint25_path_has_automated_coverage() -> None:
    sprint25_hosted_validation_foundation_path_manifest().assert_complete_coverage(
        SPRINT25_TESTED_PATHS
    )


def test_sprint25_paths_are_test_only_and_prohibit_unsafe_effects() -> None:
    manifest = sprint25_hosted_validation_foundation_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "production-credentials" in path.prohibited_effects
        assert "production-data" in path.prohibited_effects
        assert "incomplete-finalist-contract" in path.prohibited_effects
