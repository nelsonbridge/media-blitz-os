"""Append-only persistence and state lookup for governed Enki transitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from nks.adapters.enki_state import JsonEnkiStateRepository
from nks.application.governed_transactions import canonical_sha256
from nks.enki.transitions import StateSnapshot, TransitionRecord

RecordT = TypeVar("RecordT", bound=BaseModel)


class EnkiTransitionRecordConflictError(RuntimeError):
    """Raised when an immutable transition or state-snapshot id changes content."""


class JsonEnkiTransitionRepository:
    """Persist transition records and their resulting state snapshots append-only."""

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root
        self._state = JsonEnkiStateRepository(repository_root)

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
            raise EnkiTransitionRecordConflictError(
                f"immutable {collection} id already exists with different content: "
                f"{record_id}"
            )
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _read(path: Path, record_type: type[RecordT]) -> RecordT:
        return record_type.model_validate_json(path.read_text(encoding="utf-8"))

    def get_transition(self, transition_id: str) -> TransitionRecord | None:
        path = self._path("enki-transitions", transition_id)
        if not path.exists():
            return None
        return self._read(path, TransitionRecord)

    def list_transitions(self, subject, domain: str) -> list[TransitionRecord]:
        return [
            record
            for path in sorted(self._collection("enki-transitions").glob("*.json"))
            if (record := self._read(path, TransitionRecord)).subject == subject
            and record.domain == domain
        ]

    def append_transition(self, transition: TransitionRecord) -> None:
        self._append(
            "enki-transitions",
            transition.transition_id,
            transition,
        )
        for snapshot in transition.to_states:
            self._append("enki-state-snapshots", snapshot.state_id, snapshot)

    def append_seed_snapshot(self, snapshot: StateSnapshot) -> None:
        """Register a composite or externally assembled immutable seed state."""

        self._append("enki-state-snapshots", snapshot.state_id, snapshot)

    def get_snapshot(self, state_id: str) -> StateSnapshot | None:
        snapshot_path = self._path("enki-state-snapshots", state_id)
        if snapshot_path.exists():
            return self._read(snapshot_path, StateSnapshot)

        observation = self._state.get_observation(state_id)
        if observation is not None:
            return StateSnapshot(
                state_id=observation.observation_id,
                subject=observation.subject,
                domain=observation.domain,
                content_sha256=canonical_sha256(observation),
                observation_ids=[observation.observation_id],
                relationship_ids=[],
                context=observation.context,
                temporal_status=observation.temporal_status.value,
                metadata={"source_record_type": "OBSERVATION"},
            )
        relationship = self._state.get_relationship(state_id)
        if relationship is not None:
            return StateSnapshot(
                state_id=relationship.relationship_id,
                subject=relationship.subject,
                domain=relationship.domain,
                content_sha256=canonical_sha256(relationship),
                observation_ids=[],
                relationship_ids=[relationship.relationship_id],
                context=relationship.context,
                temporal_status="CURRENT",
                metadata={"source_record_type": "RELATIONSHIP"},
            )
        return None
