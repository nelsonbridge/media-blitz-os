import json
from pathlib import Path

from nks.application.deployment_decision_resolution import (
    ArchitectureLock,
    DeploymentDecisionResolution,
    HOSTED_RC2_SHA256,
)
from nks.application.hosted_release_candidate import HumanDecisionDisposition


ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = ROOT / "releases/enki-hosted-1.0-rc2/human-deployment-decision.json"
LOCK_PATH = ROOT / "releases/enki-hosted-1.0-rc2/architecture-lock.json"


def test_persisted_human_decision_is_exact_approved_candidate():
    decision = DeploymentDecisionResolution(
        **json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    )

    assert decision.candidate_sha256 == HOSTED_RC2_SHA256
    assert decision.disposition == HumanDecisionDisposition.APPROVE
    assert decision.conditions == ()
    assert decision.accepted_risks == ()
    assert decision.evidence_waivers == ()
    assert decision.architecture_lock_authorized is True
    assert decision.production_execution_authorized is False
    assert decision.external_services_budget_usd == 0


def test_persisted_architecture_lock_is_bound_to_exact_human_decision():
    decision = DeploymentDecisionResolution(
        **json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    )
    lock = ArchitectureLock(**json.loads(LOCK_PATH.read_text(encoding="utf-8")))

    assert lock.candidate_sha256 == decision.candidate_sha256
    assert lock.decision_resolution_sha256 == decision.resolution_sha256
    assert lock.architecture_id == "CF-NEON-R2"
    assert lock.compute_provider == "Cloudflare Workers"
    assert lock.canonical_store == "Neon Postgres"
    assert lock.object_store == "Cloudflare R2"
    assert lock.optional_services == ()
    assert lock.production_execution_authorized is False
    assert lock.external_services_budget_usd == 0
    assert any("hosted architecture validation remains BLOCKED" in item for item in lock.unresolved_prerequisites)
    assert any("production deployment readiness remains BLOCKED" in item for item in lock.unresolved_prerequisites)
