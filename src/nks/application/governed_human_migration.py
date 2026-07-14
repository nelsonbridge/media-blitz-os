"""Governed migration from legacy temporal human state into generic Enki state."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.adapters.human_state_enki import (
    project_human_observation,
    project_human_transition,
)
from nks.application.approval_lifecycle import ApprovalGrantRepository
from nks.application.governed_state_write import (
    EnkiStateWriter,
    ExecuteGovernedStateWrite,
    GovernedStateWritePlan,
    StateWriteFailureHook,
)
from nks.application.governed_transactions import (
    FailureHook,
    GovernedTransactionJournal,
    GovernedTransactionReceipt,
    GovernedTransactionReceiptRepository,
)
from nks.domain.human_state import HumanStateObservation, HumanStateTransition
from nks.enki.contracts import ExpressionOrigin, SubjectRef
from nks.governance.approvals import ExecutionContext


class ConsentState(StrEnum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"


class PrivacyClassification(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class HumanMigrationProtectionPolicy(BaseModel):
    """Human-specific consent, purpose, privacy, validity, and revocation policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    consent_state: ConsentState
    allowed_purposes: set[str] = Field(min_length=1)
    privacy_classification: PrivacyClassification
    approved_by: str = Field(min_length=1)
    approved_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    correction_allowed: bool = True
    retraction_allowed: bool = True
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_window(self) -> "HumanMigrationProtectionPolicy":
        if self.expires_at is not None and self.expires_at <= self.approved_at:
            raise ValueError("expires_at must follow approved_at")
        if self.revoked_at is not None and self.revoked_at < self.approved_at:
            raise ValueError("revoked_at cannot precede approved_at")
        return self

    def assert_authorized(self, *, purpose: str, at: datetime) -> None:
        reasons: list[str] = []
        if self.consent_state != ConsentState.GRANTED:
            reasons.append(f"consent state is {self.consent_state.value}")
        if purpose not in self.allowed_purposes:
            reasons.append("purpose is not allowed")
        if self.expires_at is not None and self.expires_at <= at:
            reasons.append("policy is expired")
        if self.revoked_at is not None and self.revoked_at <= at:
            reasons.append("policy is revoked")
        if reasons:
            raise PermissionError("; ".join(reasons))


