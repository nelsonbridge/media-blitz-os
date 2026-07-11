from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from nks.adapters.human_state import JsonHumanStateRepository
from nks.application.human_state import (
    ApproveModelIngestion,
    PublishHumanStateFeedback,
    RecordHumanObservation,
    RecordHumanTransition,
    sha256_text,
)
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    HumanStateTransition,
    IngestionScope,
    ModelIngestionPolicy,
    TemporalStatus,
    TransitionOrigin,
    TransitionType,
)

NOW = datetime(2026, 7, 11, 12, 0, tzinfo=timezone.utc)


def observation(
    observation_id: str,
    content: str,
    status: TemporalStatus,
    effective_from: date,
    *,
    supersedes: str | None = None,
) -> HumanStateObservation:
    return HumanStateObservation(
        observation_id=observation_id,
        subject_id="NKS-PER-000001",
        content=content,
        content_hash=sha256_text(content),
        domain="career.relocation",
        state_type="preference",
        provenance="REAL",
        source_id="NKS-SRC-000001",
        observed_at=NOW,
        effective_from=effective_from,
        context=["career planning"],
        expression_strength=ExpressionStrength.EXPLICIT,
        confidence="HIGH",
        temporal_status=status,
        supersedes_observation_id=supersedes,
    )


def test_human_evolution_is_preserved_and_published_with_independent_scope(tmp_path: Path):
    repository = JsonHumanStateRepository(tmp_path)
    record = RecordHumanObservation(repository)

    historical = observation(
        "NKS-HSO-000001",
        "I do not want to relocate.",
        TemporalStatus.HISTORICAL,
        date(2026, 1, 1),
    )
    current = observation(
        "NKS-HSO-000002",
        "I may relocate for an exceptional role.",
        TemporalStatus.CONDITIONAL,
        date(2026, 7, 11),
    )
    record.execute(historical)
    record.execute(current)

    transition = HumanStateTransition(
        transition_id="NKS-HST-000001",
        subject_id=current.subject_id,
        domain=current.domain,
        from_observation_id=historical.observation_id,
        to_observation_id=current.observation_id,
        transition_type=TransitionType.CONDITIONAL_REVISION,
        origin=TransitionOrigin.SUBJECT_DECLARED,
        detected_at=NOW,
        stated_reason="An exceptional-role condition was introduced.",
        durability="UNKNOWN",
        reversibility="POSSIBLE",
        confidence="HIGH",
        approved_for_model_feedback=True,
        approved_by="subject",
    )
    RecordHumanTransition(repository).execute(transition)

    policy = ModelIngestionPolicy(
        policy_id="NKS-MIP-000001",
        subject_id=current.subject_id,
        domain=current.domain,
        observation_id=current.observation_id,
        observation_hash=current.content_hash,
        approved_scopes={IngestionScope.PERSONALIZATION, IngestionScope.RETRIEVAL},
        denied_scopes={IngestionScope.FINE_TUNING, IngestionScope.EXTERNAL_MODEL_TRANSMISSION},
        approved_by="subject",
        approved_at=NOW,
    )
    ApproveModelIngestion(repository).execute(policy)

    receipt = PublishHumanStateFeedback(repository).execute(
        subject_id=current.subject_id,
        domain=current.domain,
        policy_id=policy.policy_id,
        scope=IngestionScope.PERSONALIZATION,
        now=NOW,
    )

    payload_path = tmp_path / "generated" / "model-feedback" / receipt.receipt_id / "payload.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["current_observation"]["observation_id"] == current.observation_id
    assert payload["historical_observations"][0]["observation_id"] == historical.observation_id
    assert payload["transitions"][0]["transition_type"] == "CONDITIONAL_REVISION"
    assert payload["behavioral_instructions"]["preserve_history"] is True
    assert payload["behavioral_instructions"]["do_not_generalize_beyond_context"] is True


