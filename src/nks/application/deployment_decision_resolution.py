"""Governed resolution of the Enki hosted RC2 human deployment disposition.

Sprint 37 converts an explicit human disposition into a durable decision record and,
for approved dispositions, an architecture lock.  The lock is deliberately narrower
than production execution authority: it fixes the candidate-bound provider baseline
without creating credentials, spending authority, production-control evidence, or an
external deployment effect.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_release_candidate import HumanDecisionDisposition


HOSTED_RC2_VERSION = "enki-hosted-1.0-rc2"
HOSTED_RC2_SHA256 = "sha256:c443b2ff6eeb00e6682f6c56dc00cd14bdee53940432e1b9d12e9f473c9346b4"
HOSTED_RC2_REQUEST_ID = "DECISION-enki-hosted-1.0-rc2"
HOSTED_RC2_REQUEST_SHA256 = "sha256:cfb54f4f807c9ae3cbaa49b7cb76edb89ed91f034fee4559f05bfea4e850e6eb"
REFERENCE_ARCHITECTURE_ID = "CF-NEON-R2"


class DeploymentDecisionState(StrEnum):
    APPROVED = "APPROVED"
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"


_DECISION_STATE_BY_DISPOSITION = {
    HumanDecisionDisposition.APPROVE: DeploymentDecisionState.APPROVED,
    HumanDecisionDisposition.APPROVE_WITH_CONDITIONS: DeploymentDecisionState.APPROVED_WITH_CONDITIONS,
    HumanDecisionDisposition.DEFER: DeploymentDecisionState.DEFERRED,
    HumanDecisionDisposition.REJECT: DeploymentDecisionState.REJECTED,
}


class DeploymentDecisionResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    request_id: Literal[HOSTED_RC2_REQUEST_ID] = HOSTED_RC2_REQUEST_ID
    request_sha256: Literal[HOSTED_RC2_REQUEST_SHA256] = HOSTED_RC2_REQUEST_SHA256
    candidate_version: Literal[HOSTED_RC2_VERSION] = HOSTED_RC2_VERSION
    candidate_sha256: Literal[HOSTED_RC2_SHA256] = HOSTED_RC2_SHA256
    decision_authority: Literal["HUMAN"] = "HUMAN"
    decision_authority_identity: str = Field(min_length=1)
    disposition: HumanDecisionDisposition
    decision_state: DeploymentDecisionState
    conditions: tuple[str, ...] = ()
    accepted_risks: tuple[str, ...] = ()
    evidence_waivers: tuple[str, ...] = ()
    source_reference: str = Field(min_length=1)
    architecture_lock_authorized: bool
    production_execution_authorized: Literal[False] = False
    external_services_budget_usd: Literal[0] = 0
    resolution_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_resolution(self) -> "DeploymentDecisionResolution":
        expected_state = _DECISION_STATE_BY_DISPOSITION[self.disposition]
        if self.decision_state != expected_state:
            raise ValueError("decision state does not match human disposition")

        expected_lock_authority = self.disposition in {
            HumanDecisionDisposition.APPROVE,
            HumanDecisionDisposition.APPROVE_WITH_CONDITIONS,
        }
        if self.architecture_lock_authorized != expected_lock_authority:
            raise ValueError("architecture lock authority does not match human disposition")

        if self.disposition == HumanDecisionDisposition.APPROVE_WITH_CONDITIONS:
            if not self.conditions:
                raise ValueError("conditional approval requires explicit conditions")
        elif self.conditions:
            raise ValueError("conditions are only valid for APPROVE_WITH_CONDITIONS")

        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"resolution_sha256"})
        )
        if self.resolution_sha256 != expected:
            raise ValueError("deployment decision resolution hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "DeploymentDecisionResolution":
        payload = {
            "schema_version": 1,
            "request_id": HOSTED_RC2_REQUEST_ID,
            "request_sha256": HOSTED_RC2_REQUEST_SHA256,
            "candidate_version": HOSTED_RC2_VERSION,
            "candidate_sha256": HOSTED_RC2_SHA256,
            "decision_authority": "HUMAN",
            "conditions": (),
            "accepted_risks": (),
            "evidence_waivers": (),
            "production_execution_authorized": False,
            "external_services_budget_usd": 0,
            **values,
        }
        payload["resolution_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ArchitectureLock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    lock_id: Literal["ARCH-LOCK-enki-hosted-1.0-rc2"] = "ARCH-LOCK-enki-hosted-1.0-rc2"
    candidate_version: Literal[HOSTED_RC2_VERSION] = HOSTED_RC2_VERSION
    candidate_sha256: Literal[HOSTED_RC2_SHA256] = HOSTED_RC2_SHA256
    decision_resolution_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    architecture_id: Literal[REFERENCE_ARCHITECTURE_ID] = REFERENCE_ARCHITECTURE_ID
    compute_provider: Literal["Cloudflare Workers"] = "Cloudflare Workers"
    canonical_store: Literal["Neon Postgres"] = "Neon Postgres"
    object_store: Literal["Cloudflare R2"] = "Cloudflare R2"
    optional_services: tuple[str, ...] = ()
    responsibility_boundaries: tuple[str, ...]
    unresolved_prerequisites: tuple[str, ...]
    rollback_candidate_sha256: Literal[HOSTED_RC2_SHA256] = HOSTED_RC2_SHA256
    production_execution_authorized: Literal[False] = False
    external_services_budget_usd: Literal[0] = 0
    lock_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_lock(self) -> "ArchitectureLock":
        if self.optional_services:
            raise ValueError("optional provider services require a separate architecture decision")
        if not self.responsibility_boundaries:
            raise ValueError("architecture lock requires explicit responsibility boundaries")
        if not self.unresolved_prerequisites:
            raise ValueError("architecture lock must preserve unresolved prerequisites")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"lock_sha256"})
        )
        if self.lock_sha256 != expected:
            raise ValueError("architecture lock hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ArchitectureLock":
        payload = {
            "schema_version": 1,
            "lock_id": "ARCH-LOCK-enki-hosted-1.0-rc2",
            "candidate_version": HOSTED_RC2_VERSION,
            "candidate_sha256": HOSTED_RC2_SHA256,
            "architecture_id": REFERENCE_ARCHITECTURE_ID,
            "compute_provider": "Cloudflare Workers",
            "canonical_store": "Neon Postgres",
            "object_store": "Cloudflare R2",
            "optional_services": (),
            "rollback_candidate_sha256": HOSTED_RC2_SHA256,
            "production_execution_authorized": False,
            "external_services_budget_usd": 0,
            **values,
        }
        payload["lock_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class DeploymentDecisionOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: DeploymentDecisionResolution
    architecture_lock: ArchitectureLock | None

    @model_validator(mode="after")
    def validate_outcome(self) -> "DeploymentDecisionOutcome":
        if self.decision.architecture_lock_authorized != (self.architecture_lock is not None):
            raise ValueError("architecture lock presence does not match disposition authority")
        if self.architecture_lock is not None:
            if self.architecture_lock.decision_resolution_sha256 != self.decision.resolution_sha256:
                raise ValueError("architecture lock is not bound to the decision resolution")
        return self


def resolve_human_deployment_disposition(
    disposition: HumanDecisionDisposition,
    *,
    decision_authority_identity: str,
    source_reference: str,
    conditions: tuple[str, ...] = (),
    accepted_risks: tuple[str, ...] = (),
    evidence_waivers: tuple[str, ...] = (),
) -> DeploymentDecisionOutcome:
    """Resolve the exact RC2 decision without manufacturing production authority."""

    decision = DeploymentDecisionResolution.create(
        request_id=HOSTED_RC2_REQUEST_ID,
        request_sha256=HOSTED_RC2_REQUEST_SHA256,
        candidate_version=HOSTED_RC2_VERSION,
        candidate_sha256=HOSTED_RC2_SHA256,
        decision_authority="HUMAN",
        decision_authority_identity=decision_authority_identity,
        disposition=disposition,
        decision_state=_DECISION_STATE_BY_DISPOSITION[disposition],
        conditions=conditions,
        accepted_risks=accepted_risks,
        evidence_waivers=evidence_waivers,
        source_reference=source_reference,
        architecture_lock_authorized=disposition
        in {
            HumanDecisionDisposition.APPROVE,
            HumanDecisionDisposition.APPROVE_WITH_CONDITIONS,
        },
        production_execution_authorized=False,
        external_services_budget_usd=0,
    )

    if not decision.architecture_lock_authorized:
        return DeploymentDecisionOutcome(decision=decision, architecture_lock=None)

    architecture_lock = ArchitectureLock.create(
        lock_id="ARCH-LOCK-enki-hosted-1.0-rc2",
        candidate_version=HOSTED_RC2_VERSION,
        candidate_sha256=HOSTED_RC2_SHA256,
        decision_resolution_sha256=decision.resolution_sha256,
        architecture_id=REFERENCE_ARCHITECTURE_ID,
        compute_provider="Cloudflare Workers",
        canonical_store="Neon Postgres",
        object_store="Cloudflare R2",
        optional_services=(),
        responsibility_boundaries=(
            "Cloudflare Workers provides compute and edge runtime only.",
            "Neon Postgres is the canonical structured-data system of record.",
            "Cloudflare R2 stores evidence, artifacts, packages, exports, and backups.",
            "Enki governed application services remain the only authorized canonical mutation path.",
            "Optional Cloudflare or provider services require a separate governed architecture decision.",
        ),
        unresolved_prerequisites=(
            "RC2 hosted architecture validation remains BLOCKED until required hosted TEST evidence is completed or separately waived by human authority.",
            "RC2 production deployment readiness remains BLOCKED until production-control evidence exists.",
            "Sprint 26 CF-NATIVE hosted TEST validation remains blocked on external TEST capabilities.",
            "Sprint 27 CF-NEON-R2 hosted TEST validation remains unexecuted pending external TEST capabilities.",
            "Sprint 28 GCP-NEON-R2 hosted TEST validation remains unexecuted pending external TEST capabilities.",
            "Production credentials, paid external services, and production effects require separate explicit authorization.",
        ),
        rollback_candidate_sha256=HOSTED_RC2_SHA256,
        production_execution_authorized=False,
        external_services_budget_usd=0,
    )
    return DeploymentDecisionOutcome(decision=decision, architecture_lock=architecture_lock)
