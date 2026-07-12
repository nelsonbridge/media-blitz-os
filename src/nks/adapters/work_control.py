"""Filesystem persistence for canonical backlog and sprint records."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from nks.domain.work_control import BacklogItem, SprintRecord

T = TypeVar("T", bound=BaseModel)


class JsonWorkControlRepository:
    def __init__(self, root: Path) -> None:
        self._root = root / "records"

    def _collection(self, name: str) -> Path:
        path = self._root / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _save(path: Path, record: BaseModel) -> None:
        serialized = record.model_dump_json(indent=2) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") == serialized:
            return
        path.write_text(serialized, encoding="utf-8")

    @staticmethod
    def _load(path: Path, model: type[T]) -> T | None:
        if not path.exists():
            return None
        return model.model_validate_json(path.read_text(encoding="utf-8"))

    def save_work_item(self, record: BacklogItem) -> BacklogItem:
        self._save(
            self._collection("work-items") / f"{record.work_item_id}.json", record
        )
        return record

    def get_work_item(self, work_item_id: str) -> BacklogItem | None:
        return self._load(
            self._collection("work-items") / f"{work_item_id}.json", BacklogItem
        )

    def list_work_items(self) -> list[BacklogItem]:
        return [
            BacklogItem.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._collection("work-items").glob("*.json"))
        ]

    def save_sprint(self, record: SprintRecord) -> SprintRecord:
        self._save(self._collection("sprints") / f"{record.sprint_id}.json", record)
        return record

    def get_sprint(self, sprint_id: str) -> SprintRecord | None:
        return self._load(
            self._collection("sprints") / f"{sprint_id}.json", SprintRecord
        )

    def list_sprints(self) -> list[SprintRecord]:
        records = [
            SprintRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._collection("sprints").glob("*.json"))
        ]
        return sorted(records, key=lambda item: item.sequence)
