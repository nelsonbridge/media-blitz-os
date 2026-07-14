"""Append-only persistence for Enki-native model-use packages and effects."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from nks.enki.model_use_contracts import (
    DownstreamEffectReceipt,
    EnkiModelUsePackage,
    ModelUseRevocation,
)


class EnkiModelUseRecordConflictError(RuntimeError):
    """Raised when an immutable model-use record id changes content."""


class JsonEnkiModelUseRepository:
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
            raise EnkiModelUseRecordConflictError(
                f"immutable {collection} id already exists with different content: "
                f"{record_id}"
            )
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _read(path: Path, record_type):
        return record_type.model_validate_json(path.read_text(encoding="utf-8"))

    def append_package(self, package: EnkiModelUsePackage) -> None:
        self._append("enki-model-use-packages", package.package_id, package)

    def get_package(self, package_id: str) -> EnkiModelUsePackage | None:
        path = self._path("enki-model-use-packages", package_id)
        if not path.exists():
            return None
        return self._read(path, EnkiModelUsePackage)

    def append_effect(self, effect: DownstreamEffectReceipt) -> None:
        self._append("enki-model-use-effects", effect.effect_id, effect)

    def get_effect(self, effect_id: str) -> DownstreamEffectReceipt | None:
        path = self._path("enki-model-use-effects", effect_id)
        if not path.exists():
            return None
        return self._read(path, DownstreamEffectReceipt)

    def append_revocation(self, revocation: ModelUseRevocation) -> None:
        existing = self.get_revocation(revocation.package_id)
        if existing is not None:
            if existing == revocation:
                return
            raise EnkiModelUseRecordConflictError(
                "a different revocation already exists for package: "
                f"{revocation.package_id}"
            )
        self._append(
            "enki-model-use-revocations",
            revocation.revocation_id,
            revocation,
        )

    def get_revocation(self, package_id: str) -> ModelUseRevocation | None:
        for path in sorted(
            self._collection("enki-model-use-revocations").glob("*.json")
        ):
            record = self._read(path, ModelUseRevocation)
            if record.package_id == package_id:
                return record
        return None
