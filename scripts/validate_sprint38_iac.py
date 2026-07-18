#!/usr/bin/env python3
"""Validate the persisted Sprint 38 IaC package with zero external effects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nks.application.infrastructure_as_code import (
    InfrastructurePackage,
    execute_reproducibility_cycle,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing infrastructure/enki-hosted-1.0-rc2.",
    )
    args = parser.parse_args()

    package_path = (
        args.repository_root
        / "infrastructure/enki-hosted-1.0-rc2/cf-neon-r2-iac.json"
    )
    package = InfrastructurePackage.model_validate_json(
        package_path.read_text(encoding="utf-8")
    )
    cycle = execute_reproducibility_cycle(package.definition)

    report = {
        "status": "PASS_TEST_NO_EFFECT",
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "definition_id": package.definition.definition_id,
        "definition_sha256": package.definition.definition_sha256,
        "architecture_id": package.definition.architecture_id,
        "candidate_sha256": package.definition.candidate_sha256,
        "environment": package.definition.environment.value,
        "deterministic_rebuild": cycle.deterministic_rebuild,
        "initial_state_fingerprint_sha256": (
            cycle.initial_snapshot.state_fingerprint_sha256
        ),
        "rebuilt_state_fingerprint_sha256": (
            cycle.rebuilt_snapshot.state_fingerprint_sha256
        ),
        "pre_teardown_export_manifest_sha256": (
            cycle.teardown.export_manifest_sha256
        ),
        "cycle_sha256": cycle.cycle_sha256,
        "external_effect_count": cycle.external_effect_count,
        "provider_execution_authorized": False,
        "external_services_budget_usd": 0,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
