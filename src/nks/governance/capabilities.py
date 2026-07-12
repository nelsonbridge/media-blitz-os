"""Load and validate immutable capability records from canonical repository state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Capability(BaseModel):
    """Runtime projection of a canonical capability record."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    canonical_name: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    parent_id: str | None = None
    purpose: str = Field(min_length=1)
    status: str = "active"
    responsibilities: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)
    provides: list[str] = Field(default_factory=list)
    implementation_independent: bool = True
    license_eligible: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityRegistry:
    """Repository-backed source of truth for enduring capability identities."""

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root
        self.records_root = repository_root / "records" / "capabilities"
        self.registry_path = self.records_root / "capability-registry.json"
        self._capabilities = self._load()
        self.validate_hierarchy()

    def _load(self) -> dict[str, Capability]:
        if not self.registry_path.exists():
            raise FileNotFoundError(self.registry_path)
        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        identifiers = registry.get("capability_ids") or registry.get("capabilities") or []
        if identifiers and isinstance(identifiers[0], dict):
            identifiers = [item["id"] for item in identifiers]
        capabilities: dict[str, Capability] = {}
        for capability_id in identifiers:
            path = self.records_root / f"{capability_id}.json"
            capability = Capability.model_validate_json(path.read_text(encoding="utf-8"))
            if capability.id in capabilities:
                raise ValueError(f"duplicate capability id: {capability.id}")
            capabilities[capability.id] = capability
        return capabilities

    def get(self, capability_id: str) -> Capability:
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise KeyError(f"unknown capability: {capability_id}") from exc

    def all(self) -> tuple[Capability, ...]:
        return tuple(self._capabilities[key] for key in sorted(self._capabilities))

    def requires(self, capability_id: str) -> frozenset[str]:
        capability = self.get(capability_id)
        return frozenset(capability.requires)

    def validate_hierarchy(self) -> None:
        for capability in self._capabilities.values():
            references = [*capability.requires]
            if capability.parent_id:
                references.append(capability.parent_id)
            missing = sorted({item for item in references if item not in self._capabilities})
            if missing:
                raise ValueError(
                    f"capability {capability.id} references unknown capabilities: {missing}"
                )
            if capability.id in references:
                raise ValueError(f"capability {capability.id} cannot depend on itself")

        def visit(capability_id: str, stack: tuple[str, ...]) -> None:
            if capability_id in stack:
                chain = " -> ".join((*stack, capability_id))
                raise ValueError(f"capability hierarchy cycle: {chain}")
            capability = self.get(capability_id)
            dependencies = list(capability.requires)
            if capability.parent_id:
                dependencies.append(capability.parent_id)
            for dependency in dependencies:
                visit(dependency, (*stack, capability_id))

        for capability_id in self._capabilities:
            visit(capability_id, ())
