from __future__ import annotations

from pathlib import Path

import pytest

from nks.domain.models import WorkflowEvent
from nks.governance import (
    AuthorityResolver,
    CapabilityRegistry,
    EntitlementResolver,
    LicenseBundle,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_capability_registry_loads_anu_and_enki() -> None:
    registry = CapabilityRegistry(REPOSITORY_ROOT)

    assert registry.get("ANU").parent_id is None
    assert registry.get("ENKI").parent_id == "ANU"
    assert registry.requires("ENKI") == frozenset({"ANU"})


def test_enki_cannot_infer_anu_authority() -> None:
    resolver = AuthorityResolver(REPOSITORY_ROOT)

    decision = resolver.resolve(
        action="publish",
        requested_by="conversational-reasoning-adapter",
    )

    assert decision.authorized is False
    assert decision.required_authority == "ANU"


def test_enki_can_act_after_explicit_anu_approval() -> None:
    resolver = AuthorityResolver(REPOSITORY_ROOT)

    decision = resolver.resolve(
        action="publish",
        requested_by="conversational-reasoning-adapter",
        approval_holder_reference="founder-origin-authority",
    )

    assert decision.authorized is True
    assert decision.actor_capability == "ENKI"


def test_unregistered_implementation_is_rejected() -> None:
    resolver = AuthorityResolver(REPOSITORY_ROOT)

    decision = resolver.resolve(action="analyze", requested_by="unknown-adapter")

    assert decision.authorized is False
    assert decision.actor_capability == "UNKNOWN"


def test_entitlements_are_capability_based() -> None:
    registry = CapabilityRegistry(REPOSITORY_ROOT)
    bundle = LicenseBundle(bundle_id="LIC-TEST-001", capabilities=frozenset({"ENKI"}))
    resolver = EntitlementResolver(registry, bundle)

    assert resolver.allows("ENKI") is True
    assert resolver.allows("ANU") is False
    with pytest.raises(PermissionError):
        resolver.require("ANU")


def test_workflow_event_supports_provider_neutral_attribution() -> None:
    event = WorkflowEvent(
        event_id="EVT-TEST-001",
        event_type="canonical-record-updated",
        subject_id="NKS-ART-000001",
        actor_capability="ENKI",
        actor_implementation="repository-coding-adapter",
        authority_source="ANU",
    )

    assert event.actor_capability == "ENKI"
    assert event.actor_implementation == "repository-coding-adapter"
