"""Application services for temporal human evolution and model feedback."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from nks.adapters.human_state import JsonHumanStateRepository
from nks.domain.human_state import (
    HumanStateObservation,
    HumanStateTransition,
    IngestionScope,
    ModelFeedbackPackage,
    ModelFeedbackReceipt,
    ModelIngestionPolicy,
    TemporalStatus,
)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


class RecordHumanObservation:
    def __init__(self, repository: JsonHumanStateRepository) -> None:
        self._repository = repository

    def execute(self, observation: HumanStateObservation) -> HumanStateObservation:
        if observation.content_hash != sha256_text(observation.content):
            raise ValueError("observation content_hash does not match content")
        return self._repository.save_observation(observation)


class RecordHumanTransition:
    def __init__(self, repository: JsonHumanStateRepository) -> None:
        self._repository = repository

    def execute(self, transition: HumanStateTransition) -> HumanStateTransition:
        before = self._repository.get_observation(transition.from_observation_id)
        after = self._repository.get_observation(transition.to_observation_id)
        if before is None or after is None:
            raise ValueError("transition observations must exist")
        if before.subject_id != transition.subject_id or after.subject_id != transition.subject_id:
            raise ValueError("transition subject does not match observation subject")
        if before.domain != transition.domain or after.domain != transition.domain:
            raise ValueError("transition domain does not match observation domain")
        if after.effective_from < before.effective_from:
            raise ValueError("transition destination cannot predate source observation")
        return self._repository.save_transition(transition)


class ApproveModelIngestion:
    def __init__(self, repository: JsonHumanStateRepository) -> None:
        self._repository = repository

    def execute(self, policy: ModelIngestionPolicy) -> ModelIngestionPolicy:
        observation = self._repository.get_observation(policy.observation_id)
        if observation is None:
            raise ValueError("policy observation does not exist")
        if observation.subject_id != policy.subject_id or observation.domain != policy.domain:
            raise ValueError("policy scope does not match observation")
        if observation.content_hash != policy.observation_hash:
            raise ValueError("policy hash does not match observation")
        return self._repository.save_policy(policy)


class PublishHumanStateFeedback:
    def __init__(self, repository: JsonHumanStateRepository, publisher_version: str = "0.1.0") -> None:
        self._repository = repository
        self._publisher_version = publisher_version

    def execute(
        self,
        *,
        subject_id: str,
        domain: str,
        policy_id: str,
        scope: IngestionScope,
        now: datetime | None = None,
    ) -> ModelFeedbackReceipt:
        now = now or datetime.now(timezone.utc)
        policy = self._repository.get_policy(policy_id)
        if policy is None:
            raise ValueError("model-ingestion policy does not exist")
        if policy.subject_id != subject_id or policy.domain != domain:
            raise ValueError("policy does not authorize this subject and domain")
        if policy.revoked_at is not None:
            raise ValueError("model-ingestion policy is revoked")
        if policy.expires_at is not None and policy.expires_at <= now:
            raise ValueError("model-ingestion policy is expired")
        if scope not in policy.approved_scopes or scope in policy.denied_scopes:
            raise ValueError("model-ingestion scope is not approved")

        observations = self._repository.list_observations(subject_id, domain)
        eligible = [
            item
            for item in observations
            if item.temporal_status
            not in {TemporalStatus.RETRACTED, TemporalStatus.EXPIRED, TemporalStatus.DISPUTED}
        ]
        if not eligible:
            raise ValueError("no eligible human-state observations exist")

        current_candidates = [
            item
            for item in eligible
            if item.temporal_status
            in {TemporalStatus.CURRENT, TemporalStatus.CONDITIONAL, TemporalStatus.CONTEXT_SPECIFIC}
        ]
        if not current_candidates:
            raise ValueError("no current approved human-state observation exists")
        current = max(current_candidates, key=lambda item: (item.effective_from, item.observed_at))
        if current.observation_id != policy.observation_id or current.content_hash != policy.observation_hash:
            raise ValueError("policy is stale for the current observation")

        transitions = [
            item
            for item in self._repository.list_transitions(subject_id, domain)
            if item.approved_for_model_feedback
        ]
        package = ModelFeedbackPackage(
            subject_id=subject_id,
            domain=domain,
            current_observation=current,
            historical_observations=[item for item in eligible if item.observation_id != current.observation_id],
            transitions=transitions,
            permitted_scope=scope,
            behavioral_instructions={
                "use_current_state": True,
                "preserve_history": True,
                "do_not_generalize_beyond_context": True,
                "preserve_uncertainty": True,
                "do_not_treat_inference_as_self_declaration": True,
            },
        )
        payload = package.model_dump_json(exclude_none=False)
        receipt = ModelFeedbackReceipt(
            receipt_id=f"NKS-MFR-{uuid4().hex[:12].upper()}",
            subject_id=subject_id,
            domain=domain,
            observation_ids=[item.observation_id for item in observations],
            transition_ids=[item.transition_id for item in transitions],
            policy_id=policy_id,
            destination_scope=scope,
            payload_hash=sha256_text(payload),
            published_at=now,
            publisher_version=self._publisher_version,
        )
        self._repository.save_feedback(package, receipt)
        self._repository.save_feedback_manifest(receipt)
        return receipt
