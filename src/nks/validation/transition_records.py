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

    violations: set[str] = set()
    if collection == "enki-state-snapshots":
        observation_ids = payload.get("observation_ids") or []
        relationship_ids = payload.get("relationship_ids") or []
        if not observation_ids and not relationship_ids:
            violations.add(
                "<record>: Value error, a state snapshot must reference canonical state"
            )

    try:
        model.model_validate(payload)
    except ValidationError as exc:
        for error in exc.errors(include_url=False):
            location = ".".join(str(part) for part in error["loc"]) or "<record>"
            violations.add(f"{location}: {error['msg']}")

    return sorted(violations)
