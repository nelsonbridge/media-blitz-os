"""Portable export/import for canonical NKS state."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path


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


def export_portable_state(repository_root: Path, archive_path: Path) -> ExportResult:
    repository_root = repository_root.resolve()
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    files = _canonical_files(repository_root)

    manifest_files: list[dict[str, str | int]] = []
    for path in files:
        relative = path.relative_to(repository_root).as_posix()
        data = path.read_bytes()
        manifest_files.append(
            {
                "path": relative,
                "sha256": _sha256_bytes(data),
                "size": len(data),
            }
        )

    manifest = {
        "format": "nks-portable-state",
        "version": 1,
        "files": manifest_files,
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
