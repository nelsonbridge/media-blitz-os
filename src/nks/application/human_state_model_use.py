"""Decomposed, governed model-use workflow for temporal human state.

This module is a compatibility bridge. It leaves ``PublishHumanStateFeedback``
intact while providing explicit interpretation, package, authority, receipt,
and persistence stages that can migrate to Enki-native contracts over time.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from nks.domain.human_state import (
    HumanStateObservation,
    HumanStateTransition,
    IngestionScope,
    ModelFeedbackPackage,
    ModelIngestionPolicy,
    TemporalStatus,
)
from nks.governance.approvals import ApprovalEvaluation, ExecutionContext


class HumanStateModelUseReader(Protocol):
    def list_observations(self, subject_id: str, domain: str) -> Sequence[HumanStateObservation]: ...

    def list_transitions(self, subject_id: str, domain: str) -> Sequence[HumanStateTransition]: ...

    def get_policy(self, policy_id: str) -> ModelIngestionPolicy | None: ...


class HumanStateModelUseWriter(Protocol):
    def save_model_use(
        self,
        package: ModelFeedbackPackage,
        receipt: "GovernedHumanStateModelUseReceipt",
    ) -> None: ...


class HumanStateInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_id: str
    domain: str
    current_observation: HumanStateObservation
    historical_observations: list[HumanStateObservation] = Field(default_factory=list)
    transitions: list[HumanStateTransition] = Field(default_factory=list)
    resolved_at: datetime


class HumanStateModelUseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    package: ModelFeedbackPackage
    payload_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class AuthorizedHumanStateModelUse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    envelope: HumanStateModelUseEnvelope
    policy_id: str
    approval_id: str
    execution_context: ExecutionContext
    transaction_id: str
    authorized_at: datetime
    exact_retry: bool = False


class GovernedHumanStateModelUseReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str
    subject_id: str
    domain: str
    observation_ids: list[str]
    transition_ids: list[str]
    policy_id: str
    approval_id: str
    execution_context: ExecutionContext
    transaction_id: str
    destination_scope: IngestionScope
    payload_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    authorized_at: datetime
    recorded_at: datetime
    publisher_version: str
    exact_retry: bool = False
    revocable: bool = True


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


class ResolveHumanStateInterpretation:
    """Resolve current and historical state without authorizing disclosure."""

    def __init__(self, repository: HumanStateModelUseReader) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        subject_id: str,
        domain: str,
        now: datetime | None = None,
    ) -> HumanStateInterpretation:
        resolved_at = now or datetime.now(timezone.utc)
        observations = list(self._repository.list_observations(subject_id, domain))
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
            raise ValueError("no current human-state observation exists")

        current = max(current_candidates, key=lambda item: (item.effective_from, item.observed_at))
        return HumanStateInterpretation(
            subject_id=subject_id,
            domain=domain,
            current_observation=current,
            historical_observations=[
                item for item in eligible if item.observation_id != current.observation_id
            ],
            transitions=list(self._repository.list_transitions(subject_id, domain)),
            resolved_at=resolved_at,
        )


class BuildHumanStateModelUsePackage:
    """Build a side-effect-free package from an already resolved interpretation.

    Transition inclusion is explicit. Legacy ``approved_for_model_feedback`` is
    not treated as authority and does not automatically select a transition.
    """

    def execute(
        self,
        interpretation: HumanStateInterpretation,
        *,
        scope: IngestionScope,
        included_transition_ids: Sequence[str] = (),
    ) -> HumanStateModelUseEnvelope:
        available = {item.transition_id: item for item in interpretation.transitions}
        unknown = set(included_transition_ids) - available.keys()
        if unknown:
            raise ValueError(f"unknown transition references: {sorted(unknown)}")
        selected = [available[item_id] for item_id in included_transition_ids]

        package = ModelFeedbackPackage(
            subject_id=interpretation.subject_id,
            domain=interpretation.domain,
            current_observation=interpretation.current_observation,
            historical_observations=interpretation.historical_observations,
            transitions=selected,
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
        return HumanStateModelUseEnvelope(
            package=package,
            payload_hash=_sha256_text(payload),
        )


class AuthorizeHumanStateModelUse:
    """Require both purpose policy and exact context-bound approval."""

    def __init__(self, repository: HumanStateModelUseReader) -> None:
        self._repository = repository

    def execute(
        self,
        interpretation: HumanStateInterpretation,
        envelope: HumanStateModelUseEnvelope,
        *,
        policy_id: str,
        approval: ApprovalEvaluation,
        now: datetime | None = None,
    ) -> AuthorizedHumanStateModelUse:
        authorized_at = now or datetime.now(timezone.utc)
        package = envelope.package
        policy = self._repository.get_policy(policy_id)
        if policy is None:
            raise ValueError("model-ingestion policy does not exist")
        if policy.subject_id != interpretation.subject_id or policy.domain != interpretation.domain:
            raise ValueError("policy does not authorize this subject and domain")
        if policy.observation_id != interpretation.current_observation.observation_id:
            raise ValueError("policy is stale for the current observation")
        if policy.observation_hash != interpretation.current_observation.content_hash:
            raise ValueError("policy hash does not match the current observation")
        if policy.revoked_at is not None and policy.revoked_at <= authorized_at:
            raise ValueError("model-ingestion policy is revoked")
        if policy.expires_at is not None and policy.expires_at <= authorized_at:
            raise ValueError("model-ingestion policy is expired")
        if (
            package.permitted_scope not in policy.approved_scopes
            or package.permitted_scope in policy.denied_scopes
        ):
            raise ValueError("model-ingestion scope is not approved by policy")

        if not approval.authorized:
            raise PermissionError("governed approval evaluation is not authorized")
        expected_action = f"model-use:{package.permitted_scope.value.lower()}"
        request = approval.request
        if request.action != expected_action:
            raise PermissionError("approval action does not match model-use scope")
        if request.subject_id != interpretation.subject_id:
            raise PermissionError("approval subject does not match interpretation subject")
        if request.content_sha256 != envelope.payload_hash:
            raise PermissionError("approval content hash does not match model-use package")

        return AuthorizedHumanStateModelUse(
            envelope=envelope,
            policy_id=policy_id,
            approval_id=approval.approval_id,
            execution_context=request.execution_context,
            transaction_id=request.transaction_id,
            authorized_at=authorized_at,
            exact_retry=approval.exact_retry,
        )


class RecordHumanStateModelUse:
    """Create and persist an immutable governed receipt after authorization."""

    def __init__(
        self,
        writer: HumanStateModelUseWriter,
        *,
        publisher_version: str = "0.1.0",
    ) -> None:
        self._writer = writer
        self._publisher_version = publisher_version

    def execute(
        self,
        authorized: AuthorizedHumanStateModelUse,
        *,
        recorded_at: datetime | None = None,
    ) -> GovernedHumanStateModelUseReceipt:
        timestamp = recorded_at or datetime.now(timezone.utc)
        package = authorized.envelope.package
        receipt_basis = "|".join(
            [
                authorized.transaction_id,
                authorized.envelope.payload_hash,
                authorized.approval_id,
                self._publisher_version,
            ]
        )
        receipt_id = "NKS-GMUR-" + hashlib.sha256(
            receipt_basis.encode("utf-8")
        ).hexdigest()[:12].upper()
        receipt = GovernedHumanStateModelUseReceipt(
            receipt_id=receipt_id,
            subject_id=package.subject_id,
            domain=package.domain,
            observation_ids=[
                package.current_observation.observation_id,
                *[item.observation_id for item in package.historical_observations],
            ],
            transition_ids=[item.transition_id for item in package.transitions],
            policy_id=authorized.policy_id,
            approval_id=authorized.approval_id,
            execution_context=authorized.execution_context,
            transaction_id=authorized.transaction_id,
            destination_scope=package.permitted_scope,
            payload_hash=authorized.envelope.payload_hash,
            authorized_at=authorized.authorized_at,
            recorded_at=timestamp,
            publisher_version=self._publisher_version,
            exact_retry=authorized.exact_retry,
        )
        self._writer.save_model_use(package, receipt)
        return receipt
