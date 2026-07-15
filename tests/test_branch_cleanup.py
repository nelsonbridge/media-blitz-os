import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cleanup_branches import archive_tag, merged_target, validate_final_branches


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
