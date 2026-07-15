"""Immutable policy lifecycle, deterministic simulation, and governed activation.

Policy simulation is side-effect free. Activation, rollback, and retirement are
separate approval-bound governed transactions. TEST policy authority can never
activate or replace a PRODUCTION policy.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import (
    GovernedOperationPlan,
    GovernedOperationResult,
    GovernedTransactionExecutor,
    GovernedTransactionReceipt,
    canonical_sha256,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


class PolicyEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"


class PolicyOperator(StrEnum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    IN = "IN"
    EXISTS = "EXISTS"


class PolicyLifecycleAction(StrEnum):
    ACTIVATE = "ACTIVATE"
    ROLLBACK = "ROLLBACK"
    RETIRE = "RETIRE"


class PolicyRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1)
    attribute: str = Field(min_length=1)
    operator: PolicyOperator
    expected: object | None = None
    effect: PolicyEffect
    priority: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_expected(self) -> "PolicyRule":
        if self.operator == PolicyOperator.EXISTS and self.expected is not None:
            raise ValueError("EXISTS rules cannot carry expected values")
        if self.operator != PolicyOperator.EXISTS and self.expected is None:
            raise ValueError("non-EXISTS rules require expected values")
        if self.operator == PolicyOperator.IN and not isinstance(self.expected, list):
            raise ValueError("IN rules require a list expected value")
        return self


class PolicyBundle(BaseModel):
    """Immutable, attributable, context-bound policy version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    boundary: BoundaryContext
    authored_by: str = Field(min_length=1)
    authored_at: datetime
    previous_bundle_sha256: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    rules: list[PolicyRule] = Field(min_length=1)
    default_effect: PolicyEffect
    bundle_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_bundle(self) -> "PolicyBundle":
        if self.version == 1 and self.previous_bundle_sha256 is not None:
            raise ValueError("first policy version cannot have a predecessor")
        if self.version > 1 and self.previous_bundle_sha256 is None:
            raise ValueError("later policy versions require a predecessor hash")
        identifiers = [rule.rule_id for rule in self.rules]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("policy rule identifiers must be unique")
        priorities = [rule.priority for rule in self.rules]
        if len(priorities) != len(set(priorities)):
            raise ValueError("policy rule priorities must be unique")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"bundle_sha256"}))
        if self.bundle_sha256 != expected:
            raise ValueError("policy bundle hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "PolicyBundle":
        payload = dict(values)
        payload["bundle_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class PolicyEvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1)
    attributes: dict[str, object]


class PolicyCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    effect: PolicyEffect
    matched_rule_id: str | None = None


class PolicySimulationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    simulation_id: str
    baseline_bundle_sha256: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    candidate_bundle_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    candidate_results: list[PolicyCaseResult]
    baseline_results: list[PolicyCaseResult] = Field(default_factory=list)
    changed_case_ids: list[str] = Field(default_factory=list)
    execution_context: ExecutionContext = ExecutionContext.TEST
    canonical_state_mutated: bool = False
    report_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_simulation(self) -> "PolicySimulationReport":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("policy simulation is TEST-only")
        if self.canonical_state_mutated:
            raise ValueError("policy simulation cannot mutate canonical state")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"report_sha256"}))
        if self.report_sha256 != expected:
            raise ValueError("policy simulation report hash is invalid")
        return self


class PolicyComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_sha256: str
    candidate_sha256: str
    added_rule_ids: list[str]
    removed_rule_ids: list[str]
    changed_rule_ids: list[str]
    default_effect_changed: bool
    comparison_sha256: str

    @model_validator(mode="after")
    def validate_hash(self) -> "PolicyComparison":
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"comparison_sha256"}))
        if self.comparison_sha256 != expected:
            raise ValueError("policy comparison hash is invalid")
        return self


