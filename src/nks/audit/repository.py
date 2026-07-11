"""Deterministic repository census, integrity, drift, and readiness audit."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    ".venv",
    "venv",
}
RECORD_COLLECTIONS = (
    "sources",
    "artifacts",
    "proofs",
    "narratives",
    "visuals",
    "publications",
    "visual-requests",
    "feedback",
    "events",
    "capabilities",
)


@dataclass(frozen=True)
class AuditResult:
    report_path: Path
    json_path: Path
    file_count: int
    issue_count: int


def _files(root: Path, excluded_roots: tuple[Path, ...] = ()) -> list[Path]:
    """Return repository files without caches or generated audit output roots."""
    excluded = tuple(path.resolve() for path in excluded_roots)
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_DIRS for part in path.relative_to(root).parts)
        and not any(path.resolve().is_relative_to(item) for item in excluded)
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _record_index(root: Path) -> tuple[dict[str, dict], list[str]]:
    records: dict[str, dict] = {}
    issues: list[str] = []
    records_root = root / "records"
    if not records_root.exists():
        return records, ["records directory is missing"]

    for path in sorted(records_root.rglob("*.json")):
        try:
            record = _read_json(path)
        except (json.JSONDecodeError, OSError) as exc:
            issues.append(f"invalid JSON: {path.relative_to(root)} ({exc})")
            continue
        record_id = (
            record.get("id") or record.get("registry_id") or record.get("event_id")
        )
        if not record_id:
            issues.append(f"record missing identifier: {path.relative_to(root)}")
            continue
        if record_id in records:
            issues.append(f"duplicate record id: {record_id}")
        records[record_id] = {"path": str(path.relative_to(root)), "data": record}
    return records, issues


def _integrity_issues(records: dict[str, dict]) -> list[str]:
    issues: list[str] = []
    references = {
        "source_ids": True,
        "artifact_id": False,
        "proof_id": False,
        "narrative_id": False,
        "visual_package_id": False,
        "publication_id": False,
        "source_id": False,
    }
    for record_id, item in sorted(records.items()):
        data = item["data"]
        for field, many in references.items():
            value = data.get(field)
            if value is None:
                continue
            values: Iterable[str] = value if many else [value]
            for target in values:
                if target and target not in records:
                    issues.append(f"orphan reference: {record_id}.{field} -> {target}")
    return issues


def _drift_issues(root: Path, records: dict[str, dict]) -> list[str]:
    issues: list[str] = []
    generated = root / "generated"
    expected = {
        "publication-index.md": sum(
            1 for record_id in records if record_id.startswith("NKS-PUB-")
        ),
        "proof-index.md": sum(
            1 for record_id in records if record_id.startswith("NKS-PRF-")
        ),
        "visual-package-index.md": sum(
            1 for record_id in records if record_id.startswith("NKS-VIS-")
        ),
        "visual-request-index.md": sum(
            1 for record_id in records if record_id.startswith("NKS-VRQ-")
        ),
    }
    for filename, count in expected.items():
        path = generated / filename
        if not path.exists():
            issues.append(f"generated view missing: generated/{filename}")
            continue
        text = path.read_text(encoding="utf-8")
        if "Total " not in text or str(count) not in text:
            issues.append(
                f"generated view may be stale: generated/{filename} expected count {count}"
            )
    return issues


def _readiness(records: dict[str, dict]) -> dict[str, int]:
    counters: Counter[str] = Counter()
    for record_id, item in records.items():
        if not record_id.startswith("NKS-PUB-"):
            continue
        data = item["data"]
        counters[f"status:{data.get('status', 'unknown')}"] += 1
        counters[f"editorial:{data.get('editorial_status', 'unknown')}"] += 1
        counters[f"approval:{data.get('user_approval', 'unknown')}"] += 1
    return dict(sorted(counters.items()))


def _top_level_counts(root: Path, files: list[Path]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for path in files:
        relative = path.relative_to(root)
        counts[relative.parts[0] if len(relative.parts) > 1 else "(root)"] += 1
    return dict(sorted(counts.items()))


def _extension_counts(files: list[Path]) -> dict[str, int]:
    counts = Counter(path.suffix.lower() or "(none)" for path in files)
    return dict(sorted(counts.items()))


def _record_counts(root: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for collection in RECORD_COLLECTIONS:
        directory = root / "records" / collection
        result[collection] = (
            len(list(directory.glob("*.json"))) if directory.exists() else 0
        )
    return result


def audit_repository(root: Path, output_dir: Path | None = None) -> AuditResult:
    root = root.resolve()
    output_dir = (output_dir or root / "generated" / "audit").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = _files(root, excluded_roots=(output_dir,))
    records, parse_issues = _record_index(root)
    integrity = _integrity_issues(records)
    drift = _drift_issues(root, records)
    issues = sorted(parse_issues + integrity + drift)

    payload = {
        "audit_version": 1,
        "repository_root": str(root),
        "file_count": len(files),
        "top_level_counts": _top_level_counts(root, files),
        "extension_counts": _extension_counts(files),
        "record_counts": _record_counts(root),
        "record_count": len(records),
        "test_count": (
            len(list((root / "tests").glob("test_*.py")))
            if (root / "tests").exists()
            else 0
        ),
        "schema_count": (
            len(list((root / "schemas").rglob("*.*")))
            if (root / "schemas").exists()
            else 0
        ),
        "readiness": _readiness(records),
        "issues": issues,
        "issue_count": len(issues),
    }

    json_path = output_dir / "repository-audit.json"
    report_path = output_dir / "repository-audit.md"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Repository Audit",
        "",
        "> Generated from repository state. Do not edit manually.",
        "",
        "## Census",
        "",
        f"- Files: {payload['file_count']}",
        f"- Canonical records: {payload['record_count']}",
        f"- Tests: {payload['test_count']}",
        f"- Schemas: {payload['schema_count']}",
        "",
        "## Top-Level File Counts",
        "",
        "| Area | Files |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {name} | {count} |" for name, count in payload["top_level_counts"].items()
    )
    lines.extend(
        [
            "",
            "## Canonical Record Counts",
            "",
            "| Collection | Records |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {name} | {count} |" for name, count in payload["record_counts"].items()
    )
    lines.extend(
        [
            "",
            "## Publication Readiness",
            "",
            "| State | Count |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {name} | {count} |" for name, count in payload["readiness"].items()
    )
    lines.extend(["", "## Findings", ""])
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append(
            "- No census, reference-integrity, or generated-view drift issues detected."
        )
    lines.extend(["", f"Total findings: {len(issues)}", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return AuditResult(report_path, json_path, len(files), len(issues))
