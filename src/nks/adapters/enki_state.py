"""Append-only persistence for domain-neutral Enki observations and relationships."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from nks.enki.contracts import Observation, RelationshipAssertion, SubjectRef

RecordT = TypeVar("RecordT", bound=BaseModel)


class EnkiStateConflictError(RuntimeError):
    """Raised when an immutable Enki identifier already has different content."""


class JsonEnkiStateRepository:
    """Persist generic observations and relationship assertions without schema forks."""

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root

    def _collection(self, name: str) -> Path:
        directory = self._root / "records" / name
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def _safe_identifier(value: str) -> str:
        return value.replace("/", "_").replace("\\", "_")

    def _path(self, collection: str, record_id: str) -> Path:
        return self._collection(collection) / f"{self._safe_identifier(record_id)}.json"

    @staticmethod
    def _serialize(record: BaseModel) -> str:
        return json.dumps(
            record.model_dump(mode="json", exclude_none=False),
            indent=2,
            sort_keys=True,
        ) + "\n"

    def _append(self, collection: str, record_id: str, record: BaseModel) -> None:
        path = self._path(collection, record_id)
        content = self._serialize(record)
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return
            raise EnkiStateConflictError(
                f"immutable Enki record id already exists with different content: {record_id}"
            )
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _read(path: Path, record_type: type[RecordT]) -> RecordT:
        return record_type.model_validate_json(path.read_text(encoding="utf-8"))

    def append_observations(self, observations: Iterable[Observation]) -> None:
        for observation in observations:
            self._append("enki-observations", observation.observation_id, observation)

    def append_relationships(
        self,
        relationships: Iterable[RelationshipAssertion],
    ) -> None:
        for relationship in relationships:
            self._append(
                "relationship-assertions",
                relationship.relationship_id,
                relationship,
            )

    def get_observation(self, observation_id: str) -> Observation | None:
        path = self._path("enki-observations", observation_id)
        if not path.exists():
            return None
        return self._read(path, Observation)

    def get_relationship(self, relationship_id: str) -> RelationshipAssertion | None:
        path = self._path("relationship-assertions", relationship_id)
        if not path.exists():
            return None
        return self._read(path, RelationshipAssertion)

    def list_observations(self, subject: SubjectRef, domain: str) -> list[Observation]:
        return [
            record
            for path in sorted(self._collection("enki-observations").glob("*.json"))
            if (record := self._read(path, Observation)).subject == subject
            and record.domain == domain
        ]

    def list_relationships(
        self,
        subject: SubjectRef,
        domain: str,
    ) -> list[RelationshipAssertion]:
        return [
            record
            for path in sorted(
                self._collection("relationship-assertions").glob("*.json")
            )
            if (record := self._read(path, RelationshipAssertion)).subject == subject
            and record.domain == domain
        ]
