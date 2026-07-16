"""Sprint 12 recovery, retry, rollback, and adversarial portability controls.

This module deliberately wraps the existing portable export/import contract rather than
changing historical behavior in-place. It adds transactional staging, append-only recovery
journaling, deterministic portability-scope enrichment, strict package validation, and
failpoints used to prove interruption and rollback behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from nks.application.export_import import (
    ExportResult,
    export_portable_state,
    import_portable_state,
    verify_imported_state,
)
from nks.application.reconstruction import (
    PersistedKnowledgeHistory,
    ReconstructedGovernedState,
    reconstruct_governed_state,
)

SUPPORTED_EXPORT_CONTRACTS = {"nks-portable-state-v1"}
SUPPORTED_RECONSTRUCTION_CONTRACTS = {"nks-governed-history-v1"}
SUPPORTED_SEQUENCE_CONTRACTS = {"ordered-only", "contiguous-index"}

Failpoint = Literal[
    "after_export_stage",
    "after_import_stage",
    "after_destination_backup",
    "before_reconstruction",
]


class RecoveryError(RuntimeError):
    """Base error for recoverable Sprint 12 operations."""


class InterruptedOperationError(RecoveryError):
    """Raised by a deterministic failpoint to simulate an interrupted operation."""


@dataclass(frozen=True)
class RecoveryEvent:
    operation_id: str
    operation: str
    phase: str
    outcome: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "operation_id": self.operation_id,
            "operation": self.operation,
            "phase": self.phase,
            "outcome": self.outcome,
            "detail": self.detail,
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _append_event(journal_path: Path | None, event: RecoveryEvent) -> None:
    if journal_path is None:
        return
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(event.as_dict(), sort_keys=True, separators=(",", ":")) + "\n"
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def read_recovery_journal(journal_path: Path) -> list[dict[str, str]]:
    if not journal_path.exists():
        return []
    return [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines() if line]


def _safe_remove(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _extract_binary_asset_references(payload: Any, *, subject_path: str) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    singular_keys = {"binary_asset_ref", "binary_asset_reference"}
    plural_keys = {"binary_asset_refs", "binary_asset_references"}

    def add(value: Any) -> None:
        if isinstance(value, str) and value:
            references.append({"subject_path": subject_path, "reference": value})
        elif isinstance(value, dict):
            references.append({"subject_path": subject_path, "reference": value})

    for node in _walk_json(payload):
        for key in singular_keys:
            if key in node:
                add(node[key])
        for key in plural_keys:
            values = node.get(key)
            if isinstance(values, list):
                for value in values:
                    add(value)

    return references


def _fixed_zipinfo(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path)
    info.date_time = (1980, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def _enrich_portable_scope(repository_root: Path, archive_path: Path) -> ExportResult:
    """Add event files and binary-asset references to the portable manifest.

    TB-014 requires portable state to account for canonical records, events, schemas,
    and binary asset references. Event records already under ``records/`` remain covered
    by the base exporter; a legacy top-level ``events/`` tree is also included here.
    Binary content is not copied implicitly. Instead, governed references are preserved.
    """

    with zipfile.ZipFile(archive_path, "r") as bundle:
        names = bundle.namelist()
        if "manifest.json" not in names:
            raise ValueError("portable package missing manifest.json")
        manifest = json.loads(bundle.read("manifest.json"))
        entries = {name: bundle.read(name) for name in names if name != "manifest.json"}

    legacy_events = repository_root / "events"
    if legacy_events.exists():
        for path in sorted(item for item in legacy_events.rglob("*") if item.is_file()):
            relative = path.relative_to(repository_root).as_posix()
            entries.setdefault(relative, path.read_bytes())

    file_items: dict[str, dict[str, Any]] = {}
    for item in manifest.get("files", []):
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            file_items[item["path"]] = dict(item)
    for path, data in entries.items():
        file_items[path] = {"path": path, "sha256": _sha256_bytes(data), "size": len(data)}

    binary_references: list[dict[str, Any]] = []
    for path, data in entries.items():
        if not path.endswith(".json"):
            continue
        try:
            payload = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        binary_references.extend(_extract_binary_asset_references(payload, subject_path=path))

    # De-duplicate structurally while retaining deterministic ordering.
    encoded_refs = {
        json.dumps(reference, sort_keys=True, separators=(",", ":")): reference
        for reference in binary_references
    }
    event_paths = sorted(
        path
        for path in entries
        if path.startswith("events/") or path.startswith("records/events/")
    )
    manifest["files"] = [file_items[path] for path in sorted(file_items)]
    manifest["portable_scope"] = {
        "event_paths": event_paths,
        "binary_asset_references": [encoded_refs[key] for key in sorted(encoded_refs)],
    }

    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    rewrite_path = archive_path.with_name(f"{archive_path.name}.rewrite")
    _safe_remove(rewrite_path)
    with zipfile.ZipFile(rewrite_path, "w") as bundle:
        bundle.writestr(_fixed_zipinfo("manifest.json"), manifest_bytes)
        for path in sorted(entries):
            bundle.writestr(_fixed_zipinfo(path), entries[path])
    os.replace(rewrite_path, archive_path)

    return ExportResult(
        archive_path=archive_path,
        file_count=len(manifest["files"]),
        manifest_sha256=_sha256_bytes(manifest_bytes),
    )


def _validate_history_semantics(history: PersistedKnowledgeHistory) -> ReconstructedGovernedState:
    by_knowledge: dict[str, list[Any]] = {}
    for transition in history.transitions:
        if not transition.provenance:
            raise ValueError(f"missing provenance for transition: {transition.transition_id}")
        by_knowledge.setdefault(transition.knowledge_id, []).append(transition)

    for knowledge_id, transitions in by_knowledge.items():
        ordered = sorted(transitions, key=lambda item: (item.transition_index, item.transition_id))
        prior_states: set[str] = set()
        for transition in ordered:
            if transition.lineage.parent_state_id is not None:
                if transition.lineage.parent_state_id != transition.from_state_id:
                    raise ValueError(
                        f"broken lineage parent for {knowledge_id}: {transition.transition_id}"
                    )
            if transition.lineage.supersedes_state_id is not None:
                if transition.lineage.supersedes_state_id not in prior_states:
                    raise ValueError(
                        f"invalid supersedes authority reference for {knowledge_id}: "
                        f"{transition.lineage.supersedes_state_id}"
                    )
            prior_states.add(transition.to_state_id)

    return reconstruct_governed_state(history)


def validate_portable_package(archive_path: Path) -> dict[str, Any]:
    """Fail closed on malformed, corrupt, incomplete, or semantically invalid packages."""

    try:
        bundle = zipfile.ZipFile(archive_path, "r")
    except zipfile.BadZipFile as exc:
        raise ValueError("malformed portable package") from exc

    with bundle:
        names = bundle.namelist()
        if "manifest.json" not in names:
            raise ValueError("portable package missing manifest.json")
        try:
            manifest = json.loads(bundle.read("manifest.json"))
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("invalid portable package manifest") from exc
        if not isinstance(manifest, dict):
            raise ValueError("invalid portable package manifest shape")
        if manifest.get("format") != "nks-portable-state":
            raise ValueError("unsupported portable-state format")
        if manifest.get("version") != 1:
            raise ValueError("unsupported portable-state version")

        schema = manifest.get("schema", {})
        if not isinstance(schema, dict):
            raise ValueError("invalid schema section")
        export_contract = schema.get("export_contract_version")
        reconstruction_contract = schema.get("reconstruction_contract_version")
        sequence_contracts = schema.get("supported_sequence_contracts", [])
        if export_contract is not None and export_contract not in SUPPORTED_EXPORT_CONTRACTS:
            raise ValueError(f"unsupported export contract: {export_contract}")
        if reconstruction_contract is not None and reconstruction_contract not in SUPPORTED_RECONSTRUCTION_CONTRACTS:
            raise ValueError(f"unsupported reconstruction contract: {reconstruction_contract}")
        if sequence_contracts and (
            not isinstance(sequence_contracts, list)
            or not set(sequence_contracts).issubset(SUPPORTED_SEQUENCE_CONTRACTS)
        ):
            raise ValueError("unsupported sequence contract declaration")

        file_items = manifest.get("files")
        if not isinstance(file_items, list):
            raise ValueError("invalid files section")
        seen_paths: set[str] = set()
        for item in file_items:
            if not isinstance(item, dict):
                raise ValueError("invalid file manifest entry")
            path_value = item.get("path")
            digest = item.get("sha256")
            size = item.get("size")
            if not isinstance(path_value, str) or not path_value:
                raise ValueError("invalid file manifest path")
            relative = Path(path_value)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsafe archive path: {relative}")
            if path_value in seen_paths:
                raise ValueError(f"duplicate manifest path: {path_value}")
            seen_paths.add(path_value)
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError(f"invalid checksum declaration: {path_value}")
            if not isinstance(size, int) or size < 0:
                raise ValueError(f"invalid size declaration: {path_value}")
            if path_value not in names:
                raise ValueError(f"missing required package file: {path_value}")
            data = bundle.read(path_value)
            if len(data) != size:
                raise ValueError(f"size mismatch: {path_value}")
            if _sha256_bytes(data) != digest:
                raise ValueError(f"checksum mismatch: {path_value}")

        reconstruction = manifest.get("governed_reconstruction", {})
        if reconstruction and not isinstance(reconstruction, dict):
            raise ValueError("invalid governed reconstruction section")
        history_present = bool(reconstruction.get("history_present", False)) if reconstruction else False
        reconstruction_supported = (
            bool(reconstruction.get("reconstruction_supported", False)) if reconstruction else False
        )
        history_path = (
            reconstruction.get("history_path", "records/history/transitions.json")
            if reconstruction
            else "records/history/transitions.json"
        )
        if reconstruction_supported and not history_present:
            raise ValueError("invalid governed reconstruction declaration")
        if history_present:
            if not isinstance(history_path, str) or history_path not in seen_paths:
                raise ValueError("missing governed history file")
            history_bytes = bundle.read(history_path)
            declared_history_hash = reconstruction.get("history_sha256")
            if declared_history_hash is not None and _sha256_bytes(history_bytes) != declared_history_hash:
                raise ValueError("governed history checksum mismatch")
            try:
                history = PersistedKnowledgeHistory.model_validate_json(history_bytes.decode("utf-8"))
            except Exception as exc:
                raise ValueError("invalid governed history") from exc
            _validate_history_semantics(history)

        evidence = manifest.get("evidence", {"references": [], "unresolved": []})
        if not isinstance(evidence, dict):
            raise ValueError("invalid evidence section")
        if not isinstance(evidence.get("references", []), list):
            raise ValueError("invalid evidence references")
        if not isinstance(evidence.get("unresolved", []), list):
            raise ValueError("invalid unresolved evidence references")

        portable_scope = manifest.get("portable_scope", {"event_paths": [], "binary_asset_references": []})
        if not isinstance(portable_scope, dict):
            raise ValueError("invalid portable scope")
        event_paths = portable_scope.get("event_paths", [])
        binary_references = portable_scope.get("binary_asset_references", [])
        if not isinstance(event_paths, list) or not all(isinstance(path, str) for path in event_paths):
            raise ValueError("invalid event path inventory")
        if not set(event_paths).issubset(seen_paths):
            raise ValueError("portable scope references a missing event file")
        if not isinstance(binary_references, list):
            raise ValueError("invalid binary asset reference inventory")

    return manifest


def export_portable_state_recoverable(
    repository_root: Path,
    archive_path: Path,
    *,
    journal_path: Path | None = None,
    operation_id: str = "s12-export",
    failpoint: Failpoint | None = None,
) -> ExportResult:
    """Stage, validate, and atomically publish a portable export.

    Repeated execution is idempotent with respect to repository state: the destination is
    replaced only by a fully validated package and no canonical record is mutated.
    """

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    partial = archive_path.with_name(f"{archive_path.name}.partial")
    if partial.exists():
        _safe_remove(partial)
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "export", "recovery", "recovered", "removed stale staged export"),
        )

    _append_event(journal_path, RecoveryEvent(operation_id, "export", "start", "started", str(archive_path)))
    try:
        export_portable_state(repository_root, partial)
        result = _enrich_portable_scope(repository_root, partial)
        validate_portable_package(partial)
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "export", "stage", "complete", result.manifest_sha256),
        )
        if failpoint == "after_export_stage":
            _append_event(
                journal_path,
                RecoveryEvent(operation_id, "export", "interruption", "recoverable_failure", "after_export_stage"),
            )
            raise InterruptedOperationError("export interrupted after validated staging")
        os.replace(partial, archive_path)
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "export", "commit", "complete", result.manifest_sha256),
        )
        return ExportResult(archive_path, result.file_count, result.manifest_sha256)
    except InterruptedOperationError:
        raise
    except Exception as exc:
        _safe_remove(partial)
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "export", "rollback", "rolled_back", str(exc)),
        )
        raise


def import_portable_state_recoverable(
    archive_path: Path,
    destination_root: Path,
    *,
    replace: bool = False,
    journal_path: Path | None = None,
    operation_id: str = "s12-import",
    failpoint: Failpoint | None = None,
) -> dict[str, Any]:
    """Validate and stage an import before atomically replacing destination state."""

    manifest = validate_portable_package(archive_path)
    destination_root = destination_root.resolve()
    destination_root.parent.mkdir(parents=True, exist_ok=True)
    stage = destination_root.parent / f".{destination_root.name}.import-partial"
    backup = destination_root.parent / f".{destination_root.name}.rollback"

    if stage.exists():
        _safe_remove(stage)
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "import", "recovery", "recovered", "removed stale staged import"),
        )
    if backup.exists():
        # A prior operation stopped after moving the original destination aside.
        if destination_root.exists():
            _safe_remove(backup)
        else:
            os.replace(backup, destination_root)
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "import", "recovery", "recovered", "reconciled rollback backup"),
        )

    _append_event(journal_path, RecoveryEvent(operation_id, "import", "start", "started", str(archive_path)))
    import_portable_state(archive_path, stage, replace=True)
    verify_imported_state(stage, manifest)
    _append_event(journal_path, RecoveryEvent(operation_id, "import", "stage", "complete", str(stage)))

    if failpoint == "after_import_stage":
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "import", "interruption", "recoverable_failure", "after_import_stage"),
        )
        raise InterruptedOperationError("import interrupted after validated staging")

    destination_had_state = destination_root.exists() and any(destination_root.iterdir())
    if destination_had_state and not replace:
        _safe_remove(stage)
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "import", "rollback", "rolled_back", "destination is not empty"),
        )
        raise FileExistsError(f"destination is not empty: {destination_root}")

    moved_to_backup = False
    try:
        if destination_root.exists():
            if destination_had_state:
                os.replace(destination_root, backup)
                moved_to_backup = True
            else:
                destination_root.rmdir()

        if failpoint == "after_destination_backup":
            raise InterruptedOperationError("import interrupted after destination backup")

        os.replace(stage, destination_root)
        verify_imported_state(destination_root, manifest)
        _safe_remove(backup)
        _append_event(journal_path, RecoveryEvent(operation_id, "import", "commit", "complete", str(destination_root)))
        return manifest
    except Exception as exc:
        _safe_remove(stage)
        if moved_to_backup:
            _safe_remove(destination_root)
            os.replace(backup, destination_root)
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "import", "rollback", "rolled_back", str(exc)),
        )
        raise


def restore_and_reconstruct_recoverable(
    archive_path: Path,
    destination_root: Path,
    *,
    replace: bool = False,
    journal_path: Path | None = None,
    operation_id: str = "s12-restore",
    failpoint: Failpoint | None = None,
) -> ReconstructedGovernedState:
    manifest = import_portable_state_recoverable(
        archive_path,
        destination_root,
        replace=replace,
        journal_path=journal_path,
        operation_id=operation_id,
        failpoint=failpoint if failpoint in {"after_import_stage", "after_destination_backup"} else None,
    )
    reconstruction = manifest.get("governed_reconstruction", {})
    if not reconstruction.get("reconstruction_supported", False):
        raise RecoveryError("portable package does not declare governed reconstruction support")
    history_path = destination_root / reconstruction.get("history_path", "records/history/transitions.json")
    history = PersistedKnowledgeHistory.model_validate_json(history_path.read_text(encoding="utf-8"))
    if failpoint == "before_reconstruction":
        _append_event(
            journal_path,
            RecoveryEvent(operation_id, "reconstruction", "interruption", "recoverable_failure", "before_reconstruction"),
        )
        raise InterruptedOperationError("restoration interrupted before reconstruction")
    reconstructed = _validate_history_semantics(history)
    _append_event(
        journal_path,
        RecoveryEvent(operation_id, "reconstruction", "complete", "complete", reconstructed.canonical_fingerprint()),
    )
    return reconstructed
