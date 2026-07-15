from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

from nks.application.boundary_isolation import BoundaryRecord
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas"


def _load(name: str) -> dict[str, object]:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


def test_boundary_schemas_are_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(_load("boundary-context.schema.json"))
    Draft202012Validator.check_schema(_load("boundary-record.schema.json"))


def test_runtime_boundary_record_validates_against_schema() -> None:
    context_schema = _load("boundary-context.schema.json")
    record_schema = _load("boundary-record.schema.json")
    store = {
        context_schema["$id"]: context_schema,
        "boundary-context.schema.json": context_schema,
    }
    resolver = RefResolver.from_schema(record_schema, store=store)
    validator = Draft202012Validator(record_schema, resolver=resolver)

    boundary = BoundaryContext(
        namespace_id="NKS-TEST",
        tenant_id="TENANT-A",
        subject_id="SUBJECT-1",
        domain="operations",
        audience="internal",
        execution_context=ExecutionContext.TEST,
    )
    record = BoundaryRecord.create(
        record_id="REC-1",
        subject_type="ORGANIZATION",
        boundary=boundary,
        payload={"classification": "SYNTHETIC/TEST"},
    )
    validator.validate(record.model_dump(mode="json"))
