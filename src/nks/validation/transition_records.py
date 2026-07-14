"""Executable validation for canonical Enki transition record families."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from nks.enki.transitions import StateSnapshot, TransitionRecord

TRANSITION_RECORD_MODELS: dict[str, type[BaseModel]] = {
    "enki-state-snapshots": StateSnapshot,
    "enki-transitions": TransitionRecord,
}


def validate_transition_record(
    collection: str,
    payload: dict[str, Any],
) -> list[str]:
    """Return deterministic runtime contract violations for transition records."""

    model = TRANSITION_RECORD_MODELS.get(collection)
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