class PolicyActivationRecord(BaseModel):
    """Append-only lifecycle record preserving exact historical attribution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    activation_id: str
    policy_id: str
    action: PolicyLifecycleAction
    from_bundle_sha256: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    to_bundle_sha256: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    boundary: BoundaryContext
    transaction_id: str
    approval_id: str
    recorded_at: datetime
    record_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_transition(self) -> "PolicyActivationRecord":
        if self.action in {PolicyLifecycleAction.ACTIVATE, PolicyLifecycleAction.ROLLBACK}:
            if self.to_bundle_sha256 is None:
                raise ValueError("activation and rollback require a target bundle")
        if self.action == PolicyLifecycleAction.RETIRE and self.to_bundle_sha256 is not None:
            raise ValueError("retirement cannot claim an active target bundle")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"record_sha256"}))
        if self.record_sha256 != expected:
            raise ValueError("policy activation record hash is invalid")
        return self


class PolicyRepository(Protocol):
    def append_bundle(self, bundle: PolicyBundle) -> None: ...
    def get_bundle(self, bundle_sha256: str) -> PolicyBundle | None: ...
    def list_bundles(self, policy_id: str) -> list[PolicyBundle]: ...
    def get_active_bundle(self, policy_id: str, boundary: BoundaryContext) -> PolicyBundle | None: ...
    def append_activation(self, record: PolicyActivationRecord) -> None: ...
    def list_activations(self, policy_id: str) -> list[PolicyActivationRecord]: ...


def _matches(rule: PolicyRule, attributes: dict[str, object]) -> bool:
    present = rule.attribute in attributes
    actual = attributes.get(rule.attribute)
    if rule.operator == PolicyOperator.EXISTS:
        return present
    if not present:
        return False
    if rule.operator == PolicyOperator.EQUALS:
        return actual == rule.expected
    if rule.operator == PolicyOperator.NOT_EQUALS:
        return actual != rule.expected
    if rule.operator == PolicyOperator.IN:
        return actual in (rule.expected or [])
    return False


def evaluate_policy(bundle: PolicyBundle, case: PolicyEvaluationCase) -> PolicyCaseResult:
    for rule in sorted(bundle.rules, key=lambda item: item.priority):
        if _matches(rule, case.attributes):
            return PolicyCaseResult(
                case_id=case.case_id,
                effect=rule.effect,
                matched_rule_id=rule.rule_id,
            )
    return PolicyCaseResult(case_id=case.case_id, effect=bundle.default_effect)


def compare_policies(baseline: PolicyBundle, candidate: PolicyBundle) -> PolicyComparison:
    if baseline.policy_id != candidate.policy_id or baseline.boundary != candidate.boundary:
        raise ValueError("policy comparison requires the same policy and boundary")
    left = {rule.rule_id: rule for rule in baseline.rules}
    right = {rule.rule_id: rule for rule in candidate.rules}
    payload = {
        "baseline_sha256": baseline.bundle_sha256,
        "candidate_sha256": candidate.bundle_sha256,
        "added_rule_ids": sorted(right.keys() - left.keys()),
        "removed_rule_ids": sorted(left.keys() - right.keys()),
        "changed_rule_ids": sorted(
            identifier for identifier in left.keys() & right.keys() if left[identifier] != right[identifier]
        ),
        "default_effect_changed": baseline.default_effect != candidate.default_effect,
    }
    return PolicyComparison(**payload, comparison_sha256=canonical_sha256(payload))


def simulate_policy(
    candidate: PolicyBundle,
    cases: list[PolicyEvaluationCase],
    *,
    baseline: PolicyBundle | None = None,
) -> PolicySimulationReport:
    if candidate.boundary.execution_context != ExecutionContext.TEST:
        raise ValueError("TEST simulation cannot evaluate a PRODUCTION policy as activatable evidence")
    if baseline is not None and baseline.boundary != candidate.boundary:
        raise ValueError("simulation baseline and candidate boundaries must match")
    candidate_results = [evaluate_policy(candidate, case) for case in cases]
    baseline_results = [evaluate_policy(baseline, case) for case in cases] if baseline else []
    baseline_map = {result.case_id: result for result in baseline_results}
    changed = [
        result.case_id
        for result in candidate_results
        if baseline_map.get(result.case_id) != result
    ] if baseline else [result.case_id for result in candidate_results]
    payload = {
        "simulation_id": f"SIM-{candidate.bundle_sha256.removeprefix('sha256:')[:24]}",
        "baseline_bundle_sha256": baseline.bundle_sha256 if baseline else None,
        "candidate_bundle_sha256": candidate.bundle_sha256,
        "candidate_results": candidate_results,
        "baseline_results": baseline_results,
        "changed_case_ids": sorted(changed),
        "execution_context": ExecutionContext.TEST,
        "canonical_state_mutated": False,
    }
    return PolicySimulationReport(**payload, report_sha256=canonical_sha256(payload))


class PolicyLifecycleAdapter:
    def __init__(
        self,
        repository: PolicyRepository,
        *,
        bundle: PolicyBundle | None,
        action: PolicyLifecycleAction,
        approval_id: str,
    ) -> None:
        self._repository = repository
        self._bundle = bundle
        self._action = action
        self._approval_id = approval_id

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        active = self._repository.get_active_bundle(plan.subject_id, self._boundary(plan))
        target = self._bundle
        if self._action != PolicyLifecycleAction.RETIRE and target is None:
            raise ValueError("activation or rollback requires a bundle")
        if target is not None:
            if target.policy_id != plan.subject_id:
                raise ValueError("policy plan subject does not match bundle")
            if target.boundary.execution_context != plan.execution_context:
                raise ValueError("policy bundle context does not match plan")
            if target.boundary != self._boundary(plan):
                raise ValueError("policy bundle boundary does not match plan")
            self._repository.append_bundle(target)
        record_payload = {
            "activation_id": f"POL-ACT-{plan.transaction_id}",
            "policy_id": plan.subject_id,
            "action": self._action,
            "from_bundle_sha256": active.bundle_sha256 if active else None,
            "to_bundle_sha256": target.bundle_sha256 if target else None,
            "boundary": self._boundary(plan),
            "transaction_id": plan.transaction_id,
            "approval_id": self._approval_id,
            "recorded_at": plan.requested_at,
        }
        record = PolicyActivationRecord(
            **record_payload,
            record_sha256=canonical_sha256(record_payload),
        )
        self._repository.append_activation(record)
        return GovernedOperationResult(
            output_sha256=record.record_sha256,
            metadata={
                "policy_id": plan.subject_id,
                "action": self._action.value,
                "policy_bundle_sha256": target.bundle_sha256 if target else None,
            },
        )

    @staticmethod
    def _boundary(plan: GovernedOperationPlan) -> BoundaryContext:
        raw = plan.metadata.get("boundary")
        if not isinstance(raw, dict):
            raise ValueError("policy lifecycle plan requires boundary metadata")
        return BoundaryContext.model_validate(raw)


class ExecutePolicyLifecycle:
    def __init__(self, executor: GovernedTransactionExecutor, repository: PolicyRepository) -> None:
        self._executor = executor
        self._repository = repository

    def execute(
        self,
        *,
        action: PolicyLifecycleAction,
        policy_id: str,
        boundary: BoundaryContext,
        approval_id: str,
        transaction_id: str,
        requested_at: datetime,
        acceptable_authority_classes: set[str],
        bundle: PolicyBundle | None = None,
    ) -> GovernedTransactionReceipt:
        if boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 17 lifecycle execution is TEST-only")
        content = {
            "action": action,
            "policy_id": policy_id,
            "boundary": boundary,
            "bundle_sha256": bundle.bundle_sha256 if bundle else None,
        }
        plan = GovernedOperationPlan(
            operation_id=f"POLICY-{action.value}-{policy_id}",
            transaction_id=transaction_id,
            action=f"policy:{action.value.lower()}",
            subject_id=policy_id,
            content_sha256=canonical_sha256(content),
            execution_context=ExecutionContext.TEST,
            acceptable_authority_classes=acceptable_authority_classes,
            requested_at=requested_at,
            metadata={"boundary": boundary.model_dump(mode="json")},
        )
        return self._executor.execute(
            plan,
            approval_id=approval_id,
            adapter=PolicyLifecycleAdapter(
                self._repository,
                bundle=bundle,
                action=action,
                approval_id=approval_id,
            ),
            now=requested_at,
        )


def attribute_historical_decision(
    repository: PolicyRepository,
    *,
    policy_id: str,
    activation_id: str,
) -> PolicyBundle | None:
    for activation in repository.list_activations(policy_id):
        if activation.activation_id == activation_id and activation.to_bundle_sha256:
            return repository.get_bundle(activation.to_bundle_sha256)
    return None
