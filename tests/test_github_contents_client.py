import pytest

from nks.adapters.github_client import (
    GitHubConflictError,
    GitHubContentsClient,
    GitHubFileSnapshot,
    GitHubPermissionError,
    GitHubRetryableError,
)


class FakeTransport:
    def __init__(self):
        self.files: dict[str, GitHubFileSnapshot] = {}
        self.fail_with: Exception | None = None

    def _raise_if_needed(self):
        if self.fail_with is not None:
            exc = self.fail_with
            self.fail_with = None
            raise exc

    def get(self, path: str) -> GitHubFileSnapshot | None:
        self._raise_if_needed()
        return self.files.get(path)

    def create(self, path: str, content: str, message: str) -> GitHubFileSnapshot:
        self._raise_if_needed()
        if path in self.files:
            raise FileExistsError(path)
        snapshot = GitHubFileSnapshot(path, content, "v1")
        self.files[path] = snapshot
        return snapshot

    def update(
        self,
        path: str,
        content: str,
        message: str,
        expected_version: str,
    ) -> GitHubFileSnapshot:
        self._raise_if_needed()
        current = self.files.get(path)
        if current is None:
            raise KeyError(path)
        if current.version != expected_version:
            raise FileExistsError(path)
        next_version = f"v{int(current.version[1:]) + 1}"
        snapshot = GitHubFileSnapshot(path, content, next_version)
        self.files[path] = snapshot
        return snapshot

    def list(self, prefix: str) -> list[str]:
        self._raise_if_needed()
        return [path for path in self.files if path.startswith(prefix)]


def test_create_read_update_and_list():
    transport = FakeTransport()
    client = GitHubContentsClient(transport)

    client.write_text("records/a.json", "one", "create")
    assert client.read_text("records/a.json") == "one"
    client.write_text("records/a.json", "two", "update")

    assert client.read_text("records/a.json") == "two"
    assert client.list_paths("records/") == ["records/a.json"]


def test_stale_version_is_classified_as_conflict():
    transport = FakeTransport()
    client = GitHubContentsClient(transport)
    client.write_text("records/a.json", "one", "create")
    client.read_text("records/a.json")
    transport.files["records/a.json"] = GitHubFileSnapshot(
        "records/a.json", "external", "v2"
    )

    with pytest.raises(GitHubConflictError):
        client.write_text("records/a.json", "local", "update")


def test_permission_and_timeout_are_classified():
    transport = FakeTransport()
    client = GitHubContentsClient(transport)

    transport.fail_with = PermissionError("denied")
    with pytest.raises(GitHubPermissionError):
        client.read_text("records/a.json")

    transport.fail_with = TimeoutError("temporary")
    with pytest.raises(GitHubRetryableError):
        client.list_paths("records/")
