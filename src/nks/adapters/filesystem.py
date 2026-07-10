"""Local filesystem adapter for portable NKS execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generic, TypeVar

from nks.domain.models import CanonicalRecord, WorkflowEvent

RecordT = TypeVar("RecordT", bound=CanonicalRecord)


class JsonRecordRepository(Generic[RecordT]):
    def __init__(self, root: Path, record_type: type[RecordT], collection: str) -> None:
        self._directory = root / collection
        self._record_type = record_type
        self._directory.mkdir(parents=True, exist_ok=True)

    def _path(self, record_id: str) -> Path:
        safe_id = record_id.replace("/", "_")
        return self._directory / f"{safe_id}.json"

    def get(self, record_id: str) -> RecordT | None:
        path = self._path(record_id)
        if not path.exists():
            return None
        return self._record_type.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, record: RecordT) -> RecordT:
        path = self._path(record.id)
        serialized = record.model_dump_json(indent=2)
        if path.exists() and path.read_text(encoding="utf-8") == serialized:
            return record
        path.write_text(serialized, encoding="utf-8")
        return record

    def list(self) -> list[RecordT]:
        return [
            self._record_type.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._directory.glob("*.json"))
        ]


class JsonEventRepository:
    def __init__(self, root: Path) -> None:
        self._path = root / "events" / "events.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: WorkflowEvent) -> None:
        existing_ids = {item.event_id for item in self.list()}
        if event.event_id in existing_ids:
            return
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")

    def list(self) -> list[WorkflowEvent]:
        if not self._path.exists():
            return []
        return [
            WorkflowEvent.model_validate_json(line)
            for line in self._path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
