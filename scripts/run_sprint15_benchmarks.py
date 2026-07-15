#!/usr/bin/env python3
"""Run the governed Sprint 15 synthetic benchmark suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nks.application.governed_transactions import canonical_sha256
from nks.application.performance_boundaries import run_default_synthetic_suite


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reports = run_default_synthetic_suite()
    payload = {
        "suite_id": "ENKI-SPRINT-15-SYNTHETIC-SMALL",
        "execution_context": "TEST",
        "data_classification": "SYNTHETIC/TEST",
        "external_services_cost_usd": 0,
        "external_effect": False,
        "production_capacity_claim": False,
        "reports": [report.model_dump(mode="json") for report in reports],
    }
    payload["suite_sha256"] = canonical_sha256(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
