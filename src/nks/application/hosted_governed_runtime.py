"""Hosted governed mutation runtime for Enki Sprint 42.

The runtime composes exact hosted identity, context-bound approval, policy,
provenance, physical reservation/journaling/receipts, and interruption recovery.
It remains TEST-only and provider-neutral: no external provider effect is produced by
this module.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_identity import (
    HostedBoundaryContext,
    HostedCredential,
    HostedIdentityService,
)
from nks.application.physical_canonical_persistence import (
    PhysicalMutationAuthorization,
    PhysicalMutationReceipt,
    SQLiteCanonicalPersistence,
)
from nks.enki.temporal_authority import TemporalAuthorityEnvelope
from nks.governance.approvals import (
    ApprovalGrant,
    ApprovalRequest,
    ExecutionContext,
    evaluate_approval,
)
from nks.governance.boundaries import BoundaryAction, HumanBoundaryPolicy


RUNTIME_LEDGER_SQL = """
CREATE TABLE IF NOT EXISTS hosted_runtime_requests (
    request_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    transaction_id TEXT NOT NULL UNIQUE,
    tenant_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    approval_id TEXT NOT NULL,
    identity_decision_sha256 TEXT NOT NULL,
    provenance_sha256 TEXT NOT NULL,
    policy_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    physical_receipt_sha256 TEXT,
    runtime_receipt_sha256 TEXT,
    created_at TEXT NOT NULL,
    committed_at TEXT
);

CREATE TABLE IF NOT EXISTS hosted_runtime_authority_consumptions (
    approval_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    request_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    physical_receipt_sha256 TEXT,
    consumed_at TEXT
);

