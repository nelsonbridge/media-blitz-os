from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from nks.adapters.workflow_events import (
    JsonWorkflowEventRecordRepository,
    WorkflowEventConflictError,
)
from nks.application.model_use_journal import (
    ModelUseEventStage,
    ModelUseJournal,
    model_use_event_id,
)
from nks.domain.models import WorkflowEvent


def _now() -> datetime:
    return datetime(2026, 7, 14, 7, 0, tzinfo=timezone.utc)


def _record(journal: ModelUseJournal, stage: ModelUseEventStage, **kwargs) -> None:
    journal.record(
        stage,
        occurred_at=_now(),
        transaction_id="TX-1",
        subject_id="SUBJECT-1",
        approval_id="APR-1",
        policy_id="POL-1",
        payload_hash="sha256:" + "1" * 64,
        execution_context="TEST",
        **kwargs,
    )


def test_journal_events_are_deterministic_and_idempotent(tmp_path: Path) -> None:
    repository = JsonWorkflowEventRecordRepository(tmp_path)
    journal = ModelUseJournal(repository)

    _record(journal, ModelUseEventStage.APPROVAL_RESERVED)
    _record(journal, ModelUseEventStage.APPROVAL_RESERVED)

    events = repository.list()
    assert len(events) == 1
    event = events[0]
    assert event.event_id == model_use_event_id(
        "TX-1", ModelUseEventStage.APPROVAL_RESERVED
    )
    assert event.payload["logical_time"] == _now().isoformat()
    assert event.payload["payload_hash"] == "sha256:" + "1" * 64
    assert "content" not in event.payload
    assert "statement" not in event.payload


def test_failure_types_receive_distinct_append_only_event_ids(tmp_path: Path) -> None:
    repository = JsonWorkflowEventRecordRepository(tmp_path)
    journal = ModelUseJournal(repository)

    _record(journal, ModelUseEventStage.FAILED, failure_type="OSError")
    _record(journal, ModelUseEventStage.FAILED, failure_type="PermissionError")

    events = repository.list()
    assert len(events) == 2
    assert len({event.event_id for event in events}) == 2
    assert {event.payload["failure_type"] for event in events} == {
        "OSError",
        "PermissionError",
    }


def test_existing_event_id_with_different_content_fails(tmp_path: Path) -> None:
    repository = JsonWorkflowEventRecordRepository(tmp_path)
    event = WorkflowEvent(
        event_id="NKS-EVT-1",
        event_type="MODEL_USE_AUTHORIZED",
        subject_id="SUBJECT-1",
        payload={"transaction_id": "TX-1"},
    )
    repository.append(event)

    with pytest.raises(WorkflowEventConflictError, match="different content"):
        repository.append(
            event.model_copy(update={"payload": {"transaction_id": "TX-2"}})
        )
