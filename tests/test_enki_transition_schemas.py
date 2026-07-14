from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from nks.enki.transitions import (
    ConflictKind,
    StateSnapshot,
    TransitionRecord,
    TransitionType,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_transition_schemas_are_strict_draft_2020_12() -> None:
    for name in (
        "enki-state-snapshot.schema.json",
        "enki-transition.schema.json",
    ):
        schema = _schema(name)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False


def test_state_snapshot_schema_matches_runtime_contract_fields() -> None:
    schema = _schema("enki-state-snapshot.schema.json")
    model_schema = StateSnapshot.model_json_schema()

    assert set(schema["properties"]) == set(model_schema["properties"])
    assert set(schema["required"]) == set(model_schema["required"])
    assert schema["anyOf"] == [
        {"properties": {"observation_ids": {"minItems": 1}}},
        {"properties": {"relationship_ids": {"minItems": 1}}},
    ]


def test_transition_schema_matches_runtime_contract_fields_and_enums() -> None:
    schema = _schema("enki-transition.schema.json")
    model_schema = TransitionRecord.model_json_schema()

    assert set(schema["properties"]) == set(model_schema["properties"])
    assert set(schema["required"]) == set(model_schema["required"])
    assert set(schema["properties"]["transition_type"]["enum"]) == {
        item.value for item in TransitionType
    }
    assert set(schema["properties"]["detected_conflicts"]["items"]["enum"]) == {
        item.value for item in ConflictKind
    }
