from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from nks.adapters.concurrent_evidence import (
    ConcurrentEvidenceConflict,
    ConcurrentEvidenceKind,
    ConcurrentEvidenceRecord,
    GitHubConcurrentEvidenceStore,
    JsonConcurrentEvidenceStore,
    prove_concurrent_adapter_parity,
    reconstruct_concurrent_evidence,
)


@dataclass
class FakeGitHubContentsClient:
    files: dict[str, str] = field(default_factory=dict)
    fail_next_create: bool = False

    def read_file(self, path: str) -> str | None:
        return self.files.get(path)

    def create_file(self, path: str, content: str) -> None:
        if self.fail_next_create:
            self.fail_next_create = False
            raise OSError("synthetic GitHub adapter interruption")
        if path in self.files:
            raise RuntimeError("GitHub create_file cannot replace existing content")
        self.files[path] = content

    def list_files(self, prefix: str) -> list[str]:
        normalized = prefix.rstrip("/") + "/"
        return sorted(path for path in self.files if path.startswith(normalized))


def _records() -> list[ConcurrentEvidenceRecord]:
    return [
        ConcurrentEvidenceRecord.create(
            record_id="INTENT-1",
            key="KEY-1",
            sequence=1,
            kind=ConcurrentEvidenceKind.INTENT,
            payload={"expected_version": 0, "payload_sha256": "sha256:" + "1" * 64},
        ),
        ConcurrentEvidenceRecord.create(
            record_id="EFFECT-1",
            key="KEY-1",
            sequence=1,
            kind=ConcurrentEvidenceKind.EFFECT,
            payload={"version": 1, "value_sha256": "sha256:" + "2" * 64},
        ),
        ConcurrentEvidenceRecord.create(
            record_id="RECEIPT-1",
            key="KEY-1",
            sequence=1,
            kind=ConcurrentEvidenceKind.RECEIPT,
            payload={"state": "COMMITTED", "effect_sha256": "sha256:" + "2" * 64},
        ),
    ]


def test_filesystem_and_github_content_adapters_have_exact_parity(tmp_path) -> None:
    filesystem = JsonConcurrentEvidenceStore(tmp_path)
    github = GitHubConcurrentEvidenceStore(FakeGitHubContentsClient())

    result = prove_concurrent_adapter_parity(
        filesystem,
        github,
        _records(),
        key="KEY-1",
    )

    assert result.equivalent is True
    assert result.left_sha256 == result.right_sha256
    assert result.left_reconstruction_sha256 == result.right_reconstruction_sha256
    assert result.capabilities == [
        "append",
        "conflict-denial",
        "exact-retry",
        "get",
        "list",
        "reconstruct",
    ]
    assert filesystem.get("RECEIPT-1") == github.get("RECEIPT-1")


def test_both_adapters_reject_divergent_immutable_identity(tmp_path) -> None:
    original = _records()[0]
    conflict = ConcurrentEvidenceRecord.create(
        record_id=original.record_id,
        key=original.key,
        sequence=original.sequence,
        kind=original.kind,
        payload={"expected_version": 99, "payload_sha256": "sha256:" + "9" * 64},
    )
    stores = [
        JsonConcurrentEvidenceStore(tmp_path),
        GitHubConcurrentEvidenceStore(FakeGitHubContentsClient()),
    ]

    for store in stores:
        store.append(original)
        with pytest.raises(ConcurrentEvidenceConflict, match="immutable concurrency evidence"):
            store.append(conflict)
        assert store.get(original.record_id) == original


def test_github_adapter_interruption_recovers_by_exact_retry_without_partial_record() -> None:
    client = FakeGitHubContentsClient(fail_next_create=True)
    store = GitHubConcurrentEvidenceStore(client)
    record = _records()[0]

    with pytest.raises(OSError, match="adapter interruption"):
        store.append(record)
    assert store.get(record.record_id) is None

    store.append(record)
    store.append(record)
    assert store.get(record.record_id) == record
    assert len(store.list_records()) == 1


def test_reconstruction_detects_missing_receipt_on_both_adapters(tmp_path) -> None:
    stores = [
        JsonConcurrentEvidenceStore(tmp_path),
        GitHubConcurrentEvidenceStore(FakeGitHubContentsClient()),
    ]
    incomplete = _records()[:2]

    for store in stores:
        for record in incomplete:
            store.append(record)
        reconstruction = reconstruct_concurrent_evidence(store, key="KEY-1")
        assert reconstruction.intent_count == 1
        assert reconstruction.effect_count == 1
        assert reconstruction.receipt_count == 0
        assert reconstruction.complete is False


def test_record_tamper_and_production_relabel_fail_closed() -> None:
    record = _records()[0]
    with pytest.raises(ValueError, match="record hash is invalid"):
        ConcurrentEvidenceRecord.model_validate(
            record.model_dump(mode="python") | {"record_sha256": "sha256:" + "0" * 64}
        )
    payload = record.model_dump(mode="python")
    payload["execution_context"] = "PRODUCTION"
    with pytest.raises(ValueError, match="TEST-only"):
        ConcurrentEvidenceRecord.model_validate(payload)
