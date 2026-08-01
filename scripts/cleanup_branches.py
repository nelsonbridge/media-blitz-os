#!/usr/bin/env python3
"""Consolidate a GitHub repository to main and sandbox branches.

Unique nonmerged branch tips are preserved as lightweight archive tags before
branch deletion. The tool is dry-run by default and writes a deterministic JSON
report when requested.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
PROTECTED_BRANCHES = ("main", "sandbox")


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
    before: list[str]
    after: list[str]
    requested_branches: list[str]
    already_absent: list[str]
    deleted: list[str]
    archived: dict[str, str]
    merged_into: dict[str, str]
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


def normalize_requested_branches(branches: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for branch in branches:
        name = branch.strip()
        if not name:
            continue
        if name in PROTECTED_BRANCHES:
            raise RuntimeError(f"Refusing to delete protected branch: {name}")
        if name not in seen:
            normalized.append(name)
            seen.add(name)
    return normalized


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
    apply: bool,
    report_path: Path | None,
    requested_branches: list[str] | None = None,
) -> CleanupReport:
    branches = client.list_branches(repository)
    by_name = {branch.name: branch for branch in branches}
    before = sorted(by_name)
    errors: list[str] = []
    archived: dict[str, str] = {}
    merged_into: dict[str, str] = {}
    deleted: list[str] = []
    already_absent: list[str] = []
    requested = normalize_requested_branches(requested_branches or [])

    sandbox = by_name.get("sandbox")
    if sandbox is None:
        raise RuntimeError("sandbox branch does not exist")

    if "main" not in by_name:
        raise RuntimeError("main branch does not exist")
    if apply and not requested:
        raise RuntimeError("--apply requires at least one explicit --branch value")

    working = branches
    current = {branch.name: branch for branch in working}
    candidate_names = requested or [
        branch.name for branch in working if branch.name not in PROTECTED_BRANCHES
    ]

    for candidate_name in candidate_names:
        branch = current.get(candidate_name)
        if branch is None:
            already_absent.append(candidate_name)
            continue

        statuses: dict[str, str] = {}
        for target in PROTECTED_BRANCHES:
            if target not in current:
                continue
            try:
                statuses[target] = client.compare_status(
                    repository,
                    branch.name,
                    target,
                )
            except GitHubApiError as exc:
                errors.append(f"compare {branch.name} to {target}: {exc}")

        target = merged_target(statuses)
        if target is not None:
            merged_into[branch.name] = target
        else:
            tag = archive_tag(branch.name, branch.sha)
            archived[branch.name] = tag
            if apply:
                client.create_ref(repository, f"refs/tags/{tag}", branch.sha)

        if apply:
            client.delete_branch(repository, branch.name)
        deleted.append(branch.name)

    after_records = client.list_branches(repository) if apply else working
    after = sorted(branch.name for branch in after_records if branch.name in PROTECTED_BRANCHES)
    if apply:
        validate_final_branches([branch.name for branch in after_records])

    report = CleanupReport(
        repository=repository,
        apply=apply,
        before=before,
        after=after,
        requested_branches=requested,
        already_absent=sorted(already_absent),
        deleted=sorted(deleted),
        archived=dict(sorted(archived.items())),
        merged_into=dict(sorted(merged_into.items())),
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
        help="Exact branch name to evaluate or delete; repeat as needed",
    )
    parser.add_argument("--apply", action="store_true", help="Apply destructive cleanup")
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

    report = run_cleanup(
        GitHubClient(args.token),
        args.repository,
        apply=args.apply,
        report_path=args.report,
        requested_branches=args.branch,
    )
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
