"""Governance runtime for canonical capabilities, authority, and entitlements."""

from nks.governance.authority import AuthorityDecision, AuthorityResolver
from nks.governance.capabilities import Capability, CapabilityRegistry
from nks.governance.entitlements import EntitlementResolver, LicenseBundle

__all__ = [
    "AuthorityDecision",
    "AuthorityResolver",
    "Capability",
    "CapabilityRegistry",
    "EntitlementResolver",
    "LicenseBundle",
]
