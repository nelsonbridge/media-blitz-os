from __future__ import annotations

from pydantic import ValidationError

from nks.application.hosted_release_candidate import HumanDecisionDisposition
from nks.application.operational_release import (
    EnkiOperationalReleasePackage,
    LaunchDecisionState,
    OperationalEvidenceDomain,
    OperationalEvidenceStatus,
    OperationalReadinessStatus,
    ProductionControlClassification,
    build_human_launch_decision_request,
    build_operational_release_package,
)
from nks.application.production_control_readiness import ProductionControl


def test_operational_release_binds_all_twelve_evidence_domains() -> None:
    release = build_operational_release_package()

    assert {item.domain for item in release.evidence} == set(OperationalEvidenceDomain)
    assert release.external_services_budget_usd == 0
    assert release.production_launch_authorized is False
    assert release.launch_decision_state == LaunchDecisionState.PENDING_HUMAN_DECISION


def test_operational_release_keeps_test_and_production_readiness_separate() -> None:
    release = build_operational_release_package()

    assert release.readiness.software_ready is True
    assert release.readiness.hosted_platform_status == OperationalReadinessStatus.CONDITIONAL
    assert release.readiness.production_controls_status == OperationalReadinessStatus.NOT_READY
    assert release.readiness.operational_status == OperationalReadinessStatus.CONDITIONAL
    assert release.readiness.production_launch_authorized is False
    assert "production-control-evidence-missing" in release.readiness.blockers
    assert "independent-penetration-testing-required" in release.readiness.blockers


def test_every_production_control_is_explicit_and_external_required() -> None:
    release = build_operational_release_package()

    assert {item.control for item in release.production_controls} == set(ProductionControl)
    assert all(
        item.classification == ProductionControlClassification.EXTERNALLY_REQUIRED
        for item in release.production_controls
    )
    assert all(not item.qualifying_production_evidence_present for item in release.production_controls)

    pen_test = next(
        item
        for item in release.production_controls
        if item.control == ProductionControl.INDEPENDENT_PENETRATION_TESTING
    )
    assert pen_test.independent_assessment_required is True


def test_release_does_not_upgrade_conditional_or_test_evidence_to_production_validation() -> None:
    release = build_operational_release_package()

    security = next(item for item in release.evidence if item.domain == OperationalEvidenceDomain.SECURITY)
    cost = next(item for item in release.evidence if item.domain == OperationalEvidenceDomain.COST)
    software = next(item for item in release.evidence if item.domain == OperationalEvidenceDomain.SOFTWARE)

    assert security.status == OperationalEvidenceStatus.CONDITIONAL
    assert cost.status == OperationalEvidenceStatus.CONDITIONAL
    assert software.status == OperationalEvidenceStatus.VALIDATED_TEST


def test_operational_release_hash_is_deterministic() -> None:
    first = build_operational_release_package()
    second = build_operational_release_package()

    assert first == second
    assert first.release_sha256 == second.release_sha256


def test_human_launch_request_supports_all_dispositions_without_selecting_one() -> None:
    release = build_operational_release_package()
    request = build_human_launch_decision_request(release)

    assert request.release_sha256 == release.release_sha256
    assert set(request.supported_dispositions) == set(HumanDecisionDisposition)
    assert request.decision_state == LaunchDecisionState.PENDING_HUMAN_DECISION
    assert request.decision_authority == "HUMAN"
    assert request.selected_disposition is None


def test_release_model_rejects_missing_evidence_domain() -> None:
    release = build_operational_release_package()
    payload = release.model_dump(mode="python")
    payload["evidence"] = tuple(
        item
        for item in payload["evidence"]
        if item["domain"] != OperationalEvidenceDomain.COST
    )

    try:
        EnkiOperationalReleasePackage.model_validate(payload)
    except (ValidationError, ValueError):
        pass
    else:
        raise AssertionError("release accepted a missing evidence domain")


def test_release_model_rejects_false_ready_production_controls() -> None:
    release = build_operational_release_package()
    payload = release.model_dump(mode="python")
    readiness = release.readiness.model_copy(
        update={"production_controls_status": OperationalReadinessStatus.READY}
    )
    payload["readiness"] = readiness

    try:
        EnkiOperationalReleasePackage.model_validate(payload)
    except (ValidationError, ValueError):
        pass
    else:
        raise AssertionError("release accepted READY controls without validated production evidence")
