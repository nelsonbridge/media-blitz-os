"""Concrete GitHub contents client built on an injected transport.

The transport may be implemented by the GitHub REST API, an SDK, a connector,
or a test double. Network and authentication concerns remain outside the domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class GitHubPersistenceError(RuntimeError):
    """Base persistence error."""


class GitHubNotFoundError(GitHubPersistenceError):
    pass


class GitHubConflictError(GitHubPersistenceError):
    pass


class GitHubPermissionError(GitHubPersistenceError):
    pass


class GitHubRetryableError(GitHubPersistenceError):
    pass


@dataclass(frozen=True)
class GitHubFileSnapshot:
    path: str
    content: str
    version: str


class GitHubContentsTransport(Protocol):
    def get(self, path: str) -> GitHubFileSnapshot | None: ...

    def create(self, path: str, content: str, message: str) -> GitHubFileSnapshot: ...

    def update(
        self,
        path: str,
        content: str,
        message: str,
        expected_version: str,
    ) -> GitHubFileSnapshot: ...

    def list(self, prefix: str) -> list[str]: ...


class GitHubContentsClient:
    """Implements the minimal GitHubContentClient contract.

    Reads capture platform version metadata internally. Writes use optimistic
    concurrency when updating existing files, while callers continue working
    only with platform-neutral text records.
    """

    def __init__(self, transport: GitHubContentsTransport) -> None:
        self._transport = transport
        self._versions: dict[str, str] = {}

    @staticmethod
    def _validate_path(path: str) -> str:
        if not path or path.startswith("/"):
            raise ValueError("path must be a relative repository path")
        candidate = Path(path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("path must be a relative repository path")
        return path

    def read_text(self, path: str) -> str | None:
        normalized = self._validate_path(path)
        try:
            snapshot = self._transport.get(normalized)
        except PermissionError as exc:
            raise GitHubPermissionError(path) from exc
        except TimeoutError as exc:
            raise GitHubRetryableError(path) from exc
        if snapshot is None:
            self._versions.pop(normalized, None)
            return None
        self._versions[normalized] = snapshot.version
        return snapshot.content

    def write_text(self, path: str, content: str, message: str) -> None:
        normalized = self._validate_path(path)
        try:
            version = self._versions.get(normalized)
            if version is None:
                current = self._transport.get(normalized)
                if current is None:
                    created = self._transport.create(normalized, content, message)
                    self._versions[normalized] = created.version
                    return
                version = current.version
                self._versions[normalized] = version

            updated = self._transport.update(
                normalized,
                content,
                message,
                expected_version=version,
            )
            self._versions[normalized] = updated.version
        except FileExistsError as exc:
            raise GitHubConflictError(path) from exc
        except PermissionError as exc:
            raise GitHubPermissionError(path) from exc
        except TimeoutError as exc:
            raise GitHubRetryableError(path) from exc
        except KeyError as exc:
            raise GitHubNotFoundError(path) from exc

    def list_paths(self, prefix: str) -> list[str]:
        normalized = self._validate_path(prefix)
        try:
            return sorted(self._transport.list(normalized))
        except PermissionError as exc:
            raise GitHubPermissionError(prefix) from exc
        except TimeoutError as exc:
            raise GitHubRetryableError(prefix) from exc
