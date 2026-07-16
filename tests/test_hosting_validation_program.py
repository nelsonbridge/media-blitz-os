from __future__ import annotations

import pytest
from pydantic import ValidationError

from nks.application.hosting_validation import (
    FINALISTS,
    REQUIRED_BOUNDARIES,
    REQUIRED_PRODUCTION_PREREQUISITES,
    FinalistValidationPlan,
    HostedExecutionState,
    HostedValidationProgram,
    ValidationPhase,
    build_hosting_validation_program,
    evaluate_hosted_preflight,
)


def test_multi_finalist_program_is_test_only_and_complete() -> None:
    program = build_hosting_validation_program()

    assert program.decision == "VALIDATE_MULTIPLE_FINALISTS"
    assert program.execution_context == "TEST"
    assert program.external_services_budget_usd == 0
    assert program.production_approval is False
    assert program.production_data_allowed is False
    assert program.production_credentials_allowed is False
    assert tuple(plan.option_id for plan in program.plans) == FINALISTS

    for plan in program.plans:
        assert plan.phases == tuple(ValidationPhase)
        assert plan.required_boundaries == REQUIRED_BOUNDARIES
        assert plan.unresolved_production_prerequisites == REQUIRED_PRODUCTION_PREREQUISITES
        assert plan.production_approval is False


def test_program_rejects_noncanonical_finalist_set() -> None:
    valid = build_hosting_validation_program()
    duplicate = valid.plans[0]

    with pytest.raises(ValidationError, match="each finalist exactly once"):
        HostedValidationProgram(plans=(duplicate, duplicate, duplicate))


def test_plan_rejects_incomplete_validation_phase_set() -> None:
    with pytest.raises(ValidationError, match="complete ordered validation phase set"):
        FinalistValidationPlan(
            option_id="CF-NATIVE",
            providers=("Cloudflare",),
            phases=(ValidationPhase.PREFLIGHT,),
            required_boundaries=REQUIRED_BOUNDARIES,
            unresolved_production_prerequisites=REQUIRED_PRODUCTION_PREREQUISITES,
        )


def test_plan_rejects_missing_boundary_dimension() -> None:
    with pytest.raises(ValidationError, match="complete boundary set"):
        FinalistValidationPlan(
            option_id="CF-NATIVE",
            providers=("Cloudflare",),
            phases=tuple(ValidationPhase),
            required_boundaries=REQUIRED_BOUNDARIES[:-1],
            unresolved_production_prerequisites=REQUIRED_PRODUCTION_PREREQUISITES,
        )


def test_plan_keeps_all_production_prerequisites_unresolved() -> None:
    with pytest.raises(ValidationError, match="remain explicit and unresolved"):
        FinalistValidationPlan(
            option_id="CF-NATIVE",
            providers=("Cloudflare",),
            phases=tuple(ValidationPhase),
            required_boundaries=REQUIRED_BOUNDARIES,
            unresolved_production_prerequisites=REQUIRED_PRODUCTION_PREREQUISITES[:-1],
        )


def test_hosted_preflight_fails_closed_without_external_test_capabilities() -> None:
    result = evaluate_hosted_preflight("CF-NEON-R2", {})

    assert result.state == HostedExecutionState.BLOCKED_EXTERNAL_CAPABILITY
    assert result.missing_capabilities == (
        "provider_test_identity",
        "provider_test_credentials",
        "teardown_authority",
    )
    assert result.execution_context == "TEST"
    assert result.production_approval is False


def test_hosted_preflight_is_ready_only_when_all_test_capabilities_exist() -> None:
    result = evaluate_hosted_preflight(
        "GCP-NEON-R2",
        {
            "provider_test_identity": True,
            "provider_test_credentials": True,
            "teardown_authority": True,
        },
    )

    assert result.state == HostedExecutionState.READY
    assert result.missing_capabilities == ()
    assert result.production_approval is False


def test_hosted_preflight_rejects_nonfinalist() -> None:
    with pytest.raises(ValueError, match="unknown hosting finalist"):
        evaluate_hosted_preflight("AWS-NATIVE", {})
