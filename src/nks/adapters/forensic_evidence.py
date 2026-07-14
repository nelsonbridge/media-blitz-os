"""Append-only filesystem and GitHub-content adapters for portable Enki evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from nks.application.forensic_reconstruction import ForensicRecord


class ForensicEvidenceConflictError(RuntimeError):
    pass


class UnsupportedAdapterOperation(RuntimeError):
    pass


SHARED_CAPABILITIES = frozenset({"append", "get", "list"})


class JsonForensicEvidenceStore:
    capabilities = SHARED_CAPABILITIES

    def __init__(self, root: Path) -> None:
        self._directory = root / "forensic-evidence"
        self._directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _serialize(record: ForensicRecord) -> str:
        return json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"

    def append(self, record: ForensicRecord) -> None:
        path = self._directory / f"{record.record_id}.json"
        content = self._serialize(record)
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return
            raise ForensicEvidenceConflictError(
                f"immutable forensic record already exists: {record.record_id}"
            )
        path.write_text(content, encoding="utf-8")

    def get(self, record_id: str) -> ForensicRecord | None:
        path = self._directory / f"{record_id}.json"
        if not path.exists():
            return None
        return ForensicRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_records(self) -> list[ForensicRecord]:
        return [
            ForensicRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._directory.glob("*.json"))
        ]

    def delete(self, record_id: str) -> None:
        raise UnsupportedAdapterOperation("forensic evidence is append-only")

    def replace(self, record: ForensicRecord) -> None:
        raise UnsupportedAdapterOperation("forensic evidence is immutable")


class GitHubContentsClient(Protocol):
    def read_file(self, path: str) -> str | None: ...

    def create_file(self, path: str, content: str) -> None: ...

    def list_files(self, prefix: str) -> list[str]: ...


class GitHubForensicEvidenceStore:
    """GitHub adapter limited to the same append/get/list contract as filesystem."""

    capabilities = SHARED_CAPABILITIES

    def __init__(self, client: GitHubContentsClient, prefix: str = "forensic-evidence") -> None:
        self._client = client
        self._prefix = prefix.rstrip("/")

    @staticmethod
    def _serialize(record: ForensicRecord) -> str:
        return json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"

    def _path(self, record_id: str) -> str:
        return f"{self._prefix}/{record_id}.json"

    def append(self, record: ForensicRecord) -> None:
        path = self._path(record.record_id)
        content = self._serialize(record)
        existing = self._client.read_file(path)
        if existing is not None:
            if existing == content:
                return
            raise ForensicEvidenceConflictError(
                f"immutable forensic record already exists: {record.record_id}"
            )
        self._client.create_file(path, content)

    def get(self, record_id: str) -> ForensicRecord | None:
        content = self._client.read_file(self._path(record_id))
        if content is None:
            return None
        return ForensicRecord.model_validate_json(content)

    def list_records(self) -> list[ForensicRecord]:
        return [
            ForensicRecord.model_validate_json(content)
            for path in sorted(self._client.list_files(self._prefix))
            if (content := self._client.read_file(path)) is not None
        ]

    def delete(self, record_id: str) -> None:
        raise UnsupportedAdapterOperation("GitHub forensic evidence is append-only")

    def replace(self, record: ForensicRecord) -> None:
        raise UnsupportedAdapterOperation("GitHub forensic evidence is immutable")
