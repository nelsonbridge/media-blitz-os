"""Capability-based licensing without commercial-tier conditionals."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from nks.governance.capabilities import CapabilityRegistry


class LicenseBundle(BaseModel):
    """A configurable bundle of canonical capabilities."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(min_length=1)
    capabilities: frozenset[str] = Field(default_factory=frozenset)
    constraints: dict[str, object] = Field(default_factory=dict)
    display_name: str | None = None


class EntitlementResolver:
    """Resolve access by immutable capability id, never by product or tier name."""

    def __init__(self, registry: CapabilityRegistry, bundle: LicenseBundle) -> None:
        self.registry = registry
        self.bundle = bundle
        for capability_id in bundle.capabilities:
            capability = registry.get(capability_id)
            if not capability.license_eligible:
                raise ValueError(f"capability is not license eligible: {capability_id}")

    def allows(self, capability_id: str) -> bool:
        self.registry.get(capability_id)
        return capability_id in self.bundle.capabilities

    def require(self, capability_id: str) -> None:
        if not self.allows(capability_id):
            raise PermissionError(
                f"bundle {self.bundle.bundle_id} does not grant capability {capability_id}"
            )
