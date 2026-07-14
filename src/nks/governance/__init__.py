"""Governance runtime for canonical capabilities, authority, and entitlements."""

from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalEvaluation,
    ApprovalGrant,
    ApprovalRequest,
    ExecutionContext,
    evaluate_approval,
)
from nks.governance.authority import AuthorityDecision, AuthorityResolver
from nks.governance.capabilities import Capability, CapabilityRegistry
from nks.governance.entitlements import EntitlementResolver, LicenseBundle

__all__ = [
    "ApprovalConsumptionStatus",
    "ApprovalDecision",
    "ApprovalEvaluation",
    "ApprovalGrant",
    "ApprovalRequest",
    "AuthorityDecision",
    "AuthorityResolver",
    "Capability",
    "CapabilityRegistry",
    "EntitlementResolver",
    "ExecutionContext",
    "LicenseBundle",
    "evaluate_approval",
]
