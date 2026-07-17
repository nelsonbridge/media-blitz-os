#!/usr/bin/env python3
"""Validate the exact authoritative remote head in an isolated worktree.

The runner never resets, stashes, cleans, or otherwise mutates the caller's
working tree. It fetches the configured authoritative branch, creates a
detached temporary worktree at that exact SHA, executes the credential-free
repository validation matrix, rejects governed drift, prints a JSON report,
and removes the temporary worktree unless --keep-worktree is requested.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class ValidationStep:
    name: str
    argv: tuple[str, ...]


@dataclass
class StepResult:
    name: str
    argv: list[str]
    returncode: int


class ValidationError(RuntimeError):
    """Raised when authoritative-head validation fails closed."""


def run(
    argv: Sequence[str],
    *,
    cwd: Path,
    capture: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        text=True,
        capture_output=capture,
        check=False,
    )
    if capture:
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
    if check and completed.returncode != 0:
        raise ValidationError(
            f"command failed ({completed.returncode}): {' '.join(argv)}"
        )
    return completed


def git_output(repository_root: Path, *args: str) -> str:
    result = run(("git", *args), cwd=repository_root)
    return result.stdout.strip()


def assert_sha_match(authoritative_sha: str, worktree_sha: str) -> None:
    if authoritative_sha != worktree_sha:
        raise ValidationError(
            "authoritative SHA mismatch: "
            f"remote={authoritative_sha} worktree={worktree_sha}"
        )


def validation_steps(python: str = sys.executable) -> list[ValidationStep]:
    """Return the credential-free governed validation matrix in execution order."""

    return [
        ValidationStep(
            "install-project-and-tests",
            (python, "-m", "pip", "install", "-e", ".[test]"),
        ),
        ValidationStep(
            "install-publication-render-dependency",
            (python, "-m", "pip", "install", "Pillow==12.2.0"),
        ),
        ValidationStep(
            "generate-release-integrity-evidence",
            (
                python,
                "scripts/generate_release_integrity_evidence.py",
                "--output-directory",
                "generated/release-integrity",
                "--verifier-source-commit",
                "8161b23b2e883278f25f3539ee3e392b8eb04033",
            ),
        ),
        ValidationStep("full-pytest", (python, "-m", "pytest")),
        ValidationStep(
            "state-authority-focused-tests",
            (python, "-m", "pytest", "tests/test_state_authority.py", "--no-cov"),
        ),
        ValidationStep(
            "state-authority-manifest-verify",
            (python, "-m", "nks.views.authority", "verify", "."),
        ),
        ValidationStep(
            "generate-canonical-views",
            (python, "-m", "nks.cli.root", "generate-views", "."),
        ),
        ValidationStep(
            "reject-generated-drift",
            ("git", "diff", "--exit-code", "--", "generated"),
        ),
        ValidationStep(
            "work-control-focused-tests",
            (
                python,
                "-m",
                "pytest",
                "-o",
                "addopts=",
                "-q",
                "tests/test_work_control.py",
                "tests/test_repository_audit.py",
            ),
        ),
        ValidationStep(
            "regenerate-work-control-projections",
            (
                python,
                "-c",
                "from pathlib import Path; from nks.views.work_control import write_work_control_views; write_work_control_views(Path('.'))",
            ),
        ),
        ValidationStep(
            "regenerate-authority-manifest",
            (python, "-m", "nks.views.authority", "write", "."),
        ),
        ValidationStep(
            "reject-work-control-drift",
            (
                "git",
                "diff",
                "--exit-code",
                "--",
                "generated/canonical-backlog.md",
                "generated/canonical-roadmap.md",
                "generated/state-authority-manifest.json",
            ),
        ),
        ValidationStep(
            "verify-regenerated-authority-manifest",
            (python, "-m", "nks.views.authority", "verify", "."),
        ),
        ValidationStep(
            "canonicalization-security-tests",
            (
                python,
                "-m",
                "pytest",
                "tests/test_delivery_and_feedback.py",
                "tests/test_restricted_canonical_writer.py",
                "tests/test_direct_source_write_protection.py",
                "tests/test_canonical_reservation_audit.py",
                "tests/test_dependency_extraction.py",
                "tests/test_generated_views.py",
                "--no-cov",
            ),
        ),
        ValidationStep(
            "regenerate-views-after-security-tests",
            (python, "-m", "nks.cli.root", "generate-views", "."),
        ),
        ValidationStep(
            "regenerate-repository-audit",
            (python, "-m", "nks.cli.root", "audit-repository", "."),
        ),
        ValidationStep(
            "reject-security-and-audit-drift",
            ("git", "diff", "--exit-code", "--", "generated"),
        ),
        ValidationStep(
            "render-publication-assets",
            (python, "scripts/render_publication_000001_assets.py", "--repository-root", "."),
        ),
        ValidationStep(
            "verify-publication-assets",
            (
                python,
                "scripts/render_publication_000001_assets.py",
                "--repository-root",
                ".",
                "--verify",
            ),
        ),
        ValidationStep(
            "regenerate-views-after-publication-assets",
            (python, "-m", "nks.cli.root", "generate-views", "."),
        ),
        ValidationStep(
            "reject-publication-asset-drift",
            (
                "git",
                "diff",
                "--exit-code",
                "--",
                "assets/publication-000001",
                "generated",
            ),
        ),
        ValidationStep(
            "repository-audit-tests",
            (python, "-m", "pytest", "tests/test_repository_audit.py", "--no-cov"),
        ),
        ValidationStep(
            "repository-audit-generation",
            (python, "-m", "nks.cli.root", "audit-repository", "."),
        ),
        ValidationStep(
            "branch-consolidation-governance",
            (
                python,
                "-c",
                "from scripts.cleanup_branches import archive_tag, merged_target, validate_final_branches; assert archive_tag('execution/complete-enki-sprint-14', 'abcdef1234567890') == 'archive/branches/execution-complete-enki-sprint-14-abcdef123456'; assert merged_target({'main': 'diverged', 'sandbox': 'ahead'}) == 'sandbox'; assert merged_target({'main': 'identical', 'sandbox': 'behind'}) == 'main'; validate_final_branches(['sandbox', 'main'])",
            ),
        ),
        ValidationStep(
            "final-governed-drift-check",
            (
                "git",
                "diff",
                "--exit-code",
                "--",
                "assets/publication-000001",
                "generated",
            ),
        ),
    ]


def skipped_checks() -> list[dict[str, str]]:
    return [
        {
            "name": "github-actions-artifact-upload",
            "reason": "requires GitHub Actions hosted artifact service",
        },
        {
            "name": "repository-audit-auto-commit-push",
            "reason": "would mutate a remote branch",
        },
        {
            "name": "branch-consolidation-apply-and-settings",
            "reason": "requires GitHub credentials and remote branch/repository-settings mutation",
        },
        {
            "name": "external-provider-validation",
            "reason": "requires separately authorized external TEST credentials and capabilities",
        },
        {
            "name": "production-or-human-authority-gates",
            "reason": "requires separate explicit production or human authorization",
        },
    ]


def parse_pytest_summary(output: str) -> tuple[int | None, int | None]:
    passed = re.search(r"(\d+) passed", output)
    warnings = re.search(r"(\d+) warnings?", output)
    return (
        int(passed.group(1)) if passed else None,
        int(warnings.group(1)) if warnings else 0,
    )


def read_coverage(worktree: Path) -> float | None:
    path = worktree / "coverage.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get("totals", {}).get("percent_covered")
    return float(value) if value is not None else None


def validate(
    repository_root: Path,
    *,
    remote: str,
    branch: str,
    keep_worktree: bool,
) -> dict[str, object]:
    repository_root = repository_root.resolve()
    original_branch = git_output(repository_root, "rev-parse", "--abbrev-ref", "HEAD")
    original_sha = git_output(repository_root, "rev-parse", "HEAD")
    original_status = git_output(repository_root, "status", "--short")

    run(("git", "fetch", remote, branch), cwd=repository_root)
    authoritative_ref = f"{remote}/{branch}"
    authoritative_sha = git_output(repository_root, "rev-parse", authoritative_ref)

    worktree_parent = Path(tempfile.mkdtemp(prefix="enki-authoritative-validation-"))
    worktree = worktree_parent / "worktree"
    step_results: list[StepResult] = []
    full_pytest_output = ""

    try:
        run(
            ("git", "worktree", "add", "--detach", str(worktree), authoritative_sha),
            cwd=repository_root,
        )
        worktree_sha = git_output(worktree, "rev-parse", "HEAD")
        worktree_status = git_output(worktree, "status", "--short")
        assert_sha_match(authoritative_sha, worktree_sha)
        if worktree_status:
            raise ValidationError(
                "isolated authoritative worktree is not initially clean: "
                f"{worktree_status}"
            )

        python_version = run(
            (sys.executable, "--version"), cwd=worktree
        ).stdout.strip()

        for step in validation_steps(sys.executable):
            print(f"\n==> {step.name}")
            result = run(step.argv, cwd=worktree, check=False)
            step_results.append(
                StepResult(step.name, list(step.argv), result.returncode)
            )
            if step.name == "full-pytest":
                full_pytest_output = (result.stdout or "") + (result.stderr or "")
            if result.returncode != 0:
                raise ValidationError(f"validation step failed: {step.name}")

        passed, warnings = parse_pytest_summary(full_pytest_output)
        coverage = read_coverage(worktree)
        return {
            "authoritative_ref": authoritative_ref,
            "authoritative_sha": authoritative_sha,
            "worktree_sha": worktree_sha,
            "sha_match": authoritative_sha == worktree_sha,
            "initial_worktree_status": worktree_status,
            "python_version": python_version,
            "original_workspace": {
                "branch": original_branch,
                "sha": original_sha,
                "status_short": original_status,
            },
            "tests_passed": passed,
            "warnings": warnings,
            "coverage_percent": coverage,
            "coverage_gate_percent": 70.0,
            "governed_drift": False,
            "steps": [asdict(item) for item in step_results],
            "skipped": skipped_checks(),
            "worktree": str(worktree) if keep_worktree else None,
        }
    finally:
        if not keep_worktree:
            if worktree.exists():
                run(
                    ("git", "worktree", "remove", "--force", str(worktree)),
                    cwd=repository_root,
                    check=False,
                )
            shutil.rmtree(worktree_parent, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="sandbox")
    parser.add_argument("--keep-worktree", action="store_true")
    args = parser.parse_args()

    try:
        report = validate(
            args.repository_root,
            remote=args.remote,
            branch=args.branch,
            keep_worktree=args.keep_worktree,
        )
    except ValidationError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        return 1

    print(json.dumps({"status": "passed", **report}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
