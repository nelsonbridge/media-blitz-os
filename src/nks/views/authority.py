"""Deterministic manifest and verification for repository state authority."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.2"
MANIFEST_PATH = Path("generated/state-authority-manifest.json")

GENERATED_PROJECTIONS: tuple[dict[str, Any], ...] = (
    {"path": "generated/publication-index.md", "generator": "nks generate-views", "sources": ["records/publications/*.json"]},
    {"path": "generated/proof-index.md", "generator": "nks generate-views", "sources": ["records/proofs/*.json"]},
    {"path": "generated/visual-package-index.md", "generator": "nks generate-views", "sources": ["records/visuals/*.json"]},
    {"path": "generated/visual-request-index.md", "generator": "nks generate-views", "sources": ["records/visual-requests/*.json"]},
    {"path": "generated/feedback-index.md", "generator": "nks generate-views", "sources": ["records/feedback/*.json"]},
    {"path": "generated/event-index.md", "generator": "nks generate-views", "sources": ["records/events/*.json"]},
    {"path": "generated/graph-index.md", "generator": "nks generate-views", "sources": ["records/**/*.json"]},
    {"path": "generated/audit-report.md", "generator": "nks generate-views", "sources": ["records/**/*.json"]},
    {"path": "generated/runtime-status-report.md", "generator": "nks generate-views", "sources": ["records/**/*.json"]},
    {"path": "generated/corpus-health-dashboard.md", "generator": "nks generate-views", "sources": ["records/**/*.json"]},
    {"path": "generated/publication-package-index.md", "generator": "nks generate-views", "sources": ["*/*/receipt.json"]},
    {"path": "generated/ecosystem-capabilities.md", "generator": "nks generate-views", "sources": ["records/capabilities/ecosystem-capabilities.json"]},
    {"path": "generated/canonical-backlog.md", "generator": "nks.views.work_control write", "sources": ["records/work-items/*.json"]},
    {"path": "generated/canonical-roadmap.md", "generator": "nks.views.work_control write", "sources": ["records/sprints/*.json"]},
    {"path": "generated/audit/repository-audit.md", "generator": "nks audit-repository", "sources": ["repository tree", "records/**/*.json"]},
    {"path": "generated/audit/repository-audit.json", "generator": "nks audit-repository", "sources": ["repository tree", "records/**/*.json"]},
)

GENERATED_OUTPUT_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "directory_glob": "generated/model-feedback/*",
        "generator": "nks.application.human_state.PublishHumanStateFeedback",
        "required": False,
        "required_files": ["payload.json", "receipt.json"],
        "sources": [
            "records/human-observations/*.json",
            "records/human-transitions/*.json",
            "records/model-ingestion-policies/*.json",
            "records/model-feedback-receipts/*.json",
        ],
    },
)


def build_authority_manifest() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_precedence": [
            "canonical_machine_state",
            "generated_authoritative_projection",
            "narrative_or_historical_material",
        ],
        "canonical_machine_state": {
            "class": 1,
            "paths": ["records/**/*.json"],
            "manually_editable": True,
            "note": "Changes require schema validation and governed state transitions.",
        },
        "generated_authoritative_projections": [
            {"class": 2, "manually_editable": False, **projection}
            for projection in GENERATED_PROJECTIONS
        ],
        "generated_output_families": [
            {"class": 2, "manually_editable": False, **family}
            for family in GENERATED_OUTPUT_FAMILIES
        ],
        "narrative_or_historical_material": {
            "class": 3,
            "paths": ["docs/**/*.md", "roadmap/**/*.md", "runtime/STATUS.md", "README.md"],
            "authoritative_for_current_state": False,
            "exceptions": ["docs/state-authority-model.md"],
        },
    }


def render_authority_manifest() -> str:
    return json.dumps(build_authority_manifest(), indent=2, sort_keys=True) + "\n"


def write_authority_manifest(repository_root: Path) -> Path:
    output = repository_root / MANIFEST_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_authority_manifest(), encoding="utf-8")
    return output


def verify_authority_manifest(repository_root: Path) -> list[str]:
    violations: list[str] = []
    manifest_path = repository_root / MANIFEST_PATH
    if not manifest_path.exists():
        violations.append(f"missing generated authority manifest: {MANIFEST_PATH}")
    else:
        try:
            observed = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            violations.append(f"invalid generated authority manifest: {MANIFEST_PATH}")
        else:
            if observed != build_authority_manifest():
                violations.append(f"stale generated authority manifest: {MANIFEST_PATH}")

    for projection in GENERATED_PROJECTIONS:
        path = repository_root / projection["path"]
        if not path.exists():
            violations.append(f"missing Class 2 projection: {projection['path']}")

    for family in GENERATED_OUTPUT_FAMILIES:
        directories = sorted(repository_root.glob(family["directory_glob"]))
        if family["required"] and not directories:
            violations.append(
                f"missing required Class 2 output family: {family['directory_glob']}"
            )
        for directory in directories:
            if not directory.is_dir():
                violations.append(f"Class 2 output family member is not a directory: {directory}")
                continue
            for filename in family["required_files"]:
                path = directory / filename
                if not path.exists():
                    violations.append(
                        f"incomplete Class 2 output family member: {path.relative_to(repository_root)}"
                    )

    return violations


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write", "verify"))
    parser.add_argument("repository_root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()

    if args.command == "write":
        print(write_authority_manifest(root))
        return 0

    violations = verify_authority_manifest(root)
    if violations:
        for violation in violations:
            print(violation)
        return 1
    print("state authority manifest: verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
