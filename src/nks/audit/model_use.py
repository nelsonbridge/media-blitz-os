"""Forensic reconstruction of one governed model-use transaction."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from nks.application.human_state_model_use import (
    GovernedHumanStateModelUseReceipt,
    hash_model_use_package,
)
from nks.application.model_use_journal import ModelUseEventStage
from nks.domain.human_state import ModelFeedbackPackage
from nks.domain.models import WorkflowEvent
from nks.governance.approvals import ApprovalConsumptionStatus, ApprovalGrant

RecordT = TypeVar("RecordT", bound=BaseModel)


class ForensicStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    CONFLICT = "CONFLICT"


class ModelUseForensicReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_id: str
    status: ForensicStatus
    approval_id: str | None = None
    receipt_id: str | None = None
    event_ids: list[str] = Field(default_factory=list)
    event_stages: list[str] = Field(default_factory=list)
    payload_hash: str | None = None
    approval_consumed: bool = False
    canonical_receipt_present: bool = False
    generated_receipt_present: bool = False
    output_pair_present: bool = False
    reconstructable: bool = False
    issues: list[str] = Field(default_factory=list)


def _load_json_records(directory: Path, record_type: type[RecordT]) -> list[RecordT]:
    if not directory.exists():
        return []
    records: list[RecordT] = []
    for path in sorted(directory.glob("*.json")):
        records.append(record_type.model_validate_json(path.read_text(encoding="utf-8")))
    return records


def _generated_receipts_for_transaction(
    repository_root: Path,
    transaction_id: str,
) -> tuple[list[GovernedHumanStateModelUseReceipt], list[str]]:
    """Read only generated receipts that claim the requested transaction.

    Legacy or unrelated generated receipt formats do not make reconstruction
    crash. A malformed receipt that explicitly claims this transaction is
    reported as conflicting evidence.
    """

    output_root = repository_root / "generated" / "model-feedback"
    if not output_root.exists():
        return [], []

    receipts: list[GovernedHumanStateModelUseReceipt] = []
    issues: list[str] = []
    for path in sorted(output_root.glob("*/receipt.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if raw.get("transaction_id") != transaction_id:
            continue
        try:
            receipts.append(GovernedHumanStateModelUseReceipt.model_validate(raw))
        except ValidationError:
            issues.append(
                "generated receipt claiming this transaction is invalid: "
                f"{path.relative_to(repository_root)}"
            )
    return receipts, issues


def reconstruct_model_use(
    repository_root: Path,
    transaction_id: str,
) -> ModelUseForensicReport:
    """Reconstruct authority, journal, receipt, and payload consistency.

    A missing canonical receipt may still be reconstructable from one complete,
    internally consistent generated payload/receipt pair. Reconstructability is
    distinct from completeness: the report remains ``INCOMPLETE`` until the
    canonical record and required journal stages exist.
    """

    incomplete: list[str] = []
    conflicts: list[str] = []

    events = [
        event
        for event in _load_json_records(
            repository_root / "records" / "events", WorkflowEvent
        )
        if event.payload.get("transaction_id") == transaction_id
    ]
    stages = [str(event.payload.get("stage", "")) for event in events]
    approval_ids = {
        str(event.payload.get("approval_id"))
        for event in events
        if event.payload.get("approval_id")
    }
    if len(approval_ids) > 1:
        conflicts.append("transaction journal references multiple approval ids")
    approval_id = next(iter(approval_ids), None)

    canonical_matches = [
        receipt
        for receipt in _load_json_records(
            repository_root / "records" / "model-feedback-receipts",
            GovernedHumanStateModelUseReceipt,
        )
        if receipt.transaction_id == transaction_id
    ]
    if len(canonical_matches) > 1:
        conflicts.append("multiple canonical model-use receipts share transaction id")
    canonical_receipt = canonical_matches[0] if len(canonical_matches) == 1 else None

    generated_matches, generated_issues = _generated_receipts_for_transaction(
        repository_root,
        transaction_id,
    )
    conflicts.extend(generated_issues)
    if len(generated_matches) > 1:
        conflicts.append("multiple generated model-use receipts share transaction id")
    generated_receipt = generated_matches[0] if len(generated_matches) == 1 else None

    if canonical_receipt is not None and generated_receipt is not None:
        if canonical_receipt != generated_receipt:
            conflicts.append("generated and canonical receipts differ")

    receipt = canonical_receipt or generated_receipt
    if canonical_receipt is None:
        incomplete.append("canonical model-use receipt is missing")
    if generated_receipt is None:
        incomplete.append("generated model-use receipt is missing")

    if receipt is not None:
        if approval_id is None:
            approval_id = receipt.approval_id
        elif receipt.approval_id != approval_id:
            conflicts.append("journal and receipt approval ids differ")

    grant: ApprovalGrant | None = None
    if approval_id is None:
        incomplete.append("approval identity cannot be reconstructed")
    else:
        matching_grants = [
            grant
            for grant in _load_json_records(
                repository_root / "records" / "approval-grants",
                ApprovalGrant,
            )
            if grant.approval_id == approval_id
        ]
        if not matching_grants:
            incomplete.append("approval grant record is missing")
        elif len(matching_grants) > 1:
            conflicts.append("multiple approval grant records share approval id")
        else:
            grant = matching_grants[0]
            if grant.consumption_status != ApprovalConsumptionStatus.CONSUMED:
                incomplete.append("approval grant is not consumed")
            if grant.consumed_by_transaction_id != transaction_id:
                conflicts.append("approval grant was not consumed by this transaction")

    required_stages = {
        ModelUseEventStage.APPROVAL_RESERVED.value,
        ModelUseEventStage.AUTHORIZED.value,
        ModelUseEventStage.APPROVAL_CONSUMED.value,
        ModelUseEventStage.PERSISTED.value,
    }
    missing_stages = sorted(required_stages - set(stages))
    if missing_stages:
        incomplete.append(f"required journal stages are missing: {missing_stages}")
    if (
        ModelUseEventStage.RECOVERED.value in stages
        and ModelUseEventStage.FAILED.value not in stages
    ):
        conflicts.append("recovery stage exists without a recorded failure")

    output_pair_present = False
    payload_valid = False
    payload_hash: str | None = receipt.payload_hash if receipt else None
    if receipt is not None:
        output = repository_root / "generated" / "model-feedback" / receipt.receipt_id
        payload_path = output / "payload.json"
        receipt_path = output / "receipt.json"
        output_pair_present = payload_path.exists() and receipt_path.exists()
        if not output_pair_present:
            incomplete.append("generated payload and receipt pair is incomplete")
        else:
            try:
                on_disk_receipt = GovernedHumanStateModelUseReceipt.model_validate_json(
                    receipt_path.read_text(encoding="utf-8")
                )
                package = ModelFeedbackPackage.model_validate_json(
                    payload_path.read_text(encoding="utf-8")
                )
            except (ValidationError, OSError):
                conflicts.append("generated model-use output is invalid")
            else:
                if on_disk_receipt != receipt:
                    conflicts.append("selected and on-disk generated receipts differ")
                observed_hash = hash_model_use_package(package)
                if observed_hash != receipt.payload_hash:
                    conflicts.append(
                        "generated payload hash does not match selected receipt"
                    )
                else:
                    payload_valid = True

                if grant is not None:
                    if grant.content_sha256 != receipt.payload_hash:
                        conflicts.append(
                            "approval content hash does not match receipt payload hash"
                        )
                    if grant.subject_id != receipt.subject_id:
                        conflicts.append("approval subject does not match receipt subject")
                    if grant.execution_context != receipt.execution_context:
                        conflicts.append(
                            "approval execution context does not match receipt"
                        )

    approval_consumed = (
        grant is not None
        and grant.consumption_status == ApprovalConsumptionStatus.CONSUMED
        and grant.consumed_by_transaction_id == transaction_id
    )
    reconstructable = (
        not conflicts
        and generated_receipt is not None
        and output_pair_present
        and payload_valid
        and approval_consumed
    )
    issues = [*conflicts, *incomplete]
    status = (
        ForensicStatus.CONFLICT
        if conflicts
        else ForensicStatus.INCOMPLETE
        if incomplete
        else ForensicStatus.COMPLETE
    )

    return ModelUseForensicReport(
        transaction_id=transaction_id,
        status=status,
        approval_id=approval_id,
        receipt_id=receipt.receipt_id if receipt else None,
        event_ids=sorted(event.event_id for event in events),
        event_stages=stages,
        payload_hash=payload_hash,
        approval_consumed=approval_consumed,
        canonical_receipt_present=canonical_receipt is not None,
        generated_receipt_present=generated_receipt is not None,
        output_pair_present=output_pair_present,
        reconstructable=reconstructable,
        issues=issues,
    )
