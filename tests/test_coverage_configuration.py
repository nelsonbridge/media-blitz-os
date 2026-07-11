from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_quantitative_coverage_configuration_is_enforced() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    test_dependencies = config["project"]["optional-dependencies"]["test"]
    pytest_addopts = config["tool"]["pytest"]["ini_options"]["addopts"]
    coverage_run = config["tool"]["coverage"]["run"]
    coverage_report = config["tool"]["coverage"]["report"]

    assert any(dependency.startswith("pytest-cov") for dependency in test_dependencies)
    assert "--cov=nks" in pytest_addopts
    assert "--cov-branch" in pytest_addopts
    assert "--cov-report=xml:coverage.xml" in pytest_addopts
    assert "--cov-report=json:coverage.json" in pytest_addopts
    assert "--cov-fail-under=70" in pytest_addopts
    assert coverage_run["branch"] is True
    assert coverage_report["fail_under"] == 70
