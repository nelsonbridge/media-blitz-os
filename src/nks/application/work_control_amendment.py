"""Approval-bound, reconstructable work-control amendments for evidence-bearing completion."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import (
    FailureHook,
    GovernedOperationAdapter,
    GovernedOperationPlan,
    GovernedOperationResult,
    GovernedTransactionExecutor,
    GovernedTransactionReceipt,
    canonical_sha256,
)
from nks.domain.work_control import BacklogItem, SprintRecord, WorkEvidence, WorkStatus
from nks.governance.approvals import ExecutionContext


class EvidenceQualification(StrEnum):
    IMPLEMENTATION = "IMPLEMENTATION"
    PATH_COVERAGE = "PATH_COVERAGE"
    VALIDATION = "VALIDATION"
    AUTHORITY = "AUTHORITY"


class QualifiedCompletionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence: WorkEvidence
    qualification: EvidenceQualification
    artifact_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class WorkControlAmendmentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    amendment_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    execution_context: ExecutionContext
    expected_sprint_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    expected_work_item_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    target_sprint: SprintRecord
    target_work_item: BacklogItem
    qualifying_evidence: list[QualifiedCompletionEvidence] = Field(min_length=1)
    acceptable_authority_classes: set[str] = Field(min_length=1)
    requested_at: datetime

    @model_validator(mode="after")
    def validate_completion_contract(self) -> "WorkControlAmendmentPlan":
        if self.target_sprint.sprint_id != self.target_work_item.sprint_id:
            raise ValueError("sprint and work item must remain linked")
        evidence_ids = {binding.evidence.evidence_id for binding in self.qualifying_evidence}
        if not evidence_ids <= {item.evidence_id for item in self.target_sprint.evidence}:
            raise ValueError("target sprint is missing bound completion evidence")
        if not evidence_ids <= {item.evidence_id for item in self.target_work_item.evidence}:
            raise ValueError("target work item is missing bound completion evidence")
        if self.target_sprint.status == WorkStatus.COMPLETE or self.target_work_item.status == WorkStatus.COMPLETE:
            required = set(EvidenceQualification)
            actual = {binding.qualification for binding in self.qualifying_evidence}
            if required - actual:
                raise ValueError("completion requires implementation, path coverage, validation, and authority evidence")
            if self.target_sprint.status != WorkStatus.COMPLETE:
                raise ValueError("work item cannot complete before its sprint amendment")
            if self.target_work_item.status != WorkStatus.COMPLETE:
                raise ValueError("sprint cannot complete before its work item amendment")
        return self

    @property
    def plan_sha256(self) -> str:
        return canonical_sha256(self)

    @property
    def target_pair_sha256(self) -> str:
        return canonical_sha256({"sprint": self.target_sprint, "work_item": self.target_work_item})


def build_completion_amendment(
    *,
    amendment_id: str,
    transaction_id: str,
    current_sprint: SprintRecord,
    current_work_item: BacklogItem,
    evidence: list[QualifiedCompletionEvidence],
    acceptable_authority_classes: set[str],
    requested_at: datetime,
    execution_context: ExecutionContext = ExecutionContext.TEST,
) -> WorkControlAmendmentPlan:
    sprint_evidence = {item.evidence_id: item for item in current_sprint.evidence}
    item_evidence = {item.evidence_id: item for item in current_work_item.evidence}
    for binding in evidence:
        sprint_evidence[binding.evidence.evidence_id] = binding.evidence
        item_evidence[binding.evidence.evidence_id] = binding.evidence
    target_sprint = current_sprint.model_copy(update={
        "status": WorkStatus.COMPLETE,
        "evidence": list(sprint_evidence.values()),
        "blocked_reason": None,
        "updated_at": requested_at,
    })
    target_item = current_work_item.model_copy(update={
        "status": WorkStatus.COMPLETE,
        "evidence": list(item_evidence.values()),
        "blocked_reason": None,
        "superseded_by": None,
        "updated_at": requested_at,
    })
    return WorkControlAmendmentPlan(
        amendment_id=amendment_id,
        transaction_id=transaction_id,
        execution_context=execution_context,
        expected_sprint_sha256=canonical_sha256(current_sprint),
        expected_work_item_sha256=canonical_sha256(current_work_item),
        target_sprint=target_sprint,
        target_work_item=target_item,
        qualifying_evidence=evidence,
        acceptable_authority_classes=acceptable_authority_classes,
        requested_at=requested_at,
    )


RepositoryFailureHook = Callable[[str], None]


class AtomicWorkControlAmendmentRepository:
    def __init__(self, root: Path, failure_hook: RepositoryFailureHook | None = None) -> None:
        self._root = root / "records"
        self._sprints = self._root / "sprints"
        self._items = self._root / "work-items"
        self._sprints.mkdir(parents=True, exist_ok=True)
        self._items.mkdir(parents=True, exist_ok=True)
        self._failure_hook = failure_hook or (lambda _stage: None)

    @staticmethod
    def _serialize(record: BaseModel) -> str:
        return json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"

    def _sprint_path(self, sprint_id: str) -> Path:
        return self._sprints / f"{sprint_id}.json"

    def _item_path(self, work_item_id: str) -> Path:
        return self._items / f"{work_item_id}.json"

    def get_sprint(self, sprint_id: str) -> SprintRecord:
        return SprintRecord.model_validate_json(self._sprint_path(sprint_id).read_text(encoding="utf-8"))

    def get_work_item(self, work_item_id: str) -> BacklogItem:
        return BacklogItem.model_validate_json(self._item_path(work_item_id).read_text(encoding="utf-8"))

    def seed(self, sprint: SprintRecord, work_item: BacklogItem) -> None:
        self._sprint_path(sprint.sprint_id).write_text(self._serialize(sprint), encoding="utf-8")
        self._item_path(work_item.work_item_id).write_text(self._serialize(work_item), encoding="utf-8")

    def apply(self, plan: WorkControlAmendmentPlan) -> str:
        current_sprint = self.get_sprint(plan.target_sprint.sprint_id)
        current_item = self.get_work_item(plan.target_work_item.work_item_id)
        sprint_hash = canonical_sha256(current_sprint)
        item_hash = canonical_sha256(current_item)
        target_sprint_hash = canonical_sha256(plan.target_sprint)
        target_item_hash = canonical_sha256(plan.target_work_item)
        if sprint_hash not in {plan.expected_sprint_sha256, target_sprint_hash}:
            raise RuntimeError("sprint state is stale or conflicts with amendment")
        if item_hash not in {plan.expected_work_item_sha256, target_item_hash}:
            raise RuntimeError("work-item state is stale or conflicts with amendment")
        if sprint_hash == target_sprint_hash and item_hash == target_item_hash:
            return plan.target_pair_sha256
        if sprint_hash == plan.expected_sprint_sha256:
            temp = self._sprint_path(plan.target_sprint.sprint_id).with_suffix(".json.tmp")
            temp.write_text(self._serialize(plan.target_sprint), encoding="utf-8")
            os.replace(temp, self._sprint_path(plan.target_sprint.sprint_id))
        self._failure_hook("after-sprint-replace")
        if item_hash == plan.expected_work_item_sha256:
            temp = self._item_path(plan.target_work_item.work_item_id).with_suffix(".json.tmp")
            temp.write_text(self._serialize(plan.target_work_item), encoding="utf-8")
            os.replace(temp, self._item_path(plan.target_work_item.work_item_id))
        self._failure_hook("after-work-item-replace")
        return plan.target_pair_sha256


class WorkControlAmendmentAdapter(GovernedOperationAdapter):
    def __init__(self, amendment: WorkControlAmendmentPlan, repository: AtomicWorkControlAmendmentRepository) -> None:
        self._amendment = amendment
        self._repository = repository

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        if plan.action != "work-control:amend":
            raise RuntimeError("operation action is not work-control amendment")
        if plan.transaction_id != self._amendment.transaction_id:
            raise RuntimeError("transaction does not match amendment")
        if plan.subject_id != self._amendment.target_sprint.sprint_id:
            raise RuntimeError("subject does not match sprint amendment")
        if plan.content_sha256 != self._amendment.plan_sha256:
            raise RuntimeError("content hash does not match amendment")
        if plan.execution_context != self._amendment.execution_context:
            raise RuntimeError("execution context does not match amendment")
        output = self._repository.apply(self._amendment)
        return GovernedOperationResult(
            output_sha256=output,
            metadata={
                "amendment_id": self._amendment.amendment_id,
                "sprint_id": self._amendment.target_sprint.sprint_id,
                "work_item_id": self._amendment.target_work_item.work_item_id,
                "target_status": self._amendment.target_sprint.status.value,
            },
        )


def build_governed_amendment_operation_plan(amendment: WorkControlAmendmentPlan) -> GovernedOperationPlan:
    return GovernedOperationPlan(
        operation_id=f"work-control-amendment:{amendment.amendment_id}",
        transaction_id=amendment.transaction_id,
        action="work-control:amend",
        subject_id=amendment.target_sprint.sprint_id,
        content_sha256=amendment.plan_sha256,
        execution_context=amendment.execution_context,
        acceptable_authority_classes=amendment.acceptable_authority_classes,
        requested_at=amendment.requested_at,
        metadata={
            "amendment_id": amendment.amendment_id,
            "work_item_id": amendment.target_work_item.work_item_id,
            "target_pair_sha256": amendment.target_pair_sha256,
        },
    )


def execute_governed_work_control_amendment(
    amendment: WorkControlAmendmentPlan,
    *,
    approval_id: str,
    transaction_executor: GovernedTransactionExecutor,
    repository: AtomicWorkControlAmendmentRepository,
    now: datetime,
    failure_hook: FailureHook | None = None,
) -> GovernedTransactionReceipt:
    return transaction_executor.execute(
        build_governed_amendment_operation_plan(amendment),
        approval_id=approval_id,
        adapter=WorkControlAmendmentAdapter(amendment, repository),
        now=now,
        failure_hook=failure_hook,
    )
