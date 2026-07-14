from __future__ import annotations

from datetime import datetime, timezone

import pytest

from nks.adapters.forensic_evidence import (
    GitHubForensicEvidenceStore,
    JsonForensicEvidenceStore,
    UnsupportedAdapterOperation,
)
from nks.application.adapter_parity import prove_adapter_parity
from nks.application.forensic_reconstruction import ForensicRecord
from nks.governance.approvals import ExecutionContext


class _FakeGitHubContentsClient:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def read_file(self, path: str) -> str | None:
        return self.files.get(path)

    def create_file(self, path: str, content: str) -> None:
        if path in self.files:
            raise RuntimeError("fake GitHub create cannot overwrite")
        self.files[path] = content

    def list_files(self, prefix: str) -> list[str]:
        return sorted(path for path in self.files if path.startswith(prefix + "/"))


def _record(record_id: str) -> ForensicRecord:
    return ForensicRecord.create(
        record_id=record_id,
        record_type="receipt",
        operation_family="transition",
        operation_id="OP-1",
        transaction_id="TX-1",
        execution_context=ExecutionContext.TEST,
        authority_class="HUMAN_ORIGIN_AUTHORITY",
        payload={"record_id": record_id},
        recorded_at=datetime(2026, 7, 14, 16, 0, tzinfo=timezone.utc),
    )


def test_filesystem_and_github_adapters_are_equivalent_for_declared_surface(tmp_path) -> None:
    filesystem = JsonForensicEvidenceStore(tmp_path)
    github = GitHubForensicEvidenceStore(_FakeGitHubContentsClient())
    result = prove_adapter_parity(filesystem, github, [_record("R-1"), _record("R-2")])
    assert result.equivalent is True
    assert result.capabilities == ["append", "get", "list"]
    assert result.left_sha256 == result.right_sha256


@pytest.mark.parametrize("operation", ["delete", "replace"])
def test_unsupported_mutation_is_explicitly_denied_by_both_adapters(tmp_path, operation: str) -> None:
    record = _record("R-1")
    stores = [
        JsonForensicEvidenceStore(tmp_path),
        GitHubForensicEvidenceStore(_FakeGitHubContentsClient()),
    ]
    for store in stores:
        store.append(record)
        with pytest.raises(UnsupportedAdapterOperation):
            getattr(store, operation)(record.record_id if operation == "delete" else record)
