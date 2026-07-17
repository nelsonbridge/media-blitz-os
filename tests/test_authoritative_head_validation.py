import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_authoritative_head import (
    ValidationError,
    assert_sha_match,
    parse_pytest_summary,
    read_coverage,
    skipped_checks,
    validation_steps,
)


def test_authoritative_sha_mismatch_fails_closed():
    with pytest.raises(ValidationError, match="authoritative SHA mismatch"):
        assert_sha_match("a" * 40, "b" * 40)


def test_authoritative_sha_match_passes():
    assert_sha_match("a" * 40, "a" * 40)


def test_validation_matrix_contains_required_governed_surfaces():
    names = [step.name for step in validation_steps("python")]

    assert names[0] == "install-project-and-tests"
    assert "generate-release-integrity-evidence" in names
    assert "full-pytest" in names
    assert "state-authority-focused-tests" in names
    assert "work-control-focused-tests" in names
    assert "canonicalization-security-tests" in names
    assert "render-publication-assets" in names
    assert "verify-publication-assets" in names
    assert "repository-audit-tests" in names
    assert "branch-consolidation-governance" in names
    assert names[-1] == "final-governed-drift-check"


def test_validation_matrix_preserves_configured_full_pytest_options():
    full_pytest = next(
        step for step in validation_steps("python") if step.name == "full-pytest"
    )

    assert full_pytest.argv == ("python", "-m", "pytest")
    assert "--no-cov" not in full_pytest.argv
    assert "-o" not in full_pytest.argv


def test_skipped_checks_name_remote_and_authority_boundaries():
    skipped = {item["name"]: item["reason"] for item in skipped_checks()}

    assert "github-actions-artifact-upload" in skipped
    assert "repository-audit-auto-commit-push" in skipped
    assert "branch-consolidation-apply-and-settings" in skipped
    assert "external-provider-validation" in skipped
    assert "production-or-human-authority-gates" in skipped
    assert "remote" in skipped["repository-audit-auto-commit-push"]
    assert "authorization" in skipped["production-or-human-authority-gates"]


def test_parse_pytest_summary_extracts_passes_and_warnings():
    passed, warnings = parse_pytest_summary(
        "================ 694 passed, 6 warnings in 12.34s ================"
    )

    assert passed == 694
    assert warnings == 6


def test_parse_pytest_summary_allows_no_warning_count():
    passed, warnings = parse_pytest_summary("51 passed in 1.20s")

    assert passed == 51
    assert warnings == 0


def test_read_coverage_uses_machine_readable_total(tmp_path: Path):
    (tmp_path / "coverage.json").write_text(
        json.dumps({"totals": {"percent_covered": 88.38}}),
        encoding="utf-8",
    )

    assert read_coverage(tmp_path) == 88.38


def test_read_coverage_returns_none_when_report_is_absent(tmp_path: Path):
    assert read_coverage(tmp_path) is None
