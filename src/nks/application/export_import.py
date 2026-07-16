"""Portable export/import for canonical NKS state."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nks.application.reconstruction import PersistedKnowledgeHistory


@dataclass(frozen=True)
class ExportResult:
    archive_path: Path
    file_count: int
    manifest_sha256: str


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_files(repository_root: Path) -> list[Path]:
    included_roots = [
        repository_root / "records",
        repository_root / "schemas",
        repository_root / "contracts",
    ]
    files: list[Path] = []
    for root in included_roots:
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(repository_root).as_posix())


def _walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_json(item)


def _extract_evidence_references(
    repository_root: Path,
    files: list[Path],
    file_hashes: dict[str, str],
) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    existing_paths = set(file_hashes)

    for path in files:
        relative = path.relative_to(repository_root).as_posix()
        if not relative.startswith("records/") or not relative.endswith(".json"):
            continue

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        for node in _walk_json(payload):
            source_ref = node.get("source_location")
            provenance = node.get("provenance") if isinstance(node.get("provenance"), dict) else {}

            if isinstance(node.get("evidence_associations"), list):
                for association in node["evidence_associations"]:
                    if not isinstance(association, dict):
                        continue
                    evidence_id = association.get("evidence_id")
                    if not isinstance(evidence_id, str) or not evidence_id:
                        continue
                    evidence_path = f"records/evidence/{evidence_id}.json"
                    resolved = evidence_path in existing_paths
                    references.append(
                        {
                            "subject_path": relative,
                            "evidence_id": evidence_id,
                            "relationship": association.get("relationship"),
                            "provenance": provenance,
                            "source_ref": source_ref,
                            "evidence_path": evidence_path,
                            "integrity_sha256": file_hashes.get(evidence_path),
                            "status": "resolved" if resolved else "unresolved",
                            "unresolved_reason": None if resolved else "missing_exported_evidence",
                        }
                    )

    # Deterministic serialization order for portability checks.
    return sorted(
        references,
        key=lambda item: (
            item["subject_path"],
            item["evidence_id"],
            str(item.get("relationship")),
            str(item.get("source_ref")),
        ),
    )


def export_portable_state(repository_root: Path, archive_path: Path) -> ExportResult:
    repository_root = repository_root.resolve()
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    files = _canonical_files(repository_root)

    manifest_files: list[dict[str, str | int]] = []
    file_hashes: dict[str, str] = {}
    for path in files:
        relative = path.relative_to(repository_root).as_posix()
        data = path.read_bytes()
        digest = _sha256_bytes(data)
        file_hashes[relative] = digest
        manifest_files.append(
            {
                "path": relative,
                "sha256": digest,
                "size": len(data),
            }
        )

    evidence_references = _extract_evidence_references(repository_root, files, file_hashes)
    unresolved_evidence = [
        {
            "subject_path": item["subject_path"],
            "evidence_id": item["evidence_id"],
            "relationship": item["relationship"],
            "source_ref": item["source_ref"],
            "reason": item["unresolved_reason"],
        }
        for item in evidence_references
        if item["status"] == "unresolved"
    ]

    history_path = "records/history/transitions.json"
    history_present = history_path in file_hashes
    history_sha256 = file_hashes.get(history_path)
    if history_present:
        history_file = repository_root / history_path
        PersistedKnowledgeHistory.model_validate_json(history_file.read_text(encoding="utf-8"))

    manifest = {
        "format": "nks-portable-state",
        "version": 1,
        "schema": {
            "export_contract_version": "nks-portable-state-v1",
            "reconstruction_contract_version": "nks-governed-history-v1",
            "supported_sequence_contracts": ["ordered-only", "contiguous-index"],
        },
        "files": manifest_files,
        "governed_reconstruction": {
            "history_path": history_path,
            "history_present": history_present,
            "history_sha256": history_sha256,
            "reconstruction_supported": history_present,
        },
        "evidence": {
            "references": evidence_references,
            "unresolved": unresolved_evidence,
        },
    }
    manifest_bytes = json.dumps(
        manifest, indent=2, sort_keys=True
    ).encode("utf-8")
    manifest_sha256 = _sha256_bytes(manifest_bytes)

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", manifest_bytes)
        for path in files:
            bundle.write(path, path.relative_to(repository_root).as_posix())

    return ExportResult(archive_path, len(files), manifest_sha256)


def import_portable_state(
    archive_path: Path,
    destination_root: Path,
    *,
    replace: bool = False,
) -> dict:
    destination_root = destination_root.resolve()
    if destination_root.exists() and any(destination_root.iterdir()):
        if not replace:
            raise FileExistsError(f"destination is not empty: {destination_root}")
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "r") as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        if manifest.get("format") != "nks-portable-state":
            raise ValueError("unsupported portable-state format")
        if manifest.get("version") != 1:
            raise ValueError("unsupported portable-state version")
        schema = manifest.get("schema", {})
        if not isinstance(schema, dict):
            raise ValueError("invalid schema section")
        reconstruction_section = manifest.get(
            "governed_reconstruction",
            {
                "history_present": False,
                "reconstruction_supported": False,
                "history_path": "records/history/transitions.json",
                "history_sha256": None,
            },
        )
        if not isinstance(reconstruction_section, dict):
            raise ValueError("invalid governed reconstruction section")
        if not isinstance(reconstruction_section.get("history_present"), bool):
            raise ValueError("invalid governed reconstruction history flag")
        if not isinstance(reconstruction_section.get("reconstruction_supported"), bool):
            raise ValueError("invalid governed reconstruction support flag")
        history_present = reconstruction_section.get("history_present", False)
        reconstruction_supported = reconstruction_section.get("reconstruction_supported", False)
        history_path = reconstruction_section.get("history_path", "records/history/transitions.json")
        history_sha256 = reconstruction_section.get("history_sha256")
        if not isinstance(history_path, str) or not history_path:
            raise ValueError("invalid governed reconstruction history path")
        if history_sha256 is not None and not isinstance(history_sha256, str):
            raise ValueError("invalid governed reconstruction history checksum")
        if reconstruction_supported and not history_present:
            raise ValueError("invalid governed reconstruction declaration")

        file_items = manifest.get("files", [])
        if not isinstance(file_items, list):
            raise ValueError("invalid files section")
        file_paths = {
            str(item.get("path"))
            for item in file_items
            if isinstance(item, dict) and "path" in item
        }

        if history_present:
            if history_path not in file_paths:
                raise ValueError("missing governed history file")
            history_bytes = bundle.read(history_path)
            PersistedKnowledgeHistory.model_validate_json(history_bytes.decode("utf-8"))
            if history_sha256 is not None and _sha256_bytes(history_bytes) != history_sha256:
                raise ValueError("governed history checksum mismatch")

        evidence = manifest.get("evidence", {"references": [], "unresolved": []})
        if not isinstance(evidence, dict):
            raise ValueError("invalid evidence section")
        if not isinstance(evidence.get("references", []), list):
            raise ValueError("invalid evidence references")
        if not isinstance(evidence.get("unresolved", []), list):
            raise ValueError("invalid unresolved evidence references")

        for item in manifest.get("files", []):
            relative = Path(str(item["path"]))
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsafe archive path: {relative}")
            data = bundle.read(relative.as_posix())
            if _sha256_bytes(data) != item["sha256"]:
                raise ValueError(f"checksum mismatch: {relative}")
            target = destination_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

    return manifest


def verify_imported_state(destination_root: Path, manifest: dict) -> None:
    for item in manifest.get("files", []):
        path = destination_root / str(item["path"])
        if not path.exists():
            raise FileNotFoundError(path)
        data = path.read_bytes()
        if _sha256_bytes(data) != item["sha256"]:
            raise ValueError(f"import verification failed: {item['path']}")
