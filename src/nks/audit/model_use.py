"""Forensic reconstruction of one governed model-use transaction."""

from __future__ import annotations

import hashlib
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from nks.application.human_state_model_use import GovernedHumanStateModelUseReceipt
from nks.application.model_use_journal import ModelUseEventStage
from nks.domain.human_state import ModelFeedbackPackage
from nks.domain.models import WorkflowEvent
from nks.governance.approvals import ApprovalConsumptionStatus, ApprovalGrant


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
    output_pair_present: bool = False
    reconstructable: bool = False
    issues: list[str] = Field(default_factory=list)


def _hash_package(package: ModelFeedbackPackage) -> str:
    serialized = package.model_dump_json(exclude_none=False)
    return "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _load_json_records(directory: Path, record_type):
    if not directory.exists():
        return []
    records = []
    for path in sorted(directory.glob("*.json")):
        records.append(record_type.model_validate_json(path.read_text(encoding="utf-8")))
    return records


def reconstruct_model_use(
    repository_root: Path,
    transaction_id: str,
) -> ModelUseForensicReport:
    """Reconstruct authority, journal, receipt, and payload consistency."""

    issues: list[str] = []
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
        issues.append("transaction journal references multiple approval ids")
    approval_id = next(iter(approval_ids), None)

    receipts = [
        receipt
        for receipt in _load_json_records(
            repository_root / "records" / "model-feedback-receipts",
            GovernedHumanStateModelUseReceipt,
        )
        if receipt.transaction_id == transaction_id
    ]
    if len(receipts) > 1:
        issues.append("multiple canonical model-use receipts share transaction id")
    receipt = receipts[0] if len(receipts) == 1 else None
    if receipt is not None:
        if approval_id is None:
            approval_id = receipt.approval_id
        elif receipt.approval_id != approval_id:
            issues.append("journal and canonical receipt approval ids differ")

    grant: ApprovalGrant | None = None
    if approval_id is None:
        issues.append("approval identity cannot be reconstructed")
    else:
        path = repository_root / "records" / "approval-grants" / f"{approval_id}.json"
        if not path.exists():
            issues.append("approval grant record is missing")
        else:
            grant = ApprovalGrant.model_validate_json(path.read_text(encoding="utf-8"))
            if grant.consumption_status != ApprovalConsumptionStatus.CONSUMED:
                issues.append("approval grant is not consumed")
            if grant.consumed_by_transaction_id != transaction_id:
                issues.append("approval grant was not consumed by this transaction")

    required_stages = {
        ModelUseEventStage.APPROVAL_RESERVED.value,
        ModelUseEventStage.AUTHORIZED.value,
        ModelUseEventStage.APPROVAL_CONSUMED.value,
        ModelUseEventStage.PERSISTED.value,
    }
    missing_stages = sorted(required_stages - set(stages))
    if missing_stages:
        issues.append(f"required journal stages are missing: {missing_stages}")
    if (
        ModelUseEventStage.RECOVERED.value in stages
        and ModelUseEventStage.FAILED.value not in stages
    ):
        issues.append("recovery stage exists without a recorded failure")

    output_pair_present = False
    payload_hash: str | None = receipt.payload_hash if receipt else None
    if receipt is None:
        issues.append("canonical model-use receipt is missing")
    else:
        output = repository_root / "generated" / "model-feedback" / receipt.receipt_id
        payload_path = output / "payload.json"
        receipt_path = output / "receipt.json"
        output_pair_present = payload_path.exists() and receipt_path.exists()
        if not output_pair_present:
            issues.append("generated payload and receipt pair is incomplete")
        else:
            generated_receipt = GovernedHumanStateModelUseReceipt.model_validate_json(
                receipt_path.read_text(encoding="utf-8")
            )
            if generated_receipt != receipt:
                issues.append("generated and canonical receipts differ")
            package = ModelFeedbackPackage.model_validate_json(
                payload_path.read_text(encoding="utf-8")
            )
            observed_hash = _hash_package(package)
            if observed_hash != receipt.payload_hash:
                issues.append("generated payload hash does not match canonical receipt")
            if grant is not None:
                if grant.content_sha256 != receipt.payload_hash:
                    issues.append("approval content hash does not match receipt payload hash")
                if grant.subject_id != receipt.subject_id:
                    issues.append("approval subject does not match receipt subject")
                if grant.execution_context != receipt.execution_context:
                    issues.append("approval execution context does not match receipt")

    conflict_markers = (
        "differ",
        "multiple",
        "does not match",
        "was not consumed by",
    )
    status = (
        ForensicStatus.CONFLICT
        if any(marker in issue for issue in issues for marker in conflict_markers)
        else ForensicStatus.INCOMPLETE
        if issues
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
        approval_consumed=(
            grant is not None
            and grant.consumption_status == ApprovalConsumptionStatus.CONSUMED
            and grant.consumed_by_transaction_id == transaction_id
        ),
        canonical_receipt_present=receipt is not None,
        output_pair_present=output_pair_present,
        reconstructable=not issues,
        issues=issues,
    )