def test_stale_policy_cannot_publish_changed_human_state(tmp_path: Path):
    repository = JsonHumanStateRepository(tmp_path)
    current = observation(
        "NKS-HSO-000001",
        "I do not want to relocate.",
        TemporalStatus.CURRENT,
        date(2026, 1, 1),
    )
    RecordHumanObservation(repository).execute(current)
    policy = ModelIngestionPolicy(
        policy_id="NKS-MIP-000001",
        subject_id=current.subject_id,
        domain=current.domain,
        observation_id=current.observation_id,
        observation_hash=current.content_hash,
        approved_scopes={IngestionScope.PERSONALIZATION},
        approved_by="subject",
        approved_at=NOW,
    )
    ApproveModelIngestion(repository).execute(policy)

    newer = observation(
        "NKS-HSO-000002",
        "I may relocate for an exceptional role.",
        TemporalStatus.CONDITIONAL,
        date(2026, 7, 11),
    )
    RecordHumanObservation(repository).execute(newer)

    with pytest.raises(ValueError, match="policy is stale"):
        PublishHumanStateFeedback(repository).execute(
            subject_id=current.subject_id,
            domain=current.domain,
            policy_id=policy.policy_id,
            scope=IngestionScope.PERSONALIZATION,
            now=NOW,
        )


def test_revoked_expired_and_denied_scopes_fail_closed(tmp_path: Path):
    repository = JsonHumanStateRepository(tmp_path)
    current = observation(
        "NKS-HSO-000001",
        "Current state.",
        TemporalStatus.CURRENT,
        date(2026, 7, 11),
    )
    RecordHumanObservation(repository).execute(current)

    expired = ModelIngestionPolicy(
        policy_id="NKS-MIP-EXPIRED",
        subject_id=current.subject_id,
        domain=current.domain,
        observation_id=current.observation_id,
        observation_hash=current.content_hash,
        approved_scopes={IngestionScope.PERSONALIZATION},
        approved_by="subject",
        approved_at=NOW - timedelta(days=2),
        expires_at=NOW - timedelta(days=1),
    )
    ApproveModelIngestion(repository).execute(expired)
    with pytest.raises(ValueError, match="expired"):
        PublishHumanStateFeedback(repository).execute(
            subject_id=current.subject_id,
            domain=current.domain,
            policy_id=expired.policy_id,
            scope=IngestionScope.PERSONALIZATION,
            now=NOW,
        )

    denied = ModelIngestionPolicy(
        policy_id="NKS-MIP-DENIED",
        subject_id=current.subject_id,
        domain=current.domain,
        observation_id=current.observation_id,
        observation_hash=current.content_hash,
        approved_scopes={IngestionScope.RETRIEVAL},
        denied_scopes={IngestionScope.FINE_TUNING},
        approved_by="subject",
        approved_at=NOW,
    )
    ApproveModelIngestion(repository).execute(denied)
    with pytest.raises(ValueError, match="not approved"):
        PublishHumanStateFeedback(repository).execute(
            subject_id=current.subject_id,
            domain=current.domain,
            policy_id=denied.policy_id,
            scope=IngestionScope.FINE_TUNING,
            now=NOW,
        )


def test_content_hash_and_inferred_transition_requirements_fail_closed(tmp_path: Path):
    repository = JsonHumanStateRepository(tmp_path)
    invalid = observation(
        "NKS-HSO-000001",
        "Content",
        TemporalStatus.CURRENT,
        date(2026, 7, 11),
    ).model_copy(update={"content_hash": "sha256:" + "0" * 64})
    with pytest.raises(ValueError, match="content_hash"):
        RecordHumanObservation(repository).execute(invalid)

    with pytest.raises(ValueError, match="inferred_causes"):
        HumanStateTransition(
            transition_id="NKS-HST-000001",
            subject_id="NKS-PER-000001",
            domain="career.relocation",
            from_observation_id="NKS-HSO-000001",
            to_observation_id="NKS-HSO-000002",
            transition_type=TransitionType.REFINEMENT,
            origin=TransitionOrigin.GOVERNED_INFERENCE,
            detected_at=NOW,
            durability="UNKNOWN",
            reversibility="POSSIBLE",
            confidence="LOW",
        )
