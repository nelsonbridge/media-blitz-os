"""Deterministic operation reconstruction from immutable Enki evidence."""

from __future__ import annotations

from nks.application.governed_transactions import canonical_sha256
from nks.application.forensic_contracts import (
    ForensicRecord,
    ReconstructionRequest,
    ReconstructionResult,
    ReconstructionStatus,
    evidence_hash,
)


def reconstruct_operation(
    request: ReconstructionRequest,
    records: list[ForensicRecord],
) -> ReconstructionResult:
    selected = [record for record in records if record.transaction_id == request.transaction_id]
    conflicts: list[str] = []
    by_id: dict[str, ForensicRecord] = {}

    for record in selected:
        existing = by_id.get(record.record_id)
        if existing is not None and existing != record:
            conflicts.append(f"record id has conflicting immutable content: {record.record_id}")
        by_id[record.record_id] = record
        if record.operation_family != request.operation_family:
            conflicts.append(f"operation family mismatch: {record.record_id}")
        if record.operation_id != request.operation_id:
            conflicts.append(f"operation id mismatch: {record.record_id}")
        if record.execution_context != request.execution_context:
            conflicts.append(f"execution context mismatch: {record.record_id}")
        if record.authority_class not in request.acceptable_authority_classes:
            conflicts.append(f"authority class is not accepted: {record.record_id}")
        if record.content_sha256 != canonical_sha256(record.payload):
            conflicts.append(f"record payload hash mismatch: {record.record_id}")
        plan_hash = record.payload.get("plan_sha256")
        if request.expected_plan_sha256 and plan_hash and plan_hash != request.expected_plan_sha256:
            conflicts.append(f"plan hash mismatch: {record.record_id}")

    unique = sorted(by_id.values(), key=lambda item: item.record_id)
    record_types = {record.record_type for record in unique}
    missing = sorted(request.required_record_types - record_types)
    terminal = [record for record in unique if record.record_type == "transaction-receipt"]
    states = {
        str(record.payload.get("terminal_state"))
        for record in terminal
        if record.payload.get("terminal_state") is not None
    }
    if len(states) > 1:
        conflicts.append("multiple incompatible terminal states")
    outputs = {
        str(record.payload["output_sha256"])
        for record in terminal
        if record.payload.get("output_sha256") is not None
    }
    if len(outputs) > 1:
        conflicts.append("multiple incompatible output hashes")
    output = next(iter(outputs), None)
    if request.expected_output_sha256 and output and output != request.expected_output_sha256:
        conflicts.append("terminal output hash does not match expectation")

    common = dict(
        operation_family=request.operation_family,
        operation_id=request.operation_id,
        transaction_id=request.transaction_id,
        evidence_sha256=evidence_hash(unique),
        record_ids=[record.record_id for record in unique],
        missing_record_types=missing,
        terminal_state=next(iter(states), None),
        output_sha256=output,
    )
    if conflicts:
        return ReconstructionResult(
            status=ReconstructionStatus.CONFLICT,
            conflicts=sorted(set(conflicts)),
            **common,
        )
    state = next(iter(states), None)
    if state == "ROLLED_BACK":
        return ReconstructionResult(status=ReconstructionStatus.ROLLED_BACK, **common)
    if state in {"COMMITTED", "RECOVERED"}:
        if missing and set(missing) <= request.repairable_record_types:
            return ReconstructionResult(
                status=ReconstructionStatus.REPAIRABLE,
                repair_actions=[f"rebuild:{item}" for item in missing],
                **common,
            )
        if missing:
            return ReconstructionResult(status=ReconstructionStatus.INCOMPLETE, **common)
        return ReconstructionResult(status=ReconstructionStatus.COMPLETE, **common)
    if {"approval-consumed", "effect", "operation-output"} & record_types:
        return ReconstructionResult(
            status=ReconstructionStatus.REPAIRABLE,
            repair_actions=["exact-retry", *[f"rebuild:{item}" for item in missing]],
            **common,
        )
    return ReconstructionResult(status=ReconstructionStatus.INCOMPLETE, **common)
