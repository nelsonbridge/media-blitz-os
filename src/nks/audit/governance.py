"""Governance-specific repository audit checks."""

from __future__ import annotations

import json
from pathlib import Path

from nks.governance.capabilities import CapabilityRegistry


_PROVIDER_TOKENS = ("chatgpt", "copilot", "claude", "gemini", "openai", "anthropic")
_DOMAIN_FIELDS = ("id", "canonical_name", "display_name", "purpose", "responsibilities", "provides")


def audit_governance(repository_root: Path) -> list[str]:
    """Return deterministic governance findings; an empty list means compliant."""

    issues: list[str] = []
    try:
        registry = CapabilityRegistry(repository_root)
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return [f"capability registry invalid: {exc}"]

    if registry.get("ANU").parent_id is not None:
        issues.append("ANU must be the root constitutional capability")
    if registry.get("ENKI").parent_id != "ANU":
        issues.append("ENKI must be subordinate to ANU")

    stewardship_path = repository_root / "records" / "stewards" / "stewards.json"
    try:
        assignments = json.loads(stewardship_path.read_text(encoding="utf-8")).get(
            "assignments", []
        )
    except (OSError, json.JSONDecodeError) as exc:
        return sorted([*issues, f"stewardship registry invalid: {exc}"])

    active_anu = [
        item
        for item in assignments
        if item.get("capability_id") == "ANU" and item.get("status") == "active"
    ]
    active_enki = [
        item
        for item in assignments
        if item.get("capability_id") == "ENKI" and item.get("status") == "active"
    ]
    if not active_anu:
        issues.append("no active ANU authority holder is registered")
    if not active_enki:
        issues.append("no active ENKI steward or implementation is registered")

    known_capabilities = {item.id for item in registry.all()}
    for assignment in assignments:
        capability_id = assignment.get("capability_id")
        if capability_id not in known_capabilities:
            issues.append(
                f"stewardship assignment references unknown capability: {capability_id}"
            )
        if assignment.get("assignment_type") == "implementation" and capability_id == "ANU":
            issues.append("ANU may not be represented as a replaceable implementation")

    for capability in registry.all():
        for field in _DOMAIN_FIELDS:
            value = getattr(capability, field, None)
            serialized = json.dumps(value, sort_keys=True).lower()
            for token in _PROVIDER_TOKENS:
                if token in serialized:
                    issues.append(
                        f"provider token '{token}' appears in domain field {capability.id}.{field}"
                    )

    return sorted(set(issues))
