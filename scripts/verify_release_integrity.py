#!/usr/bin/env python3
"""Verify an Enki release package without external services or credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nks.application.release_integrity import verify_release_integrity


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--release-directory",
        type=Path,
        default=Path("releases/enki-0.1.0-rc1"),
    )
    parser.add_argument("--expected-source-commit")
    parser.add_argument("--expected-dependency-sha256")
    parser.add_argument("--expected-workflow-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repository_root = args.repository_root.resolve()
    release_directory = args.release_directory
    if not release_directory.is_absolute():
        release_directory = repository_root / release_directory

    result = verify_release_integrity(
        repository_root,
        release_directory,
        expected_source_commit=args.expected_source_commit,
        expected_dependency_sha256=args.expected_dependency_sha256,
        expected_workflow_sha256=args.expected_workflow_sha256,
    )
    rendered = json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
