"""Resolve authority without binding domain logic to people, vendors, or models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from nks.governance.capabilities import CapabilityRegistry


@dataclass(frozen=True)
class AuthorityDecision:
    authorized: bool
    action: str
    requested_by: str
    actor_capability: str
    required_authority: str | None
    reason: str


class AuthorityResolver:
    """Evaluate implementation requests against canonical stewardship assignments."""

    _ANU_ACTIONS = frozenset(
        {
            "constitutional-amendment",
            "publish",
            "external-dispatch",
            "irreversible-governance-change",
            "waive-evidence-gate",
        }
    )

    def __init__(self, repository_root: Path, registry: CapabilityRegistry | None = None) -> None:
        self.repository_root = repository_root
        self.registry = registry or CapabilityRegistry(repository_root)
        path = repository_root / "records" / "stewards" / "stewards.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assignments: list[dict[str, object]] = raw.get("assignments", [])

    def _assignment_for(self, holder_reference: str) -> dict[str, object] | None:
        for assignment in self.assignments:
            if (
                assignment.get("holder_reference") == holder_reference
                and assignment.get("status") == "active"
            ):
                return assignment
        return None

    def resolve(
        self,
        *,
        action: str,
        requested_by: str,
        explicit_authority: str | None = None,
    ) -> AuthorityDecision:
        assignment = self._assignment_for(requested_by)
        if assignment is None:
            return AuthorityDecision(
                authorized=False,
                action=action,
                requested_by=requested_by,
                actor_capability="UNKNOWN",
                required_authority="ANU" if action in self._ANU_ACTIONS else "ENKI",
                reason="requesting implementation is not actively registered",
            )

        actor_capability = str(assignment["capability_id"])
        self.registry.get(actor_capability)

        if action in self._ANU_ACTIONS:
            if explicit_authority != "ANU":
                return AuthorityDecision(
                    authorized=False,
                    action=action,
                    requested_by=requested_by,
                    actor_capability=actor_capability,
                    required_authority="ANU",
                    reason="explicit ANU authority is required and may not be inferred",
                )
            if actor_capability != "ANU":
                anu_holder = any(
                    item.get("capability_id") == "ANU"
                    and item.get("holder_reference") == explicit_authority
                    and item.get("status") == "active"
                    for item in self.assignments
                )
                if not anu_holder:
                    # explicit_authority is a capability assertion, not an impersonation grant.
                    return AuthorityDecision(
                        authorized=False,
                        action=action,
                        requested_by=requested_by,
                        actor_capability=actor_capability,
                        required_authority="ANU",
                        reason="ANU approval must be recorded by an active ANU authority holder",
                    )

        return AuthorityDecision(
            authorized=True,
            action=action,
            requested_by=requested_by,
            actor_capability=actor_capability,
            required_authority=None,
            reason="registered implementation is authorized within its capability boundary",
        )

    def require(
        self,
        *,
        action: str,
        requested_by: str,
        explicit_authority: str | None = None,
    ) -> AuthorityDecision:
        decision = self.resolve(
            action=action,
            requested_by=requested_by,
            explicit_authority=explicit_authority,
        )
        if not decision.authorized:
            raise PermissionError(decision.reason)
        return decision
