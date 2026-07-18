from pydantic import ValidationError

from nks.application.deployment_decision_resolution import (
    HOSTED_RC2_SHA256,
    REFERENCE_ARCHITECTURE_ID,
    ArchitectureLock,
    DeploymentDecisionResolution,
    DeploymentDecisionState,
    resolve_human_deployment_disposition,
)
from nks.application.hosted_release_candidate import HumanDecisionDisposition


SOURCE = "https://github.com/nelsonbridge/media-blitz-os/issues/123#issuecomment-5008644257"


def test_approve_locks_exact_candidate_architecture_without_production_authority():
    outcome = resolve_human_deployment_disposition(
        HumanDecisionDisposition.APPROVE,
        decision_authority_identity="nelsonbridge",
        source_reference=SOURCE,
    )

    assert outcome.decision.candidate_sha256 == HOSTED_RC2_SHA256
    assert outcome.decision.decision_state == DeploymentDecisionState.APPROVED
    assert outcome.decision.architecture_lock_authorized is True
    assert outcome.decision.production_execution_authorized is False
    assert outcome.decision.external_services_budget_usd == 0

    assert outcome.architecture_lock is not None
    assert outcome.architecture_lock.architecture_id == REFERENCE_ARCHITECTURE_ID
    assert outcome.architecture_lock.compute_provider == "Cloudflare Workers"
    assert outcome.architecture_lock.canonical_store == "Neon Postgres"
    assert outcome.architecture_lock.object_store == "Cloudflare R2"
    assert outcome.architecture_lock.optional_services == ()
    assert outcome.architecture_lock.production_execution_authorized is False
    assert outcome.architecture_lock.external_services_budget_usd == 0
    assert outcome.architecture_lock.unresolved_prerequisites


def test_approve_with_conditions_requires_and_preserves_explicit_conditions():
    outcome = resolve_human_deployment_disposition(
        HumanDecisionDisposition.APPROVE_WITH_CONDITIONS,
        decision_authority_identity="human-reviewer",
        source_reference=SOURCE,
        conditions=("Complete independent penetration testing before production execution.",),
    )

    assert outcome.decision.decision_state == DeploymentDecisionState.APPROVED_WITH_CONDITIONS
    assert outcome.decision.conditions == (
        "Complete independent penetration testing before production execution.",
    )
    assert outcome.architecture_lock is not None


def test_conditional_approval_without_conditions_fails_closed():
    try:
        resolve_human_deployment_disposition(
            HumanDecisionDisposition.APPROVE_WITH_CONDITIONS,
            decision_authority_identity="human-reviewer",
            source_reference=SOURCE,
        )
    except ValidationError as exc:
        assert "conditional approval requires explicit conditions" in str(exc)
    else:
        raise AssertionError("conditional approval without conditions must fail closed")


def test_defer_and_reject_produce_distinct_nonlocking_outcomes():
    deferred = resolve_human_deployment_disposition(
        HumanDecisionDisposition.DEFER,
        decision_authority_identity="human-reviewer",
        source_reference=SOURCE,
    )
    rejected = resolve_human_deployment_disposition(
        HumanDecisionDisposition.REJECT,
        decision_authority_identity="human-reviewer",
        source_reference=SOURCE,
    )

    assert deferred.decision.decision_state == DeploymentDecisionState.DEFERRED
    assert rejected.decision.decision_state == DeploymentDecisionState.REJECTED
    assert deferred.decision.resolution_sha256 != rejected.decision.resolution_sha256
    assert deferred.architecture_lock is None
    assert rejected.architecture_lock is None


def test_all_four_dispositions_are_governed_and_distinguishable():
    outcomes = {
        HumanDecisionDisposition.APPROVE: resolve_human_deployment_disposition(
            HumanDecisionDisposition.APPROVE,
            decision_authority_identity="human-reviewer",
            source_reference=SOURCE,
        ),
        HumanDecisionDisposition.APPROVE_WITH_CONDITIONS: resolve_human_deployment_disposition(
            HumanDecisionDisposition.APPROVE_WITH_CONDITIONS,
            decision_authority_identity="human-reviewer",
            source_reference=SOURCE,
            conditions=("condition",),
        ),
        HumanDecisionDisposition.DEFER: resolve_human_deployment_disposition(
            HumanDecisionDisposition.DEFER,
            decision_authority_identity="human-reviewer",
            source_reference=SOURCE,
        ),
        HumanDecisionDisposition.REJECT: resolve_human_deployment_disposition(
            HumanDecisionDisposition.REJECT,
            decision_authority_identity="human-reviewer",
            source_reference=SOURCE,
        ),
    }

    states = {outcome.decision.decision_state for outcome in outcomes.values()}
    hashes = {outcome.decision.resolution_sha256 for outcome in outcomes.values()}
    assert len(states) == 4
    assert len(hashes) == 4


def test_resolution_hash_is_deterministic_for_exact_human_decision():
    first = resolve_human_deployment_disposition(
        HumanDecisionDisposition.APPROVE,
        decision_authority_identity="nelsonbridge",
        source_reference=SOURCE,
    )
    second = resolve_human_deployment_disposition(
        HumanDecisionDisposition.APPROVE,
        decision_authority_identity="nelsonbridge",
        source_reference=SOURCE,
    )

    assert first.decision.resolution_sha256 == second.decision.resolution_sha256
    assert first.architecture_lock is not None
    assert second.architecture_lock is not None
    assert first.architecture_lock.lock_sha256 == second.architecture_lock.lock_sha256


def test_tampered_resolution_hash_is_rejected():
    outcome = resolve_human_deployment_disposition(
        HumanDecisionDisposition.APPROVE,
        decision_authority_identity="nelsonbridge",
        source_reference=SOURCE,
    )
    payload = outcome.decision.model_dump(mode="python")
    payload["resolution_sha256"] = "sha256:" + "0" * 64

    try:
        DeploymentDecisionResolution(**payload)
    except ValidationError as exc:
        assert "deployment decision resolution hash is invalid" in str(exc)
    else:
        raise AssertionError("tampered decision hash must fail closed")


def test_tampered_architecture_lock_hash_is_rejected():
    outcome = resolve_human_deployment_disposition(
        HumanDecisionDisposition.APPROVE,
        decision_authority_identity="nelsonbridge",
        source_reference=SOURCE,
    )
    assert outcome.architecture_lock is not None
    payload = outcome.architecture_lock.model_dump(mode="python")
    payload["lock_sha256"] = "sha256:" + "0" * 64

    try:
        ArchitectureLock(**payload)
    except ValidationError as exc:
        assert "architecture lock hash is invalid" in str(exc)
    else:
        raise AssertionError("tampered architecture lock hash must fail closed")
