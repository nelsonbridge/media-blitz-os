"""Hosted TEST identity, tenancy, purpose, and execution-context enforcement.

This module extends Enki's provider-neutral boundary isolation with an identity layer
that is suitable for hosted adapter integration while remaining credential-free and
no-effect in repository validation.  TEST credentials can never authorize a
PRODUCTION request.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import (
    BoundaryAction,
    BoundaryAuthorization,
    BoundaryContext,
    HumanBoundaryPolicy,
)


_SAFE_IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"


class HostedIdentityOutcome(StrEnum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"


class HostedIdentityError(RuntimeError):
    """Fail-closed identity error that does not expose protected boundary values."""

    def __init__(self, reason_code: str) -> None:
        super().__init__("hosted identity operation denied")
        self.reason_code = reason_code


class HostedBoundaryContext(BaseModel):
    """Exact hosted request scope including purpose and caller identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    namespace_id: str = Field(pattern=_SAFE_IDENTIFIER)
    tenant_id: str = Field(pattern=_SAFE_IDENTIFIER)
    subject_id: str = Field(pattern=_SAFE_IDENTIFIER)
    domain: str = Field(pattern=_SAFE_IDENTIFIER)
    audience: str = Field(pattern=_SAFE_IDENTIFIER)
    purpose: str = Field(pattern=_SAFE_IDENTIFIER)
    principal_id: str = Field(pattern=_SAFE_IDENTIFIER)
    execution_context: ExecutionContext

    @model_validator(mode="after")
    def reject_path_shaped_identifiers(self) -> "HostedBoundaryContext":
        for value in (
            self.namespace_id,
            self.tenant_id,
            self.subject_id,
            self.domain,
            self.audience,
            self.purpose,
            self.principal_id,
        ):
            if value in {".", ".."} or ".." in value or "/" in value or "\\" in value:
                raise ValueError("hosted boundary identifiers cannot contain path traversal")
        return self

    @property
    def context_sha256(self) -> str:
        return canonical_sha256(self)

    @property
    def boundary(self) -> BoundaryContext:
        return BoundaryContext(
            namespace_id=self.namespace_id,
            tenant_id=self.tenant_id,
            subject_id=self.subject_id,
            domain=self.domain,
            audience=self.audience,
            execution_context=self.execution_context,
        )


class HostedCredential(BaseModel):
    """Signed, scoped TEST credential. No raw signing key is persisted in the model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    credential_id: str = Field(pattern=_SAFE_IDENTIFIER)
    principal_id: str = Field(pattern=_SAFE_IDENTIFIER)
    tenant_id: str = Field(pattern=_SAFE_IDENTIFIER)
    permitted_subjects: tuple[str, ...] = Field(min_length=1)
    permitted_domains: tuple[str, ...] = Field(min_length=1)
    permitted_audiences: tuple[str, ...] = Field(min_length=1)
    permitted_purposes: tuple[str, ...] = Field(min_length=1)
    permitted_actions: tuple[BoundaryAction, ...] = Field(min_length=1)
    execution_context: ExecutionContext
    authority_class: str = Field(min_length=1)
    key_id: str = Field(pattern=_SAFE_IDENTIFIER)
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    signature: str = Field(pattern=r"^hmac-sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_lifecycle_and_scope(self) -> "HostedCredential":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("hosted repository credential model is TEST-only")
        if self.expires_at <= self.issued_at:
            raise ValueError("credential expiry must follow issuance")
        if self.revoked_at is not None and self.revoked_at < self.issued_at:
            raise ValueError("credential revocation cannot precede issuance")
        for values in (
            self.permitted_subjects,
            self.permitted_domains,
            self.permitted_audiences,
            self.permitted_purposes,
        ):
            if len(values) != len(set(values)):
                raise ValueError("credential scope values must be unique")
        return self

    @property
    def unsigned_payload(self) -> dict[str, object]:
        return self.model_dump(mode="python", exclude={"signature"})

    @property
    def credential_sha256(self) -> str:
        return canonical_sha256(self)


class HostedIdentityDecision(BaseModel):
    """Privacy-preserving evidence for one hosted identity decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    credential_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    principal_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    requested_context_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    action: BoundaryAction
    outcome: HostedIdentityOutcome
    reason_code: str = Field(min_length=1)
    evaluated_at: datetime
    event_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "HostedIdentityDecision":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"event_sha256"})
        )
        if self.event_sha256 != expected:
            raise ValueError("hosted identity decision hash is invalid")
        return self


class HostedIdentityResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: HostedIdentityDecision
    authorization: BoundaryAuthorization | None

    @model_validator(mode="after")
    def validate_resolution(self) -> "HostedIdentityResolution":
        if self.decision.outcome == HostedIdentityOutcome.ALLOWED:
            if self.authorization is None:
                raise ValueError("allowed identity decision requires boundary authorization")
        elif self.authorization is not None:
            raise ValueError("denied identity decision cannot carry boundary authorization")
        return self


class HostedIdentityPolicy(BaseModel):
    """Versioned provider-neutral policy for hosted identity integration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = 1
    policy_id: str = Field(min_length=1)
    required_dimensions: tuple[str, ...]
    test_signing_key_reference: str = Field(
        pattern=r"^github-actions://[A-Z][A-Z0-9_]*$"
    )
    production_identity_provider_authorized: bool = False
    production_execution_authorized: bool = False
    denial_evidence_fields: tuple[str, ...]
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_policy(self) -> "HostedIdentityPolicy":
        expected_dimensions = (
            "principal",
            "tenant",
            "subject",
            "domain",
            "audience",
            "purpose",
            "execution_context",
        )
        if self.required_dimensions != expected_dimensions:
            raise ValueError("hosted identity policy must bind every required dimension")
        if self.production_identity_provider_authorized:
            raise ValueError("Sprint 39 cannot authorize a production identity provider")
        if self.production_execution_authorized:
            raise ValueError("Sprint 39 cannot authorize production execution")
        prohibited = {
            "principal_id",
            "tenant_id",
            "subject_id",
            "domain",
            "audience",
            "purpose",
        }
        if prohibited.intersection(self.denial_evidence_fields):
            raise ValueError("denial evidence cannot expose protected boundary values")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"policy_sha256"})
        )
        if self.policy_sha256 != expected:
            raise ValueError("hosted identity policy hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HostedIdentityPolicy":
        payload = {
            "schema_version": 1,
            "required_dimensions": (
                "principal",
                "tenant",
                "subject",
                "domain",
                "audience",
                "purpose",
                "execution_context",
            ),
            "production_identity_provider_authorized": False,
            "production_execution_authorized": False,
            **values,
        }
        payload["policy_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class TestHostedIdentityAuthority:
    """Rotatable TEST-only signing authority for hosted identity adversarial proof."""

    def __init__(self, *, key_id: str, key: bytes) -> None:
        if not key_id or not key:
            raise ValueError("non-empty TEST signing key identity and bytes are required")
        self._keys: dict[str, bytes] = {key_id: bytes(key)}
        self._active_key_id = key_id

    @property
    def active_key_id(self) -> str:
        return self._active_key_id

    @staticmethod
    def _signature(payload: dict[str, object], key: bytes) -> str:
        digest = hmac.new(
            key,
            canonical_sha256(payload).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"hmac-sha256:{digest}"

    def issue(
        self,
        *,
        credential_id: str,
        principal_id: str,
        tenant_id: str,
        permitted_subjects: tuple[str, ...],
        permitted_domains: tuple[str, ...],
        permitted_audiences: tuple[str, ...],
        permitted_purposes: tuple[str, ...],
        permitted_actions: tuple[BoundaryAction, ...],
        issued_at: datetime,
        expires_at: datetime,
        revoked_at: datetime | None = None,
    ) -> HostedCredential:
        payload = {
            "credential_id": credential_id,
            "principal_id": principal_id,
            "tenant_id": tenant_id,
            "permitted_subjects": permitted_subjects,
            "permitted_domains": permitted_domains,
            "permitted_audiences": permitted_audiences,
            "permitted_purposes": permitted_purposes,
            "permitted_actions": permitted_actions,
            "execution_context": ExecutionContext.TEST,
            "authority_class": "HOSTED-TEST-IDENTITY",
            "key_id": self._active_key_id,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "revoked_at": revoked_at,
        }
        return HostedCredential(
            **payload,
            signature=self._signature(payload, self._keys[self._active_key_id]),
        )

    def verify(self, credential: HostedCredential) -> tuple[bool, str]:
        key = self._keys.get(credential.key_id)
        if key is None:
            return False, "CREDENTIAL_KEY_RETIRED"
        expected = self._signature(credential.unsigned_payload, key)
        if not hmac.compare_digest(expected, credential.signature):
            return False, "FORGED_CREDENTIAL"
        return True, "SIGNATURE_VALID"

    def rotate(self, *, key_id: str, key: bytes, retire_prior: bool = True) -> None:
        if not key_id or not key:
            raise ValueError("non-empty replacement TEST signing key is required")
        if retire_prior:
            self._keys.clear()
        self._keys[key_id] = bytes(key)
        self._active_key_id = key_id


class HostedIdentityService:
    """Resolve TEST credentials into exact Enki boundary authority or deny generically."""

    def __init__(self, authority: TestHostedIdentityAuthority) -> None:
        self._authority = authority
        self._decisions: list[HostedIdentityDecision] = []

    @property
    def decisions(self) -> tuple[HostedIdentityDecision, ...]:
        return tuple(self._decisions)

    def _decision(
        self,
        credential: HostedCredential,
        request: HostedBoundaryContext,
        *,
        action: BoundaryAction,
        outcome: HostedIdentityOutcome,
        reason_code: str,
        now: datetime,
    ) -> HostedIdentityDecision:
        payload = {
            "event_id": f"HID-EVT-{len(self._decisions) + 1:06d}",
            "credential_id_sha256": canonical_sha256(credential.credential_id),
            "principal_id_sha256": canonical_sha256(request.principal_id),
            "requested_context_sha256": request.context_sha256,
            "action": action,
            "outcome": outcome,
            "reason_code": reason_code,
            "evaluated_at": now,
        }
        decision = HostedIdentityDecision(
            **payload,
            event_sha256=canonical_sha256(payload),
        )
        self._decisions.append(decision)
        return decision

    def resolve(
        self,
        credential: HostedCredential,
        request: HostedBoundaryContext,
        *,
        action: BoundaryAction,
        now: datetime,
        subject_type: str = "ORGANIZATION",
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> HostedIdentityResolution:
        reason = "AUTHORIZED"
        valid_signature, signature_reason = self._authority.verify(credential)
        if request.execution_context != ExecutionContext.TEST:
            reason = "TEST_CREDENTIAL_CANNOT_AUTHORIZE_PRODUCTION"
        elif not valid_signature:
            reason = signature_reason
        elif credential.revoked_at is not None and credential.revoked_at <= now:
            reason = "CREDENTIAL_REVOKED"
        elif credential.expires_at <= now:
            reason = "CREDENTIAL_EXPIRED"
        elif credential.principal_id != request.principal_id:
            reason = "PRINCIPAL_MISMATCH"
        elif credential.tenant_id != request.tenant_id:
            reason = "TENANT_MISMATCH"
        elif request.subject_id not in credential.permitted_subjects:
            reason = "SUBJECT_NOT_PERMITTED"
        elif request.domain not in credential.permitted_domains:
            reason = "DOMAIN_NOT_PERMITTED"
        elif request.audience not in credential.permitted_audiences:
            reason = "AUDIENCE_NOT_PERMITTED"
        elif request.purpose not in credential.permitted_purposes:
            reason = "PURPOSE_NOT_PERMITTED"
        elif action not in credential.permitted_actions:
            reason = "ACTION_NOT_PERMITTED"
        elif subject_type == "PERSON" and (
            human_policy is None or not human_policy.permits_use
        ):
            reason = "HUMAN_POLICY_DENIED"

        outcome = (
            HostedIdentityOutcome.ALLOWED
            if reason == "AUTHORIZED"
            else HostedIdentityOutcome.DENIED
        )
        decision = self._decision(
            credential,
            request,
            action=action,
            outcome=outcome,
            reason_code=reason,
            now=now,
        )
        if outcome == HostedIdentityOutcome.DENIED:
            return HostedIdentityResolution(decision=decision, authorization=None)

        authorization = BoundaryAuthorization(
            authorization_id=f"HID-AUTH-{decision.event_sha256.removeprefix('sha256:')[:24]}",
            boundary=request.boundary,
            permitted_actions={action},
            authority_class=credential.authority_class,
            issued_at=credential.issued_at,
            expires_at=credential.expires_at,
            revoked_at=credential.revoked_at,
        )
        return HostedIdentityResolution(
            decision=decision,
            authorization=authorization,
        )

    def require(
        self,
        credential: HostedCredential,
        request: HostedBoundaryContext,
        *,
        action: BoundaryAction,
        now: datetime,
        subject_type: str = "ORGANIZATION",
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> BoundaryAuthorization:
        resolution = self.resolve(
            credential,
            request,
            action=action,
            now=now,
            subject_type=subject_type,
            human_policy=human_policy,
        )
        if resolution.authorization is None:
            raise HostedIdentityError(resolution.decision.reason_code)
        return resolution.authorization
