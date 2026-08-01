import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cleanup_branches import (
    BranchRecord,
    archive_tag,
    merged_target,
    normalize_requested_branches,
    run_cleanup,
    validate_final_branches,
)


def test_archive_tag_is_stable_and_preserves_tip_identity():
    assert archive_tag("execution/complete-enki-sprint-14", "abcdef1234567890") == (
        "archive/branches/execution-complete-enki-sprint-14-abcdef123456"
    )


def test_merged_target_accepts_ancestor_or_identical_branch():
    assert merged_target({"main": "diverged", "sandbox": "ahead"}) == "sandbox"
    assert merged_target({"main": "identical", "sandbox": "behind"}) == "main"
    assert merged_target({"main": "behind", "sandbox": "diverged"}) is None


def test_only_main_and_sandbox_satisfy_cleanup_invariant():
    validate_final_branches(["sandbox", "main"])


def test_extra_branch_violates_cleanup_invariant():
    try:
        validate_final_branches(["main", "sandbox", "feature/stale"])
    except RuntimeError as exc:
        assert "expected only main and sandbox" in str(exc)
    else:
        raise AssertionError("extra branch should fail the invariant")


def test_normalize_requested_branches_rejects_protected_names():
    with pytest.raises(RuntimeError, match="protected branch"):
        normalize_requested_branches(["main"])


def test_normalize_requested_branches_deduplicates_and_trims():
    assert normalize_requested_branches([
        " feature/stale ",
        "feature/stale",
        "",
        "sandbox-copy",
    ]) == ["feature/stale", "sandbox-copy"]


class RecordingClient:
    def __init__(self, branches: list[BranchRecord]) -> None:
        self._branches = {branch.name: branch for branch in branches}
        self.deleted: list[str] = []

    def list_branches(self, repository: str) -> list[BranchRecord]:
        return sorted(self._branches.values(), key=lambda branch: branch.name)

    def compare_status(self, repository: str, base: str, head: str) -> str:
        if base == "feature/stale" and head == "sandbox":
            return "ahead"
        return "behind"

    def create_ref(self, repository: str, ref: str, sha: str) -> bool:
        return True

    def delete_branch(self, repository: str, branch: str) -> None:
        self.deleted.append(branch)
        self._branches.pop(branch, None)


def test_apply_requires_explicit_branch_targets():
    client = RecordingClient(
        [
            BranchRecord("main", "1111111"),
            BranchRecord("sandbox", "2222222"),
            BranchRecord("feature/stale", "3333333"),
        ]
    )

    with pytest.raises(RuntimeError, match="explicit --branch"):
        run_cleanup(
            client,
            "owner/repo",
            apply=True,
            report_path=None,
        )


def test_apply_deletes_only_requested_branch_and_preserves_approved_refs():
    client = RecordingClient(
        [
            BranchRecord("main", "1111111"),
            BranchRecord("sandbox", "2222222"),
            BranchRecord("feature/stale", "3333333"),
        ]
    )

    report = run_cleanup(
        client,
        "owner/repo",
        apply=True,
        report_path=None,
        requested_branches=["feature/stale"],
    )

    assert client.deleted == ["feature/stale"]
    assert report.deleted == ["feature/stale"]
    assert report.after == ["main", "sandbox"]
