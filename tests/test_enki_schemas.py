from __future__ import annotations

import json
from pathlib import Path

from nks.application.governed_transactions import (
    GovernedTransactionEvent,
    GovernedTransactionReceipt,
    RecoveryStrategy,
    TransactionStage,
    TransactionTerminalState,
)
from nks.enki.contracts import (
    ConfidenceLevel,
    DisclosureAction,
    FindingKind,
    ReconciliationFinding,
)
from nks.enki.disclosure import DisclosureAudience, DisclosureReceipt
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_enki_schemas_use_strict_draft_2020_12() -> None:
    for name in (
        "approval-grant.schema.json",
        "reconciliation-finding.schema.json",
        "disclosure-receipt.schema.json",
        "governed-transaction-event.schema.json",
        "governed-transaction-receipt.schema.json",
    ):
        schema = _schema(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False
        assert schema["type"] == "object"


def test_approval_schema_fields_and_enums_match_contract() -> None:
    schema = _schema("approval-grant.schema.json")
    model_schema = ApprovalGrant.model_json_schema()

    assert set(schema["properties"]) == set(model_schema["properties"])
    assert set(schema["properties"]["decision"]["enum"]) == {
        item.value for item in ApprovalDecision
    }
    assert set(schema["properties"]["execution_context"]["enum"]) == {
        item.value for item in ExecutionContext
    }
    assert set(schema["properties"]["consumption_status"]["enum"]) == {
        item.value for item in ApprovalConsumptionStatus
    }


def test_finding_schema_fields_and_enums_match_contract() -> None:
    schema = _schema("reconciliation-finding.schema.json")
    model_schema = ReconciliationFinding.model_json_schema()

    assert set(schema["properties"]) == set(model_schema["properties"])
    assert set(schema["properties"]["finding_kind"]["enum"]) == {
        item.value for item in FindingKind
    }
    confidence = schema["$defs"]["confidence_assertion"]
    assert set(confidence["properties"]["level"]["enum"]) == {
        item.value for item in ConfidenceLevel
    }
    assert schema["anyOf"] == [
        {"properties": {"observation_ids": {"minItems": 1}}},
        {"properties": {"relationship_ids": {"minItems": 1}}},
    ]


def test_disclosure_schema_fields_and_enums_match_contract() -> None:
    schema = _schema("disclosure-receipt.schema.json")
    model_schema = DisclosureReceipt.model_json_schema()

    assert set(schema["properties"]) == set(model_schema["properties"])
    assert set(schema["properties"]["audience"]["enum"]) == {
        item.value for item in DisclosureAudience
    }
    decision = schema["$defs"]["disclosure_decision"]
    assert set(decision["properties"]["action"]["enum"]) == {
        item.value for item in DisclosureAction
    }


def test_governed_transaction_event_schema_matches_contract() -> None:
    schema = _schema("governed-transaction-event.schema.json")
    model_schema = GovernedTransactionEvent.model_json_schema()

    assert set(schema["properties"]) == set(model_schema["properties"])
    assert set(schema["properties"]["stage"]["enum"]) == {
        item.value for item in TransactionStage
    }


def test_governed_transaction_receipt_schema_matches_contract() -> None:
    schema = _schema("governed-transaction-receipt.schema.json")
    model_schema = GovernedTransactionReceipt.model_json_schema()

    assert set(schema["properties"]) == set(model_schema["properties"])
    assert set(schema["properties"]["terminal_state"]["enum"]) == {
        item.value for item in TransactionTerminalState
    }
    assert set(schema["properties"]["recovery_strategy"]["enum"]) == {
        item.value for item in RecoveryStrategy
    }
    assert set(schema["properties"]["execution_context"]["enum"]) == {
        item.value for item in ExecutionContext
    }
