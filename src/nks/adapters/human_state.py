"""Filesystem persistence for temporal human-state records and model feedback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from nks.domain.human_state import (
    HumanStateObservation,
    HumanStateTransition,
    ModelFeedbackPackage,
    ModelFeedbackReceipt,
    ModelIngestionPolicy,
)

T = TypeVar("T", bound=BaseModel)


class JsonHumanStateRepository:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _collection(self, name: str) -> Path:
        path = self._root / "records" / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _write(path: Path, record: BaseModel) -> None:
        serialized = record.model_dump_json(indent=2)
        if path.exists() and path.read_text(encoding="utf-8") == serialized:
            return
        path.write_text(serialized + "\n", encoding="utf-8")

    @staticmethod
    def _read(path: Path, model: type[T]) -> T | None:
        if not path.exists():
            return None
        return model.model_validate_json(path.read_text(encoding="utf-8"))

    def save_observation(self, record: HumanStateObservation) -> HumanStateObservation:
        self._write(self._collection("human-observations") / f"{record.observation_id}.json", record)
        return record

    def get_observation(self, observation_id: str) -> HumanStateObservation | None:
        return self._read(
            self._collection("human-observations") / f"{observation_id}.json",
            HumanStateObservation,
        )

    def list_observations(self, subject_id: str, domain: str) -> list[HumanStateObservation]:
        result = []
        for path in sorted(self._collection("human-observations").glob("*.json")):
            record = HumanStateObservation.model_validate_json(path.read_text(encoding="utf-8"))
            if record.subject_id == subject_id and record.domain == domain:
                result.append(record)
        return sorted(result, key=lambda item: (item.effective_from, item.observed_at))

    def save_transition(self, record: HumanStateTransition) -> HumanStateTransition:
        self._write(self._collection("human-transitions") / f"{record.transition_id}.json", record)
        return record

    def list_transitions(self, subject_id: str, domain: str) -> list[HumanStateTransition]:
        result = []
        for path in sorted(self._collection("human-transitions").glob("*.json")):
            record = HumanStateTransition.model_validate_json(path.read_text(encoding="utf-8"))
            if record.subject_id == subject_id and record.domain == domain:
                result.append(record)
        return sorted(result, key=lambda item: item.detected_at)

    def save_policy(self, record: ModelIngestionPolicy) -> ModelIngestionPolicy:
        self._write(self._collection("model-ingestion-policies") / f"{record.policy_id}.json", record)
        return record

    def get_policy(self, policy_id: str) -> ModelIngestionPolicy | None:
        return self._read(
            self._collection("model-ingestion-policies") / f"{policy_id}.json",
            ModelIngestionPolicy,
        )

    def save_feedback(self, package: ModelFeedbackPackage, receipt: ModelFeedbackReceipt) -> None:
        output = self._root / "generated" / "model-feedback" / receipt.receipt_id
        output.mkdir(parents=True, exist_ok=True)
        (output / "payload.json").write_text(package.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (output / "receipt.json").write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")

    def save_feedback_manifest(self, receipt: ModelFeedbackReceipt) -> None:
        path = self._collection("model-feedback-receipts") / f"{receipt.receipt_id}.json"
        self._write(path, receipt)
