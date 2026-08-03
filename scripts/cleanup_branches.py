#!/usr/bin/env python3
"""Audit or explicitly delete non-authoritative GitHub branches.

The tool is non-destructive by default. Destructive execution requires every
branch to be named explicitly with ``--branch``. It never moves ``main`` or
``sandbox`` and never changes repository settings. Unique branch tips are
preserved as lightweight archive tags before deletion.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
PROTECTED_BRANCHES = ("main", "sandbox")
POST_DELETE_ATTEMPTS = 8
POST_DELETE_DELAY_SECONDS = 1.0


class GitHubApiError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"GitHub API {status}: {message}")
        self.status = status
        self.message = message


@dataclass(frozen=True)
class BranchRecord:
    name: str
    sha: str


@dataclass
class CleanupReport:
    repository: str
    apply: bool
    requested: list[str]
    before: list[str]
    after: list[str]
    deleted: list[str]
    already_absent: list[str]
    archived: dict[str, str]
    merged_into: dict[str, str]
    protected_unchanged: bool
    errors: list[str]


class GitHubClient:
    def __init__(self, token: str) -> None:
        if not token:
            raise ValueError("A GitHub token is required")
        self._token = token

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        allow_statuses: tuple[int, ...] = (),
    ) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{API_ROOT}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "enki-branch-cleanup",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code in allow_statuses:
                return {"status": exc.code, "body": body}
            try:
                message = json.loads(body).get("message", body)
            except json.JSONDecodeError:
                message = body
            raise GitHubApiError(exc.code, str(message)) from exc

    def list_branches(self, repository: str) -> list[BranchRecord]:
        result: list[BranchRecord] = []
        page = 1
        while True:
            rows = self.request(
                "GET",
                f"/repos/{repository}/branches?per_page=100&page={page}",
            )
            for row in rows:
                result.append(BranchRecord(row["name"], row["commit"]["sha"]))
            if len(rows) < 100:
                break
            page += 1
        return sorted(result, key=lambda item: item.name)

    def compare_status(self, repository: str, base: str, head: str) -> str:
        comparison = quote(f"{base}...{head}", safe="")
        payload = self.request("GET", f"/repos/{repository}/compare/{comparison}")
        return str(payload["status"])

    def create_ref(self, repository: str, ref: str, sha: str) -> bool:
        response = self.request(
            "POST",
            f"/repos/{repository}/git/refs",
            {"ref": ref, "sha": sha},
            allow_statuses=(422,),
        )
        return not (isinstance(response, dict) and response.get("status") == 422)

    def delete_branch(self, repository: str, branch: str) -> None:
        encoded = quote(branch, safe="")
        self.request("DELETE", f"/repos/{repository}/git/refs/heads/{encoded}")


def archive_tag(branch: str, sha: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-") or "branch"
    return f"archive/branches/{slug}-{sha[:12]}"


def merged_target(status_by_target: dict[str, str]) -> str | None:
    for target in PROTECTED_BRANCHES:
        if status_by_target.get(target) in {"ahead", "identical"}:
            return target
    return None


def validate_final_branches(branches: list[str]) -> None:
    if sorted(branches) != sorted(PROTECTED_BRANCHES):
        raise RuntimeError(
            "Branch cleanup invariant failed: expected only main and sandbox, "
            f"found {branches}"
        )


def validate_requested_branches(branches: list[str]) -> list[str]:
    requested = sorted(set(branches))
    protected = sorted(set(requested).intersection(PROTECTED_BRANCHES))
    if protected:
        raise RuntimeError(
            "Protected branches cannot be cleanup targets: " + ", ".join(protected)
        )
    return requested


def wait_for_final_branch_records(
    client: GitHubClient,
    repository: str,
    *,
    attempts: int = POST_DELETE_ATTEMPTS,
    delay_seconds: float = POST_DELETE_DELAY_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> list[BranchRecord]:
    """Reconcile GitHub's eventually consistent branch-list response.

    Ref deletion is authoritative when the DELETE request succeeds, but the
    branches listing can briefly return the deleted ref. Poll a bounded number
    of times and preserve fail-closed behavior if the invariant never settles.
    """

    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    records: list[BranchRecord] = []
    for attempt in range(attempts):
        records = client.list_branches(repository)
        names = sorted(branch.name for branch in records)
        if names == sorted(PROTECTED_BRANCHES):
            return records
        if attempt + 1 < attempts:
            sleep(delay_seconds)

    validate_final_branches(sorted(branch.name for branch in records))
    return records


def write_report(path: Path, report: CleanupReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_cleanup(
    client: GitHubClient,
    repository: str,
    *,
    branches: list[str] | None,
    apply: bool,
    report_path: Path | None,
    settle_attempts: int = POST_DELETE_ATTEMPTS,
    settle_delay_seconds: float = POST_DELETE_DELAY_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> CleanupReport:
    records = client.list_branches(repository)
    by_name = {branch.name: branch for branch in records}
    before = sorted(by_name)
    unapproved = sorted(set(before).difference(PROTECTED_BRANCHES))

    supplied = list(branches or [])
    if apply and not supplied:
        raise RuntimeError(
            "Destructive cleanup requires at least one explicit --branch value"
        )

    requested = validate_requested_branches(supplied if supplied else unapproved)
    already_absent = sorted(branch for branch in requested if branch not in by_name)
    live_requested = sorted(branch for branch in requested if branch in by_name)

    if apply:
        projected = sorted(set(before).difference(live_requested))
        # Preflight before any mutation. The caller must explicitly name every
        # non-authoritative live branch, preventing partial cleanup.
        validate_final_branches(projected)

    archived: dict[str, str] = {}
    merged_into: dict[str, str] = {}
    deleted: list[str] = []
    errors: list[str] = []

    protected_before = {
        name: by_name[name].sha for name in PROTECTED_BRANCHES if name in by_name
    }

    for branch_name in live_requested:
        branch = by_name[branch_name]
        statuses: dict[str, str] = {}
        for target in PROTECTED_BRANCHES:
            if target not in by_name:
                continue
            try:
                statuses[target] = client.compare_status(
                    repository,
                    branch_name,
                    target,
                )
            except GitHubApiError as exc:
                errors.append(f"compare {branch_name} to {target}: {exc}")

        target = merged_target(statuses)
        if target is not None:
            merged_into[branch_name] = target
        else:
            tag = archive_tag(branch_name, branch.sha)
            archived[branch_name] = tag
            if apply:
                client.create_ref(repository, f"refs/tags/{tag}", branch.sha)

        if apply:
            client.delete_branch(repository, branch_name)
            deleted.append(branch_name)

    after_records = (
        wait_for_final_branch_records(
            client,
            repository,
            attempts=settle_attempts,
            delay_seconds=settle_delay_seconds,
            sleep=sleep,
        )
        if apply
        else records
    )
    after = sorted(branch.name for branch in after_records)

    after_by_name = {branch.name: branch.sha for branch in after_records}
    protected_unchanged = all(
        after_by_name.get(name) == sha for name, sha in protected_before.items()
    )
    if not protected_unchanged:
        raise RuntimeError("Protected branch tips changed during cleanup")

    report = CleanupReport(
        repository=repository,
        apply=apply,
        requested=requested,
        before=before,
        after=after,
        deleted=sorted(deleted),
        already_absent=already_absent,
        archived=dict(sorted(archived.items())),
        merged_into=dict(sorted(merged_into.items())),
        protected_unchanged=protected_unchanged,
        errors=errors,
    )
    if report_path is not None:
        write_report(report_path, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="Repository in owner/name form",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token; defaults to GITHUB_TOKEN",
    )
    parser.add_argument(
        "--branch",
        action="append",
        default=[],
        help="Exact branch to delete; repeat for each branch",
    )
    parser.add_argument("--apply", action="store_true", help="Apply explicit cleanup")
    parser.add_argument("--report", type=Path, help="Write JSON cleanup report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.repository:
        print("--repository or GITHUB_REPOSITORY is required", file=sys.stderr)
        return 2
    if not args.token:
        print("--token or GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    try:
        report = run_cleanup(
            GitHubClient(args.token),
            args.repository,
            branches=args.branch,
            apply=args.apply,
            report_path=args.report,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
