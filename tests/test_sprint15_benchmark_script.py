from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from nks.application.governed_transactions import canonical_sha256
from nks.application.performance_boundaries import OperationFamily


ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_script_writes_complete_zero_cost_test_report(tmp_path) -> None:
    output = tmp_path / "sprint15-benchmark.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_sprint15_benchmarks.py"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    payload = json.loads(output.read_text(encoding="utf-8"))
    suite_hash = payload.pop("suite_sha256")
    assert suite_hash == canonical_sha256(payload)
    assert payload["execution_context"] == "TEST"
    assert payload["data_classification"] == "SYNTHETIC/TEST"
    assert payload["external_services_cost_usd"] == 0
    assert payload["external_effect"] is False
    assert payload["production_capacity_claim"] is False
    assert {item["workload"]["family"] for item in payload["reports"]} == {
        family.value for family in OperationFamily
    }
    assert all(item["within_budget"] for item in payload["reports"])
