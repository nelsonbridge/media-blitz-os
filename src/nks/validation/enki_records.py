"""Executable validation registry for Enki-owned canonical record families."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from nks.enki.contracts import ReconciliationFinding
from nks.enki.disclosure import DisclosureReceipt
from nks.governance.approvals import ApprovalGrant

ENKI_RECORD_MODELS: dict[str, type[BaseModel]] = {
    "approval-grants": ApprovalGrant,
    "reconciliation-findings": ReconciliationFinding,
    "disclosure-receipts": DisclosureReceipt,
}


def validate_enki_record(collection: str, payload: dict[str, Any]) -> list[str]:
    """Return deterministic contract violations for a canonical record payload."""

    model = ENKI_RECORD_MODELS.get(collection)
    if model is None:
        return []
    try:
        model.model_validate(payload)
    except ValidationError as exc:
        violations: list[str] = []
        for error in exc.errors(include_url=False):
            location = ".".join(str(part) for part in error["loc"]) or "<record>"
            violations.append(f"{location}: {error['msg']}")
        return sorted(violations)
    return []