class HumanMigrationSource(BaseModel):
    """Exact legacy source records and explicit origin decisions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observations: list[HumanStateObservation] = Field(min_length=1)
    transitions: list[HumanStateTransition] = Field(default_factory=list)
    expression_origins: dict[str, ExpressionOrigin]

    @model_validator(mode="after")
    def validate_source(self) -> "HumanMigrationSource":
        observation_ids = [item.observation_id for item in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("legacy observation ids must be unique")
        if set(self.expression_origins) != set(observation_ids):
            missing = sorted(set(observation_ids) - set(self.expression_origins))
            extra = sorted(set(self.expression_origins) - set(observation_ids))
            details: list[str] = []
            if missing:
                details.append(f"missing expression origins: {', '.join(missing)}")
            if extra:
                details.append(f"unknown expression origins: {', '.join(extra)}")
            raise ValueError("; ".join(details))

        subject_ids = {item.subject_id for item in self.observations}
        domains = {item.domain for item in self.observations}
        if len(subject_ids) != 1:
            raise ValueError("migration observations must share one subject")
        if len(domains) != 1:
            raise ValueError("migration observations must share one domain")

        known_ids = set(observation_ids)
        transition_ids = [item.transition_id for item in self.transitions]
        if len(transition_ids) != len(set(transition_ids)):
            raise ValueError("legacy transition ids must be unique")
        for transition in self.transitions:
            if transition.subject_id not in subject_ids:
                raise ValueError("migration transition subject does not match")
            if transition.domain not in domains:
                raise ValueError("migration transition domain does not match")
            if transition.from_observation_id not in known_ids:
                raise ValueError("migration transition has unknown source observation")
            if transition.to_observation_id not in known_ids:
                raise ValueError("migration transition has unknown target observation")
        return self

    @property
    def subject_id(self) -> str:
        return self.observations[0].subject_id

    @property
    def domain(self) -> str:
        return self.observations[0].domain


class GovernedHumanMigrationPlan(BaseModel):
    """Exact human migration source, protection policy, and state-write plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    migration_id: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    policy: HumanMigrationProtectionPolicy
    source: HumanMigrationSource
    state_write_plan: GovernedStateWritePlan

    @model_validator(mode="after")
    def validate_binding(self) -> "GovernedHumanMigrationPlan":
        if self.policy.subject_id != self.source.subject_id:
            raise ValueError("migration policy subject does not match source subject")
        if self.state_write_plan.operation.operation_id != "human-state-migration":
            raise ValueError("state-write operation is not a human migration")
        if self.state_write_plan.operation.action != "enki:human-migrate":
            raise ValueError("state-write action is not human migration")
        if self.state_write_plan.operation.subject_id != self.source.subject_id:
            raise ValueError("migration operation subject does not match source subject")
        return self

    @classmethod
    def create(
        cls,
        *,
        migration_id: str,
        transaction_id: str,
        purpose: str,
        policy: HumanMigrationProtectionPolicy,
        source: HumanMigrationSource,
        execution_context: ExecutionContext,
        acceptable_authority_classes: set[str],
        requested_at: datetime,
    ) -> "GovernedHumanMigrationPlan":
        policy.assert_authorized(purpose=purpose, at=requested_at)
        if policy.subject_id != source.subject_id:
            raise ValueError("migration policy subject does not match source subject")

        subject = SubjectRef(subject_id=source.subject_id, subject_type="PERSON")
        observations = [
            project_human_observation(
                record,
                expression_origin=source.expression_origins[record.observation_id],
            ).model_copy(
                update={
                    "metadata": {
                        **project_human_observation(
                            record,
                            expression_origin=source.expression_origins[
                                record.observation_id
                            ],
                        ).metadata,
                        "migration_id": migration_id,
                        "migration_policy_id": policy.policy_id,
                        "migration_purpose": purpose,
                        "privacy_classification": policy.privacy_classification.value,
                        "correction_allowed": policy.correction_allowed,
                        "retraction_allowed": policy.retraction_allowed,
                    }
                }
            )
            for record in source.observations
        ]
        relationships = [
            project_human_transition(record).model_copy(
                update={
                    "metadata": {
                        **project_human_transition(record).metadata,
                        "migration_id": migration_id,
                        "migration_policy_id": policy.policy_id,
                        "migration_purpose": purpose,
                        "privacy_classification": policy.privacy_classification.value,
                    }
                }
            )
            for record in source.transitions
        ]
        state_write_plan = GovernedStateWritePlan.create(
            transaction_id=transaction_id,
            subject=subject,
            domain=source.domain,
            observations=observations,
            relationships=relationships,
            known_observation_ids=set(),
            execution_context=execution_context,
            acceptable_authority_classes=acceptable_authority_classes,
            requested_at=requested_at,
            metadata={
                "migration_id": migration_id,
                "migration_policy_id": policy.policy_id,
                "migration_purpose": purpose,
                "legacy_observation_ids": [
                    item.observation_id for item in source.observations
                ],
                "legacy_transition_ids": [
                    item.transition_id for item in source.transitions
                ],
            },
        )
        migration_operation = state_write_plan.operation.model_copy(
            update={
                "operation_id": "human-state-migration",
                "action": "enki:human-migrate",
            }
        )
        state_write_plan = state_write_plan.model_copy(
            update={"operation": migration_operation}
        )
        return cls(
            migration_id=migration_id,
            purpose=purpose,
            policy=policy,
            source=source,
            state_write_plan=state_write_plan,
        )

    def assert_semantic_parity(self) -> None:
        projected = {
            item.observation_id: item
            for item in self.state_write_plan.payload.observations
        }
        for legacy in self.source.observations:
            current = projected[legacy.observation_id]
            expected_origin = self.source.expression_origins[legacy.observation_id]
            mismatches: list[str] = []
            if current.subject.subject_id != legacy.subject_id:
                mismatches.append("subject")
            if current.domain != legacy.domain:
                mismatches.append("domain")
            if current.statement != legacy.content:
                mismatches.append("content")
            if current.content_hash != legacy.content_hash:
                mismatches.append("content_hash")
            if current.observed_at != legacy.observed_at:
                mismatches.append("observed_at")
            if current.applicability.effective_from != legacy.effective_from:
                mismatches.append("effective_from")
            if current.applicability.effective_until != legacy.effective_until:
                mismatches.append("effective_until")
            if current.context != legacy.context:
                mismatches.append("context")
            if current.expression_origin != expected_origin:
                mismatches.append("expression_origin")
            if current.temporal_status.value != legacy.temporal_status.value:
                mismatches.append("temporal_status")
            if current.evidence[0].source_id != legacy.source_id:
                mismatches.append("source_id")
            if mismatches:
                raise RuntimeError(
                    f"semantic parity failed for {legacy.observation_id}: "
                    + ", ".join(mismatches)
                )


class ExecuteGovernedHumanMigration:
    """Execute and reconstruct one human migration through shared transaction paths."""

    def __init__(
        self,
        *,
        state_writer: EnkiStateWriter,
        approval_repository: ApprovalGrantRepository,
        journal: GovernedTransactionJournal,
        receipt_repository: GovernedTransactionReceiptRepository,
    ) -> None:
        self._state_write = ExecuteGovernedStateWrite(
            state_writer=state_writer,
            approval_repository=approval_repository,
            journal=journal,
            receipt_repository=receipt_repository,
        )

    def execute(
        self,
        plan: GovernedHumanMigrationPlan,
        *,
        approval_id: str,
        now: datetime | None = None,
        transaction_failure_hook: FailureHook | None = None,
        state_write_failure_hook: StateWriteFailureHook | None = None,
    ) -> GovernedTransactionReceipt:
        at = now or plan.state_write_plan.operation.requested_at
        plan.policy.assert_authorized(purpose=plan.purpose, at=at)
        plan.assert_semantic_parity()
        return self._state_write.execute(
            plan.state_write_plan,
            approval_id=approval_id,
            now=at,
            transaction_failure_hook=transaction_failure_hook,
            state_write_failure_hook=state_write_failure_hook,
        )
