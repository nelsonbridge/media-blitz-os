from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cleanup_branches import (
    BranchRecord,
    archive_tag,
    merged_target,
    run_cleanup,
    validate_final_branches,
    validate_requested_branches,
    wait_for_final_branch_records,
)


class FakeGitHubClient:
    def __init__(
        self,
        branches: list[BranchRecord],
        *,
        comparisons: dict[tuple[str, str], str] | None = None,
        stale_reads_after_delete: int = 0,
    ) -> None:
        self.branches = {branch.name: branch for branch in branches}
        self.comparisons = comparisons or {}
        self.created_refs: list[tuple[str, str]] = []
        self.deleted_branches: list[str] = []
        self.stale_reads_after_delete = stale_reads_after_delete
        self._stale_snapshot: list[BranchRecord] | None = None
        self._stale_reads_remaining = 0

    def list_branches(self, repository: str) -> list[BranchRecord]:
        del repository
        if self._stale_reads_remaining and self._stale_snapshot is not None:
            self._stale_reads_remaining -= 1
            return list(self._stale_snapshot)
        return sorted(self.branches.values(), key=lambda item: item.name)

    def compare_status(self, repository: str, base: str, head: str) -> str:
        del repository
        return self.comparisons.get((base, head), "diverged")

    def create_ref(self, repository: str, ref: str, sha: str) -> bool:
        del repository
        self.created_refs.append((ref, sha))
        return True

    def delete_branch(self, repository: str, branch: str) -> None:
        del repository
        self._stale_snapshot = sorted(self.branches.values(), key=lambda item: item.name)
        self._stale_reads_remaining = self.stale_reads_after_delete
        self.deleted_branches.append(branch)
        self.branches.pop(branch)


def _branches(*names: str) -> list[BranchRecord]:
    return [BranchRecord(name, f"{index:040x}") for index, name in enumerate(names, 1)]


def test_archive_tag_is_stable_and_preserves_tip_identity() -> None:
    assert archive_tag("execution/complete-enki-sprint-14", "abcdef1234567890") == (
        "archive/branches/execution-complete-enki-sprint-14-abcdef123456"
    )


def test_merged_target_accepts_ancestor_or_identical_branch() -> None:
    assert merged_target({"main": "diverged", "sandbox": "ahead"}) == "sandbox"
    assert merged_target({"main": "identical", "sandbox": "behind"}) == "main"
    assert merged_target({"main": "behind", "sandbox": "diverged"}) is None


def test_only_main_and_sandbox_satisfy_cleanup_invariant() -> None:
    validate_final_branches(["sandbox", "main"])


def test_extra_branch_violates_cleanup_invariant() -> None:
    with pytest.raises(RuntimeError, match="expected only main and sandbox"):
        validate_final_branches(["main", "sandbox", "feature/stale"])


def test_protected_branches_cannot_be_requested() -> None:
    with pytest.raises(RuntimeError, match="Protected branches"):
        validate_requested_branches(["feature/x", "main"])


def test_wait_for_final_branch_records_reconciles_stale_listing() -> None:
    client = FakeGitHubClient(
        _branches("main", "sandbox", "feature/x"),
        stale_reads_after_delete=2,
    )
    client.delete_branch("owner/repo", "feature/x")
    sleeps: list[float] = []

    records = wait_for_final_branch_records(
        client,
        "owner/repo",
        attempts=3,
        delay_seconds=0.25,
        sleep=sleeps.append,
    )

    assert [record.name for record in records] == ["main", "sandbox"]
    assert sleeps == [0.25, 0.25]


def test_wait_for_final_branch_records_remains_fail_closed() -> None:
    client = FakeGitHubClient(
        _branches("main", "sandbox", "feature/x"),
        stale_reads_after_delete=3,
    )
    client.delete_branch("owner/repo", "feature/x")

    with pytest.raises(RuntimeError, match="expected only main and sandbox"):
        wait_for_final_branch_records(
            client,
            "owner/repo",
            attempts=2,
            delay_seconds=0,
            sleep=lambda _: None,
        )


def test_apply_requires_explicit_branch_names() -> None:
    client = FakeGitHubClient(_branches("main", "sandbox", "feature/x"))

    with pytest.raises(RuntimeError, match="explicit --branch"):
        run_cleanup(
            client,
            "owner/repo",
            branches=[],
            apply=True,
            report_path=None,
        )

    assert client.deleted_branches == []
    assert client.created_refs == []


def test_apply_preflight_requires_every_live_unapproved_branch() -> None:
    client = FakeGitHubClient(
        _branches("main", "sandbox", "feature/x", "feature/y")
    )

    with pytest.raises(RuntimeError, match="expected only main and sandbox"):
        run_cleanup(
            client,
            "owner/repo",
            branches=["feature/x"],
            apply=True,
            report_path=None,
        )

    assert client.deleted_branches == []
    assert client.created_refs == []


def test_unmerged_tip_is_archived_before_explicit_deletion() -> None:
    original = _branches("main", "sandbox", "feature/x")
    protected = {branch.name: branch.sha for branch in original[:2]}
    feature_sha = original[2].sha
    client = FakeGitHubClient(original)

    report = run_cleanup(
        client,
        "owner/repo",
        branches=["feature/x"],
        apply=True,
        report_path=None,
    )

    assert report.deleted == ["feature/x"]
    assert report.protected_unchanged is True
    assert report.after == ["main", "sandbox"]
    assert client.created_refs == [
        ("refs/tags/archive/branches/feature-x-000000000000", feature_sha)
    ]
    assert {name: client.branches[name].sha for name in protected} == protected


def test_apply_reconciles_eventually_consistent_branch_listing() -> None:
    client = FakeGitHubClient(
        _branches("main", "sandbox", "feature/x"),
        stale_reads_after_delete=2,
    )
    sleeps: list[float] = []

    report = run_cleanup(
        client,
        "owner/repo",
        branches=["feature/x"],
        apply=True,
        report_path=None,
        settle_attempts=3,
        settle_delay_seconds=0.5,
        sleep=sleeps.append,
    )

    assert report.after == ["main", "sandbox"]
    assert report.deleted == ["feature/x"]
    assert sleeps == [0.5, 0.5]


def test_merged_tip_is_deleted_without_redundant_archive() -> None:
    client = FakeGitHubClient(
        _branches("main", "sandbox", "feature/x"),
        comparisons={("feature/x", "sandbox"): "ahead"},
    )

    report = run_cleanup(
        client,
        "owner/repo",
        branches=["feature/x"],
        apply=True,
        report_path=None,
    )

    assert report.merged_into == {"feature/x": "sandbox"}
    assert report.archived == {}
    assert client.created_refs == []
    assert client.deleted_branches == ["feature/x"]


def test_dry_run_audits_all_unapproved_branches_without_mutation() -> None:
    client = FakeGitHubClient(_branches("main", "sandbox", "feature/x"))

    report = run_cleanup(
        client,
        "owner/repo",
        branches=None,
        apply=False,
        report_path=None,
    )

    assert report.requested == ["feature/x"]
    assert report.deleted == []
    assert report.after == ["feature/x", "main", "sandbox"]
    assert report.protected_unchanged is True
    assert client.created_refs == []
    assert client.deleted_branches == []


def test_already_absent_explicit_target_is_recorded() -> None:
    client = FakeGitHubClient(_branches("main", "sandbox"))

    report = run_cleanup(
        client,
        "owner/repo",
        branches=["feature/already-gone"],
        apply=True,
        report_path=None,
    )

    assert report.already_absent == ["feature/already-gone"]
    assert report.after == ["main", "sandbox"]
    assert report.deleted == []