CREATE TABLE IF NOT EXISTS hosted_runtime_receipts (
    receipt_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    approval_id TEXT NOT NULL,
    identity_decision_sha256 TEXT NOT NULL,
    provenance_sha256 TEXT NOT NULL,
    policy_sha256 TEXT NOT NULL,
    physical_receipt_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    runtime_receipt_sha256 TEXT NOT NULL
);
""".strip()


class HostedRuntimeError(RuntimeError):
    """Generic fail-closed hosted runtime error."""

    def __init__(self, reason_code: str) -> None:
        super().__init__("hosted governed mutation denied")
        self.reason_code = reason_code


class HostedRuntimeInterruption(RuntimeError):
    """Injected TEST interruption used to prove deterministic recovery."""


class HostedRuntimeStatus(StrEnum):
    RESERVED = "RESERVED"
    COMMITTED = "COMMITTED"


class HostedRuntimeFailurePoint(StrEnum):
    BEFORE_PHYSICAL_WRITE = "BEFORE_PHYSICAL_WRITE"
    AFTER_PHYSICAL_COMMIT = "AFTER_PHYSICAL_COMMIT"
    AFTER_RUNTIME_COMMIT = "AFTER_RUNTIME_COMMIT"


class ProvenanceKind(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    REPLAY = "REPLAY"
    REAL_TEST = "REAL_TEST"


class MutationProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provenance_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    kind: ProvenanceKind
    source_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    lineage_sha256: tuple[str, ...] = ()
    execution_context: Literal[ExecutionContext.TEST] = ExecutionContext.TEST
    provenance_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "MutationProvenance":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"provenance_sha256"})
        )
        if self.provenance_sha256 != expected:
            raise ValueError("mutation provenance hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "MutationProvenance":
        payload = {
            "lineage_sha256": (),
            "execution_context": ExecutionContext.TEST,
            **values,
        }
        payload["provenance_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class HostedMutationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str = Field(min_length=1)
    allowed_purposes: tuple[str, ...] = Field(min_length=1)
    allowed_provenance_kinds: tuple[ProvenanceKind, ...] = Field(min_length=1)
    acceptable_approval_authority_classes: tuple[str, ...] = Field(min_length=1)
    production_execution_authorized: Literal[False] = False
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_policy(self) -> "HostedMutationPolicy":
        for values in (
            self.allowed_purposes,
            self.allowed_provenance_kinds,
            self.acceptable_approval_authority_classes,
        ):
            if len(values) != len(set(values)):
                raise ValueError("hosted mutation policy values must be unique")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"policy_sha256"})
        )
        if self.policy_sha256 != expected:
            raise ValueError("hosted mutation policy hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HostedMutationPolicy":
        payload = {"production_execution_authorized": False, **values}
        payload["policy_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class HostedMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    context: HostedBoundaryContext
    envelope: TemporalAuthorityEnvelope
    provenance: MutationProvenance
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    subject_type: str = Field(min_length=1)
    human_policy: HumanBoundaryPolicy | None = None
    requested_at: datetime
    request_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_request(self) -> "HostedMutationRequest":
        if self.context.execution_context != ExecutionContext.TEST:
            raise ValueError("hosted governed runtime request must be TEST-scoped")
        if self.context.subject_id != self.envelope.subject_id:
            raise ValueError("request subject does not match canonical envelope")
        if self.context.domain != self.envelope.domain:
            raise ValueError("request domain does not match canonical envelope")
        if self.provenance.subject_id != self.envelope.subject_id:
            raise ValueError("provenance subject does not match canonical envelope")
        if self.provenance.content_sha256 != self.envelope.content_hash:
            raise ValueError("provenance content does not match canonical envelope")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"request_sha256"})
        )
        if self.request_sha256 != expected:
            raise ValueError("hosted mutation request hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HostedMutationRequest":
        payload = dict(values)
        payload["request_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class HostedRuntimeReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str
    request_id: str
    request_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    transaction_id: str
    approval_id: str
    identity_decision_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    provenance_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    physical_receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    created_at: datetime
    runtime_receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "HostedRuntimeReceipt":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"runtime_receipt_sha256"})
        )
        if self.runtime_receipt_sha256 != expected:
            raise ValueError("hosted runtime receipt hash is invalid")
        return self


class HostedRuntimeReconstruction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    request_sha256: str
    transaction_id: str
    approval_id: str
    status: HostedRuntimeStatus
    identity_decision_sha256: str
    provenance_sha256: str
    policy_sha256: str
    physical_receipt_sha256: str | None
    runtime_receipt_sha256: str | None
    reconstruction_sha256: str

    @model_validator(mode="after")
    def validate_hash(self) -> "HostedRuntimeReconstruction":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"reconstruction_sha256"})
        )
        if self.reconstruction_sha256 != expected:
            raise ValueError("hosted runtime reconstruction hash is invalid")
        return self


class HostedGovernedExecutionRuntime:
    """Durable TEST orchestration over hosted identity and physical persistence."""

    def __init__(
        self,
        persistence: SQLiteCanonicalPersistence,
        identity_service: HostedIdentityService,
    ) -> None:
        self._persistence = persistence
        self._identity_service = identity_service
        self._connection: sqlite3.Connection = persistence.connection
        self._connection.executescript(RUNTIME_LEDGER_SQL)
        self._connection.commit()

    def _request_row(self, request_id: str):
        return self._connection.execute(
            "SELECT * FROM hosted_runtime_requests WHERE request_id = ?",
            (request_id,),
        ).fetchone()

    def _physical_receipt(
        self, tenant_id: str, record_id: str
    ) -> PhysicalMutationReceipt | None:
        row = self._connection.execute(
            "SELECT * FROM physical_receipts WHERE tenant_id = ? AND record_id = ?",
            (tenant_id, record_id),
        ).fetchone()
        if row is None:
            return None
        return PhysicalMutationReceipt(
            receipt_id=row["receipt_id"],
            transaction_id=row["transaction_id"],
            tenant_id=row["tenant_id"],
            record_id=row["record_id"],
            input_sha256=row["input_sha256"],
            output_sha256=row["output_sha256"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            receipt_sha256=row["receipt_sha256"],
        )

    def _load_runtime_receipt(self, request_id: str) -> HostedRuntimeReceipt:
        row = self._connection.execute(
            "SELECT * FROM hosted_runtime_receipts WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        if row is None:
            raise HostedRuntimeError("COMMITTED_REQUEST_RECEIPT_MISSING")
        return HostedRuntimeReceipt(
            receipt_id=row["receipt_id"],
            request_id=row["request_id"],
            request_sha256=row["request_sha256"],
            transaction_id=row["transaction_id"],
            approval_id=row["approval_id"],
            identity_decision_sha256=row["identity_decision_sha256"],
            provenance_sha256=row["provenance_sha256"],
            policy_sha256=row["policy_sha256"],
            physical_receipt_sha256=row["physical_receipt_sha256"],
            created_at=datetime.fromisoformat(row["created_at"]),
            runtime_receipt_sha256=row["runtime_receipt_sha256"],
        )

    def _finalize(
        self,
        request: HostedMutationRequest,
        *,
        approval_id: str,
        identity_decision_sha256: str,
        physical_receipt: PhysicalMutationReceipt,
        now: datetime,
    ) -> HostedRuntimeReceipt:
        receipt_payload = {
            "receipt_id": f"HOSTED-RCP-{request.request_sha256.removeprefix('sha256:')[:24]}",
            "request_id": request.request_id,
            "request_sha256": request.request_sha256,
            "transaction_id": request.transaction_id,
            "approval_id": approval_id,
            "identity_decision_sha256": identity_decision_sha256,
            "provenance_sha256": request.provenance.provenance_sha256,
            "policy_sha256": request.policy_sha256,
            "physical_receipt_sha256": physical_receipt.receipt_sha256,
            "created_at": now,
        }
        receipt = HostedRuntimeReceipt(
            **receipt_payload,
            runtime_receipt_sha256=canonical_sha256(receipt_payload),
        )
        self._connection.execute(
            """
            INSERT OR IGNORE INTO hosted_runtime_receipts(
                receipt_id, request_id, request_sha256, transaction_id, approval_id,
                identity_decision_sha256, provenance_sha256, policy_sha256,
                physical_receipt_sha256, created_at, runtime_receipt_sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt.receipt_id,
                receipt.request_id,
                receipt.request_sha256,
                receipt.transaction_id,
                receipt.approval_id,
                receipt.identity_decision_sha256,
                receipt.provenance_sha256,
                receipt.policy_sha256,
                receipt.physical_receipt_sha256,
                receipt.created_at.isoformat(),
                receipt.runtime_receipt_sha256,
            ),
        )
        self._connection.execute(
            """
            UPDATE hosted_runtime_requests
            SET status = ?, physical_receipt_sha256 = ?, runtime_receipt_sha256 = ?,
                committed_at = ?
            WHERE request_id = ?
            """,
            (
                HostedRuntimeStatus.COMMITTED.value,
                physical_receipt.receipt_sha256,
                receipt.runtime_receipt_sha256,
                now.isoformat(),
                request.request_id,
            ),
        )
        self._connection.execute(
            """
            UPDATE hosted_runtime_authority_consumptions
            SET status = ?, physical_receipt_sha256 = ?, consumed_at = ?
            WHERE approval_id = ?
            """,
            (
                HostedRuntimeStatus.COMMITTED.value,
                physical_receipt.receipt_sha256,
                now.isoformat(),
                approval_id,
            ),
        )
        self._connection.commit()
        return self._load_runtime_receipt(request.request_id)

    def execute(
        self,
        request: HostedMutationRequest,
        *,
        credential: HostedCredential,
        approval: ApprovalGrant,
        policy: HostedMutationPolicy,
        now: datetime,
        failure_point: HostedRuntimeFailurePoint | None = None,
    ) -> HostedRuntimeReceipt:
        """Execute or recover one exact TEST mutation without duplicate effects."""

        existing = self._request_row(request.request_id)
        if existing is not None:
            if existing["request_sha256"] != request.request_sha256:
                raise HostedRuntimeError("DIVERGENT_REQUEST_ID_REUSE")
            if existing["status"] == HostedRuntimeStatus.COMMITTED.value:
                return self._load_runtime_receipt(request.request_id)
            physical = self._physical_receipt(
                request.context.tenant_id, request.envelope.record_id
            )
            if physical is not None:
                if physical.transaction_id != request.transaction_id:
                    raise HostedRuntimeError("PHYSICAL_RECEIPT_TRANSACTION_MISMATCH")
                return self._finalize(
                    request,
                    approval_id=existing["approval_id"],
                    identity_decision_sha256=existing["identity_decision_sha256"],
                    physical_receipt=physical,
                    now=now,
                )

        if request.policy_sha256 != policy.policy_sha256:
            raise HostedRuntimeError("POLICY_HASH_MISMATCH")
        if request.context.purpose not in policy.allowed_purposes:
            raise HostedRuntimeError("PURPOSE_NOT_ALLOWED_BY_POLICY")
        if request.provenance.kind not in policy.allowed_provenance_kinds:
            raise HostedRuntimeError("PROVENANCE_NOT_ALLOWED_BY_POLICY")
        if request.context.execution_context != ExecutionContext.TEST:
            raise HostedRuntimeError("PRODUCTION_EXECUTION_NOT_AUTHORIZED")

        identity = self._identity_service.resolve(
            credential,
            request.context,
            action=BoundaryAction.WRITE,
            now=now,
            subject_type=request.subject_type,
            human_policy=request.human_policy,
        )
        if identity.authorization is None:
            raise HostedRuntimeError(f"IDENTITY_{identity.decision.reason_code}")

        approval_request = ApprovalRequest(
            execution_context=ExecutionContext.TEST,
            action="canonical.write",
            subject_id=request.envelope.subject_id,
            content_sha256=request.envelope.content_hash,
            acceptable_authority_classes=set(
                policy.acceptable_approval_authority_classes
            ),
            transaction_id=request.transaction_id,
            requested_at=request.requested_at,
        )
        evaluation = evaluate_approval(approval, approval_request, now=now)
        if not evaluation.authorized:
            raise HostedRuntimeError("APPROVAL_DENIED")

        consumption = self._connection.execute(
            "SELECT * FROM hosted_runtime_authority_consumptions WHERE approval_id = ?",
            (approval.approval_id,),
        ).fetchone()
        if consumption is not None:
            if (
                consumption["transaction_id"] != request.transaction_id
                or consumption["request_sha256"] != request.request_sha256
            ):
                raise HostedRuntimeError("APPROVAL_ALREADY_CONSUMED_BY_OTHER_REQUEST")
        else:
            self._connection.execute(
                """
                INSERT INTO hosted_runtime_authority_consumptions(
                    approval_id, transaction_id, request_sha256, status,
                    physical_receipt_sha256, consumed_at
                ) VALUES (?, ?, ?, ?, NULL, NULL)
                """,
                (
                    approval.approval_id,
                    request.transaction_id,
                    request.request_sha256,
                    HostedRuntimeStatus.RESERVED.value,
                ),
            )

        if existing is None:
            self._connection.execute(
                """
                INSERT INTO hosted_runtime_requests(
                    request_id, request_sha256, transaction_id, tenant_id, record_id,
                    approval_id, identity_decision_sha256, provenance_sha256,
                    policy_sha256, status, physical_receipt_sha256,
                    runtime_receipt_sha256, created_at, committed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, NULL)
                """,
                (
                    request.request_id,
                    request.request_sha256,
                    request.transaction_id,
                    request.context.tenant_id,
                    request.envelope.record_id,
                    approval.approval_id,
                    identity.decision.event_sha256,
                    request.provenance.provenance_sha256,
                    policy.policy_sha256,
                    HostedRuntimeStatus.RESERVED.value,
                    now.isoformat(),
                ),
            )
        self._connection.commit()

        if failure_point == HostedRuntimeFailurePoint.BEFORE_PHYSICAL_WRITE:
            raise HostedRuntimeInterruption("injected before physical write")

        derived_expiry = approval.expires_at or (now + timedelta(minutes=5))
        physical_authorization = PhysicalMutationAuthorization(
            authorization_id=approval.approval_id,
            tenant_id=request.context.tenant_id,
            record_id=request.envelope.record_id,
            content_hash=request.envelope.content_hash,
            issued_at=approval.issued_at,
            expires_at=derived_expiry,
            revoked_at=approval.revoked_at,
        )
        physical_receipt = self._persistence.write_canonical(
            request.context.tenant_id,
            request.envelope,
            authorization=physical_authorization,
            transaction_id=request.transaction_id,
            now=now,
        )

        if failure_point == HostedRuntimeFailurePoint.AFTER_PHYSICAL_COMMIT:
            raise HostedRuntimeInterruption("injected after physical commit")

        receipt = self._finalize(
            request,
            approval_id=approval.approval_id,
            identity_decision_sha256=identity.decision.event_sha256,
            physical_receipt=physical_receipt,
            now=now,
        )

        if failure_point == HostedRuntimeFailurePoint.AFTER_RUNTIME_COMMIT:
            raise HostedRuntimeInterruption("injected after runtime commit")
        return receipt

    def reconstruct(self, request_id: str) -> HostedRuntimeReconstruction:
        row = self._request_row(request_id)
        if row is None:
            raise HostedRuntimeError("REQUEST_NOT_FOUND")
        payload = {
            "request_id": row["request_id"],
            "request_sha256": row["request_sha256"],
            "transaction_id": row["transaction_id"],
            "approval_id": row["approval_id"],
            "status": HostedRuntimeStatus(row["status"]),
            "identity_decision_sha256": row["identity_decision_sha256"],
            "provenance_sha256": row["provenance_sha256"],
            "policy_sha256": row["policy_sha256"],
            "physical_receipt_sha256": row["physical_receipt_sha256"],
            "runtime_receipt_sha256": row["runtime_receipt_sha256"],
        }
        return HostedRuntimeReconstruction(
            **payload,
            reconstruction_sha256=canonical_sha256(payload),
        )
