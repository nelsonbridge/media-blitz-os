from __future__ import annotations

import json
from pathlib import Path

from nks.audit.governance import audit_governance


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_capability_registry(
    root: Path,
    *,
    include_provider_tokens: bool = False,
    anu_parent_id: str | None = None,
    enki_parent_id: str | None = "ANU",
) -> None:
    capabilities_root = root / "records" / "capabilities"
    capabilities_root.mkdir(parents=True, exist_ok=True)

    anu_payload = {
        "id": "ANU",
        "canonical_name": "ANU",
        "display_name": "ANU",
        "kind": "constitutional",
        "parent_id": anu_parent_id,
        "purpose": "Foundational authority" if not include_provider_tokens else "ChatGPT oversight",
        "responsibilities": ["governance"],
        "requires": [],
        "provides": [],
    }
    enki_payload = {
        "id": "ENKI",
        "canonical_name": "ENKI",
        "display_name": "ENKI",
        "kind": "domain",
        "parent_id": enki_parent_id,
        "purpose": "Knowledge execution" if not include_provider_tokens else "Claude orchestration",
        "responsibilities": ["implementation"],
        "requires": ["ANU"],
        "provides": [],
    }
    _write_json(capabilities_root / "ANU.json", anu_payload)
    _write_json(capabilities_root / "ENKI.json", enki_payload)
    _write_json(
        capabilities_root / "capability-registry.json",
        {
            "capability_ids": [
                {"id": "ANU"},
                {"id": "ENKI"},
            ]
        },
    )


def _write_stewardship(
    root: Path,
    *,
    active_anu: bool = True,
    active_enki: bool = True,
    include_invalid_assignments: bool = False,
) -> None:
    stewardship_path = root / "records" / "stewards" / "stewards.json"
    assignments = []
    if active_anu:
        assignments.append(
            {
                "capability_id": "ANU",
                "assignment_type": "authority-holder",
                "status": "active",
            }
        )

    if active_enki:
        assignments.append(
            {
                "capability_id": "ENKI",
                "assignment_type": "steward",
                "status": "active",
            }
        )
    else:
        assignments.append(
            {
                "capability_id": "ENKI",
                "assignment_type": "steward",
                "status": "inactive",
            }
        )

    if include_invalid_assignments:
        assignments.extend(
            [
                {
                    "capability_id": "MISSING",
                    "assignment_type": "implementation",
                    "status": "active",
                },
                {
                    "capability_id": "ANU",
                    "assignment_type": "implementation",
                    "status": "active",
                },
            ]
        )
    _write_json(stewardship_path, {"assignments": assignments})


def test_audit_governance_returns_empty_findings_for_compliant_repository(tmp_path: Path) -> None:
    _write_capability_registry(tmp_path)
    _write_stewardship(tmp_path, active_anu=True, active_enki=True, include_invalid_assignments=False)

    findings = audit_governance(tmp_path)

    assert findings == []


def test_audit_governance_flags_invalid_registry_and_stewardship_data(tmp_path: Path) -> None:
    (tmp_path / "records" / "capabilities").mkdir(parents=True, exist_ok=True)
    (tmp_path / "records" / "capabilities" / "capability-registry.json").write_text(
        "{invalid json", encoding="utf-8"
    )

    findings = audit_governance(tmp_path)

    assert findings == ["capability registry invalid: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"]


def test_audit_governance_reports_missing_assignments_and_provider_tokens(tmp_path: Path) -> None:
    _write_capability_registry(
        tmp_path,
        include_provider_tokens=True,
        anu_parent_id=None,
        enki_parent_id="ANU",
    )
    _write_stewardship(
        tmp_path,
        active_anu=False,
        active_enki=False,
        include_invalid_assignments=True,
    )

    findings = audit_governance(tmp_path)

    assert "no active ENKI steward or implementation is registered" in findings
    assert "stewardship assignment references unknown capability: MISSING" in findings
    assert "ANU may not be represented as a replaceable implementation" in findings
    assert "provider token 'chatgpt' appears in domain field ANU.purpose" in findings
    assert "provider token 'claude' appears in domain field ENKI.purpose" in findings
