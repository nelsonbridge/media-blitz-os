from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_capability_registry_has_unique_ids_and_resolvable_records() -> None:
    registry = load_json("records/capabilities/capability-registry.json")
    entries = registry["capabilities"]
    ids = [entry["id"] for entry in entries]

    assert len(ids) == len(set(ids))
    assert ids == ["ANU", "ENKI"]

    for entry in entries:
        record_path = ROOT / entry["record"]
        assert record_path.exists()
        record = json.loads(record_path.read_text(encoding="utf-8"))
        assert record["id"] == entry["id"]
        assert record["implementation_independent"] is True


def test_anu_and_enki_hierarchy_is_explicit() -> None:
    anu = load_json("records/capabilities/ANU.json")
    enki = load_json("records/capabilities/ENKI.json")

    assert anu["parent_id"] is None
    assert anu["authority_class"] == "constitutional"
    assert anu["license_eligible"] is False

    assert enki["parent_id"] == "ANU"
    assert enki["authority_class"] == "domain"
    assert enki["license_eligible"] is True
    assert enki["metadata"]["collective_capability"] is True
    assert enki["metadata"]["exclusive_implementation_allowed"] is False


def test_roles_and_implementations_are_separate_records() -> None:
    registry = load_json("records/stewards/stewards.json")
    assignments = registry["assignments"]

    anu_assignments = [item for item in assignments if item["capability_id"] == "ANU"]
    enki_assignments = [item for item in assignments if item["capability_id"] == "ENKI"]

    assert len(anu_assignments) == 1
    assert anu_assignments[0]["assignment_type"] == "authority-holder"
    assert anu_assignments[0]["holder_reference"] != "ANU"

    assert any(item["assignment_type"] == "steward" for item in enki_assignments)
    implementations = [
        item for item in enki_assignments if item["assignment_type"] == "implementation"
    ]
    assert len(implementations) >= 2
    assert all(item["holder_reference"] != "ENKI" for item in implementations)
    assert all(
        "implementation is not ENKI itself" in item["authority_limits"]
        for item in implementations
    )


def test_brand_names_do_not_control_capability_registry() -> None:
    registry = load_json("records/capabilities/capability-registry.json")
    serialized = json.dumps(registry).lower()

    for commercial_term in ("professional os", "career platform", "media blitz product"):
        assert commercial_term not in serialized

    assert registry["rules"]["commercial_names_are_metadata"] is True
    assert registry["rules"]["personal_identity_in_domain_logic_forbidden"] is True


def test_constitutional_documents_are_present() -> None:
    required = (
        "docs/governance/NKS-CONSTITUTION.md",
        "docs/standards/NKS-STD-001-Canonical-Naming.md",
        "docs/standards/NKS-STD-002-Role-Independence.md",
        "docs/standards/NKS-STD-003-Capability-Hierarchy.md",
        "docs/standards/NKS-STD-004-Licensing-Model.md",
        "schemas/capability.schema.json",
        "schemas/stewardship.schema.json",
    )

    for relative_path in required:
        assert (ROOT / relative_path).exists(), relative_path
