"""Append-only canonical workflow-event record repository."""

from __future__ import annotations

import json
from pathlib import Path

from nks.domain.models import WorkflowEvent


class WorkflowEventConflictError(RuntimeError):
    """Raised when an immutable event id already has different content."""


class JsonWorkflowEventRecordRepository:
    """Persist one immutable JSON record per workflow event under Class 1 state."""

    def __init__(self, repository_root: Path) -> None:
        self._directory = repository_root / "records" / "events"
        self._directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_identifier(event_id: str) -> str:
        return event_id.replace("/", "_").replace("\\", "_")

    def _path(self, event_id: str) -> Path:
        return self._directory / f"{self._safe_identifier(event_id)}.json"

    @staticmethod
    def _serialize(event: WorkflowEvent) -> str:
        return json.dumps(
            event.model_dump(mode="json", exclude_none=False),
            indent=2,
            sort_keys=True,
        ) + "\n"

    def append(self, event: WorkflowEvent) -> None:
        path = self._path(event.event_id)
        content = self._serialize(event)
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return
            raise WorkflowEventConflictError(
                f"workflow event id already exists with different content: {event.event_id}"
            )
        path.write_text(content, encoding="utf-8")

    def get(self, event_id: str) -> WorkflowEvent | None:
        path = self._path(event_id)
        if not path.exists():
            return None
        return WorkflowEvent.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[WorkflowEvent]:
        return [
            WorkflowEvent.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._directory.glob("*.json"))
        ]
