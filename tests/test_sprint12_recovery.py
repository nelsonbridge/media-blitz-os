import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from nks.application.reconstruction import PersistedKnowledgeHistory, reconstruct_governed_state
from nks.application.sprint12_recovery import (
    InterruptedOperationError,
    export_portable_state_recoverable,
    import_portable_state_recoverable,
    read_recovery_journal,
    restore_and_reconstruct_recoverable,
    validate_portable_package,
)


def _history_payload() -> dict:
    return {
        "sequence_contract": "ordered-only",
        "transitions": [
            {
                "transition_id": "tr-1",
                "transition_index": 10,
                "knowledge_id": "K-001",
                "from_state_id": None,
                "to_state_id": "S-001",
                "authoritative": False,
                "state_payload": {"status": "historical"},
                "provenance": {"source": "SRC-001"},
                "evidence_associations": [
                    {"evidence_id": "EV-001", "relationship": "supports", "metadata": {}}
                ],
                "lineage": {
                    "parent_state_id": None,
                    "supersedes_state_id": None,
                    "branch_id": "main",
                },
            },
            {
                "transition_id": "tr-2",
                "transition_index": 20,
                "knowledge_id": "K-001",
                "from_state_id": "S-001",
                "to_state_id": "S-002",
                "authoritative": True,
                "state_payload": {"status": "current"},
                "provenance": {"source": "SRC-002"},
                "evidence_associations": [
                    {"evidence_id": "EV-002", "relationship": "refines", "metadata": {}}
                ],
                "lineage": {
                    "parent_state_id": "S-001",
                    "supersedes_state_id": "S-001",
                    "branch_id": "main",
                },
            },
        ],
    }


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    (source / "records" / "history").mkdir(parents=True)
    (source / "records" / "history" / "transitions.json").write_text(
        json.dumps(_history_payload(), indent=2), encoding="utf-8"
    )
    (source / "records" / "evidence").mkdir(parents=True)
    for evidence_id in ("EV-001", "EV-002"):
        (source / "records" / "evidence" / f"{evidence_id}.json").write_text(
            json.dumps({"evidence_id": evidence_id}), encoding="utf-8"
        )
    (source / "records" / "assets").mkdir(parents=True)
    (source / "records" / "assets" / "A-001.json").write_text(
        json.dumps(
            {
                "asset_id": "A-001",
                "binary_asset_references": [
                    {"asset_id": "BIN-001", "path": "assets/rendered/figure-1.png"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (source / "events").mkdir(parents=True)
    (source / "events" / "EVT-001.json").write_text(
        json.dumps({"event_id": "EVT-001", "type": "transition-recorded"}), encoding="utf-8"
    )
    return source


def _manifest(archive: Path) -> dict:
    with zipfile.ZipFile(archive, "r") as bundle:
        return json.loads(bundle.read("manifest.json"))


def _rewrite_manifest(archive: Path, mutate) -> None:
    with zipfile.ZipFile(archive, "r") as bundle:
        entries = {name: bundle.read(name) for name in bundle.namelist() if name != "manifest.json"}
        manifest = json.loads(bundle.read("manifest.json"))
    mutate(manifest)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))
        for name, data in entries.items():
            bundle.writestr(name, data)


def _rewrite_entry(archive: Path, entry_name: str, data: bytes, *, update_manifest_hash: bool) -> None:
    with zipfile.ZipFile(archive, "r") as bundle:
        entries = {name: bundle.read(name) for name in bundle.namelist() if name != "manifest.json"}
        manifest = json.loads(bundle.read("manifest.json"))
    entries[entry_name] = data
    if update_manifest_hash:
        for item in manifest["files"]:
            if item["path"] == entry_name:
                item["sha256"] = hashlib.sha256(data).hexdigest()
                item["size"] = len(data)
        if manifest.get("governed_reconstruction", {}).get("history_path") == entry_name:
            manifest["governed_reconstruction"]["history_sha256"] = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))
        for name, content in entries.items():
            bundle.writestr(name, content)


def test_ep12_07_export_retry_is_idempotent_and_scope_is_deterministic(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"

    first = export_portable_state_recoverable(source, archive)
    first_manifest = _manifest(archive)
    second = export_portable_state_recoverable(source, archive)
    second_manifest = _manifest(archive)

    assert first.manifest_sha256 == second.manifest_sha256
    assert first_manifest == second_manifest
    assert first_manifest["portable_scope"]["event_paths"] == ["events/EVT-001.json"]
    assert first_manifest["portable_scope"]["binary_asset_references"] == [
        {
            "subject_path": "records/assets/A-001.json",
            "reference": {"asset_id": "BIN-001", "path": "assets/rendered/figure-1.png"},
        }
    ]


def test_ep12_07_import_retry_does_not_duplicate_history_or_evidence(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    destination = tmp_path / "restored"
    export_portable_state_recoverable(source, archive)

    import_portable_state_recoverable(archive, destination)
    before = (destination / "records" / "history" / "transitions.json").read_bytes()
    import_portable_state_recoverable(archive, destination, replace=True)
    after = (destination / "records" / "history" / "transitions.json").read_bytes()

    assert before == after
    payload = json.loads(after)
    assert [item["transition_id"] for item in payload["transitions"]] == ["tr-1", "tr-2"]
    assert len(payload["transitions"][0]["evidence_associations"]) == 1
    assert len(payload["transitions"][1]["evidence_associations"]) == 1


def test_ep12_08_rollback_restores_original_destination_after_commit_interruption(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    destination = tmp_path / "restored"
    journal = tmp_path / "recovery.jsonl"
    destination.mkdir()
    sentinel = destination / "sentinel.txt"
    sentinel.write_text("original-state", encoding="utf-8")
    export_portable_state_recoverable(source, archive)

    with pytest.raises(InterruptedOperationError):
        import_portable_state_recoverable(
            archive,
            destination,
            replace=True,
            journal_path=journal,
            operation_id="rollback-test",
            failpoint="after_destination_backup",
        )

    assert sentinel.read_text(encoding="utf-8") == "original-state"
    assert not (destination / "records").exists()
    events = read_recovery_journal(journal)
    assert events[-1]["phase"] == "rollback"
    assert events[-1]["outcome"] == "rolled_back"


def test_ep12_09_interrupted_export_is_explicit_and_retry_converges(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    journal = tmp_path / "recovery.jsonl"

    with pytest.raises(InterruptedOperationError):
        export_portable_state_recoverable(
            source,
            archive,
            journal_path=journal,
            operation_id="export-interruption",
            failpoint="after_export_stage",
        )

    assert not archive.exists()
    assert archive.with_name("portable.zip.partial").exists()
    result = export_portable_state_recoverable(
        source, archive, journal_path=journal, operation_id="export-interruption"
    )
    assert archive.exists()
    assert validate_portable_package(archive)["format"] == "nks-portable-state"
    assert len(result.manifest_sha256) == 64
    events = read_recovery_journal(journal)
    assert any(event["outcome"] == "recoverable_failure" for event in events)
    assert any(event["phase"] == "recovery" for event in events)


def test_ep12_09_interrupted_import_leaves_destination_untouched_and_retries(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    destination = tmp_path / "restored"
    journal = tmp_path / "recovery.jsonl"
    destination.mkdir()
    (destination / "sentinel.txt").write_text("untouched", encoding="utf-8")
    export_portable_state_recoverable(source, archive)

    with pytest.raises(InterruptedOperationError):
        import_portable_state_recoverable(
            archive,
            destination,
            replace=True,
            journal_path=journal,
            operation_id="import-interruption",
            failpoint="after_import_stage",
        )

    assert (destination / "sentinel.txt").read_text(encoding="utf-8") == "untouched"
    import_portable_state_recoverable(
        archive,
        destination,
        replace=True,
        journal_path=journal,
        operation_id="import-interruption",
    )
    assert (destination / "records" / "history" / "transitions.json").exists()
    assert not (destination / "sentinel.txt").exists()


def test_ep12_10_rejects_unsupported_contract_version(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    export_portable_state_recoverable(source, archive)
    _rewrite_manifest(
        archive,
        lambda manifest: manifest["schema"].update({"export_contract_version": "future-v99"}),
    )

    with pytest.raises(ValueError, match="unsupported export contract"):
        validate_portable_package(archive)


def test_ep12_10_rejects_missing_manifest_file(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    export_portable_state_recoverable(source, archive)
    _rewrite_manifest(
        archive,
        lambda manifest: manifest["files"].append(
            {"path": "records/missing.json", "sha256": "0" * 64, "size": 1}
        ),
    )

    with pytest.raises(ValueError, match="missing required package file"):
        validate_portable_package(archive)


def test_ep12_10_rejects_checksum_corruption(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    export_portable_state_recoverable(source, archive)
    _rewrite_entry(archive, "records/evidence/EV-001.json", b"tampered", update_manifest_hash=False)

    with pytest.raises(ValueError, match="checksum mismatch"):
        validate_portable_package(archive)


def test_ep12_10_rejects_missing_provenance_even_with_valid_checksums(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    export_portable_state_recoverable(source, archive)
    history = _history_payload()
    history["transitions"][1]["provenance"] = {}
    data = json.dumps(history).encode("utf-8")
    _rewrite_entry(
        archive,
        "records/history/transitions.json",
        data,
        update_manifest_hash=True,
    )

    with pytest.raises(ValueError, match="missing provenance"):
        validate_portable_package(archive)


def test_ep12_10_rejects_broken_lineage_even_with_valid_checksums(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    export_portable_state_recoverable(source, archive)
    history = _history_payload()
    history["transitions"][1]["lineage"]["parent_state_id"] = "S-WRONG"
    data = json.dumps(history).encode("utf-8")
    _rewrite_entry(
        archive,
        "records/history/transitions.json",
        data,
        update_manifest_hash=True,
    )

    with pytest.raises(ValueError, match="broken lineage parent"):
        validate_portable_package(archive)


def test_ep12_10_rejects_multiple_authoritative_states(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    export_portable_state_recoverable(source, archive)
    history = _history_payload()
    history["transitions"][0]["authoritative"] = True
    data = json.dumps(history).encode("utf-8")
    _rewrite_entry(
        archive,
        "records/history/transitions.json",
        data,
        update_manifest_hash=True,
    )

    with pytest.raises(ValueError, match="multiple authoritative states"):
        validate_portable_package(archive)


def test_ep12_11_full_round_trip_retry_interruption_rollback_and_reconstruction(tmp_path: Path):
    source = _source(tmp_path)
    archive = tmp_path / "portable.zip"
    destination = tmp_path / "restored"
    journal = tmp_path / "recovery.jsonl"

    original_history = PersistedKnowledgeHistory.model_validate(_history_payload())
    original = reconstruct_governed_state(original_history)

    with pytest.raises(InterruptedOperationError):
        export_portable_state_recoverable(
            source,
            archive,
            journal_path=journal,
            operation_id="e2e-export",
            failpoint="after_export_stage",
        )
    export_portable_state_recoverable(
        source, archive, journal_path=journal, operation_id="e2e-export"
    )

    destination.mkdir()
    (destination / "preexisting.txt").write_text("rollback-me", encoding="utf-8")
    with pytest.raises(InterruptedOperationError):
        import_portable_state_recoverable(
            archive,
            destination,
            replace=True,
            journal_path=journal,
            operation_id="e2e-import",
            failpoint="after_destination_backup",
        )
    assert (destination / "preexisting.txt").read_text(encoding="utf-8") == "rollback-me"

    restored = restore_and_reconstruct_recoverable(
        archive,
        destination,
        replace=True,
        journal_path=journal,
        operation_id="e2e-restore",
    )
    restored_again = restore_and_reconstruct_recoverable(
        archive,
        destination,
        replace=True,
        journal_path=journal,
        operation_id="e2e-restore-retry",
    )

    assert restored.canonical_fingerprint() == original.canonical_fingerprint()
    assert restored_again.canonical_fingerprint() == original.canonical_fingerprint()
    assert restored.semantic_fingerprint() == original.semantic_fingerprint()
    assert restored.knowledge["K-001"].current_authoritative_state.state_id == "S-002"
    assert [state.state_id for state in restored.knowledge["K-001"].historical_states] == [
        "S-001",
        "S-002",
    ]
    events = read_recovery_journal(journal)
    assert any(event["outcome"] == "rolled_back" for event in events)
    assert any(event["phase"] == "reconstruction" and event["outcome"] == "complete" for event in events)
