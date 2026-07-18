"""Hosted governed retrieval and model-gateway handoff for Enki Sprint 43.

The service applies hosted identity before querying a tenant-scoped content catalog,
materializes only rows that already have a matching physical canonical record, and
then delegates temporal, privacy, purpose, audience, structured, semantic, pagination,
and stale-state semantics to the existing deterministic governed retrieval engine.
Model access is built only from the resulting noncanonical projection and continues
through the provider-neutral model gateway.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.enki_model_use_policy import model_use_context_sha256
from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_identity import (
    HostedBoundaryContext,
    HostedCredential,
    HostedIdentityError,
    HostedIdentityService,
)
from nks.application.physical_canonical_persistence import SQLiteCanonicalPersistence
from nks.enki.contracts import ConfidenceAssertion, ConfidenceLevel, SubjectRef
from nks.enki.governed_retrieval import (
    GovernedKnowledgeRecord,
    GovernedRetrievalRequest,
    KnowledgeProjection,
    PrivacyClass,
    RetrievalHit,
    StaleKnowledgeStateError,
    RetrievalMode,
    RetrievalView,
    retrieve_governed_knowledge,
)
from nks.enki.model_gateway import ModelGatewayExecutionRequest
from nks.enki.model_use_contracts import (
    EnkiModelUseDirective,
    EnkiModelUseItem,
    EnkiModelUseRequest,
    ModelUseAudience,
    ModelUseConsentState,
    ModelUseDirectiveAction,
    ModelUseItemKind,
    ModelUseSensitivity,
    ModelUseTemporalState,
)
from nks.enki.temporal_authority import (
    TemporalAuthorityConflict,
    TemporalAuthorityDisposition,
    TemporalAuthorityEnvelope,
    TemporalAuthorityTimeline,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryAction, HumanBoundaryPolicy


HOSTED_RETRIEVAL_CATALOG_SQL = """
CREATE TABLE IF NOT EXISTS hosted_knowledge_content (
    tenant_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    allowed_audiences_json TEXT NOT NULL,
    allowed_purposes_json TEXT NOT NULL,
    privacy_class TEXT NOT NULL,
    provenance_ids_json TEXT NOT NULL,
    metadata_sha256 TEXT NOT NULL,
    PRIMARY KEY (tenant_id, record_id),
    FOREIGN KEY (tenant_id, record_id)
      REFERENCES canonical_records(tenant_id, record_id)
);

CREATE INDEX IF NOT EXISTS idx_hosted_knowledge_tenant_record
ON hosted_knowledge_content(tenant_id, record_id);
""".strip()


class HostedRetrievalView(StrEnum):
    CURRENT_AUTHORITY = "CURRENT_AUTHORITY"
    HISTORICAL = "HISTORICAL"
    AS_OF = "AS_OF"


class HostedRetrievalError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__("hosted retrieval denied")
        self.reason_code = reason_code


class HostedCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    allowed_audiences: tuple[str, ...] = Field(min_length=1)
    allowed_purposes: tuple[str, ...] = Field(min_length=1)
    privacy_class: PrivacyClass
    provenance_ids: tuple[str, ...] = Field(min_length=1)
    metadata_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_entry(self) -> "HostedCatalogEntry":
        if len(self.allowed_audiences) != len(set(self.allowed_audiences)):
            raise ValueError("allowed audiences must be unique")
        if len(self.allowed_purposes) != len(set(self.allowed_purposes)):
            raise ValueError("allowed purposes must be unique")
        if len(self.provenance_ids) != len(set(self.provenance_ids)):
            raise ValueError("provenance identifiers must be unique")
        expected = canonical_sha256(
            {
                "tenant_id": self.tenant_id,
                "record_id": self.record_id,
                "content_hash": canonical_sha256(self.content),
                "allowed_audiences": self.allowed_audiences,
                "allowed_purposes": self.allowed_purposes,
                "privacy_class": self.privacy_class,
                "provenance_ids": self.provenance_ids,
            }
        )
        if self.metadata_sha256 != expected:
            raise ValueError("hosted catalog metadata hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HostedCatalogEntry":
        payload = dict(values)
        metadata_payload = {
            "tenant_id": payload["tenant_id"],
            "record_id": payload["record_id"],
            "content_hash": canonical_sha256(payload["content"]),
            "allowed_audiences": payload["allowed_audiences"],
            "allowed_purposes": payload["allowed_purposes"],
            "privacy_class": payload["privacy_class"],
            "provenance_ids": payload["provenance_ids"],
        }
        payload["metadata_sha256"] = canonical_sha256(metadata_payload)
        return cls(**payload)


class HostedRetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    context: HostedBoundaryContext
    view: HostedRetrievalView
    mode: RetrievalMode
    query: str = ""
    effective_at: datetime | None = None
    authority_at: datetime | None = None
    as_of: datetime | None = None
    page_size: int = Field(default=50, ge=1, le=100)
    cursor: str | None = None
    expected_timeline_hash: str | None = None
    requested_at: datetime

    @model_validator(mode="after")
    def validate_times(self) -> "HostedRetrievalRequest":
        if self.context.execution_context != ExecutionContext.TEST:
            raise ValueError("hosted retrieval request must be TEST-scoped")
        if self.view == HostedRetrievalView.AS_OF:
            if self.as_of is None:
                raise ValueError("AS_OF retrieval requires an explicit as_of time")
            if self.effective_at is not None or self.authority_at is not None:
                raise ValueError("AS_OF retrieval cannot mix explicit effective/authority times")
        else:
            if self.as_of is not None:
                raise ValueError("as_of is valid only for AS_OF retrieval")
            if self.effective_at is None or self.authority_at is None:
                raise ValueError("current and historical retrieval require effective and authority times")
        return self


class HostedRetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    identity_decision_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    identity_scope_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    projection: KnowledgeProjection
    catalog_scope_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    result_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_result(self) -> "HostedRetrievalResult":
        if self.projection.canonical:
            raise ValueError("hosted retrieval projection cannot be canonical")
        expected = canonical_sha256(
            self.model_dump(
                mode="python",
                exclude={"result_sha256", "identity_decision_sha256"},
            )
        )
        if self.result_sha256 != expected:
            raise ValueError("hosted retrieval result hash is invalid")
        return self


class HostedModelGatewayHandoff(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    projection_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    gateway_request: ModelGatewayExecutionRequest
    canonical_mutation_authorized: Literal[False] = False
    direct_provider_dispatch_authorized: Literal[False] = False
    handoff_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_handoff(self) -> "HostedModelGatewayHandoff":
        if self.gateway_request.model_use_request.execution_context != ExecutionContext.TEST:
            raise ValueError("hosted retrieval model handoff must remain TEST-scoped")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"handoff_sha256"})
        )
        if self.handoff_sha256 != expected:
            raise ValueError("hosted retrieval model handoff hash is invalid")
        return self




def _as_of_boundary_allows(
    record: GovernedKnowledgeRecord,
    request: HostedRetrievalRequest,
) -> bool:
    return (
        request.context.audience in record.allowed_audiences
        and request.context.purpose in record.allowed_purposes
        and record.privacy_class != PrivacyClass.RESTRICTED
    )


def _as_of_score(record: GovernedKnowledgeRecord, request: HostedRetrievalRequest) -> float:
    query = request.query.strip().lower()
    if not query:
        return 1.0
    content = record.content.lower()
    if request.mode == RetrievalMode.STRUCTURED:
        return 1.0 if query in content else 0.0
    query_tokens = set(re.findall(r"[a-z0-9]+", query))
    content_tokens = set(re.findall(r"[a-z0-9]+", content))
    if not query_tokens:
        return 0.0
    return len(query_tokens.intersection(content_tokens))


def _as_of_cursor_start(cursor: str | None, timeline_hash: str) -> int:
    if cursor is None:
        return 0
    try:
        cursor_hash, offset_text = cursor.split(":", 1)
        offset = int(offset_text)
    except (ValueError, AttributeError) as exc:
        raise StaleKnowledgeStateError("invalid retrieval cursor") from exc
    if cursor_hash != timeline_hash or offset < 0:
        raise StaleKnowledgeStateError("retrieval cursor is stale")
    return offset


def _retrieve_as_of_knowledge(
    records: tuple[GovernedKnowledgeRecord, ...],
    request: HostedRetrievalRequest,
) -> KnowledgeProjection:
    assert request.as_of is not None
    timeline = TemporalAuthorityTimeline(record.envelope for record in records)
    timeline_hash = timeline.timeline_hash
    if (
        request.expected_timeline_hash is not None
        and request.expected_timeline_hash != timeline_hash
    ):
        raise StaleKnowledgeStateError("retrieval state is stale")

    by_authority: dict[tuple[str, str, str], list[GovernedKnowledgeRecord]] = {}
    for record in records:
        envelope = record.envelope
        authoritative_then = envelope.authority_valid_from <= request.as_of and (
            envelope.authority_valid_to is None
            or request.as_of < envelope.authority_valid_to
        )
        if envelope.is_effective_at(request.as_of) and authoritative_then:
            by_authority.setdefault(envelope.authority_key, []).append(record)

    selected_ids: set[str] = set()
    for authority_key, candidates in by_authority.items():
        if len(candidates) > 1:
            raise TemporalAuthorityConflict(
                f"ambiguous historical authority for {authority_key}: "
                f"{sorted(item.envelope.record_id for item in candidates)}"
            )
        selected_ids.add(candidates[0].envelope.record_id)

    withheld_count = 0
    scored: list[tuple[float, GovernedKnowledgeRecord]] = []
    for record in records:
        if record.envelope.record_id not in selected_ids:
            continue
        if not _as_of_boundary_allows(record, request):
            withheld_count += 1
            continue
        score = _as_of_score(record, request)
        if request.query.strip() and score <= 0.0:
            continue
        scored.append((score, record))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1].envelope.recorded_at,
            item[1].envelope.record_id,
        )
    )
    start = _as_of_cursor_start(request.cursor, timeline_hash)
    end = start + request.page_size
    page = scored[start:end]
    next_cursor = f"{timeline_hash}:{end}" if end < len(scored) else None
    hits = tuple(
        RetrievalHit(
            record_id=record.envelope.record_id,
            content=record.content,
            content_hash=record.envelope.content_hash,
            is_current_authority=True,
            provenance_ids=record.provenance_ids,
            score=score,
        )
        for score, record in page
    )
    payload = {
        "tenant_id": request.context.tenant_id,
        "subject_id": request.context.subject_id,
        "domain": request.context.domain,
        "audience": request.context.audience,
        "purpose": request.context.purpose,
        "view": RetrievalView.HISTORICAL,
        "mode": request.mode,
        "timeline_hash": timeline_hash,
        "hits": hits,
        "withheld_count": withheld_count,
        "next_cursor": next_cursor,
        "canonical": False,
    }
    return KnowledgeProjection(
        **payload,
        projection_hash=canonical_sha256(payload),
    )

class HostedKnowledgeCatalog:
    """Tenant-scoped noncanonical content metadata joined to physical canonical rows."""

    def __init__(self, persistence: SQLiteCanonicalPersistence) -> None:
        self._persistence = persistence
        self._connection: sqlite3.Connection = persistence.connection
        self._connection.executescript(HOSTED_RETRIEVAL_CATALOG_SQL)
        self._connection.commit()

    def register(self, entry: HostedCatalogEntry) -> None:
        canonical = self._connection.execute(
            """
            SELECT content_hash FROM canonical_records
            WHERE tenant_id = ? AND record_id = ?
            """,
            (entry.tenant_id, entry.record_id),
        ).fetchone()
        if canonical is None:
            raise HostedRetrievalError("CANONICAL_RECORD_NOT_FOUND")
        content_hash = canonical_sha256(entry.content)
        if canonical["content_hash"] != content_hash:
            raise HostedRetrievalError("CATALOG_CONTENT_HASH_MISMATCH")
        self._connection.execute(
            """
            INSERT OR REPLACE INTO hosted_knowledge_content(
                tenant_id, record_id, content, content_hash,
                allowed_audiences_json, allowed_purposes_json,
                privacy_class, provenance_ids_json, metadata_sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.tenant_id,
                entry.record_id,
                entry.content,
                content_hash,
                json.dumps(sorted(entry.allowed_audiences), separators=(",", ":")),
                json.dumps(sorted(entry.allowed_purposes), separators=(",", ":")),
                entry.privacy_class.value,
                json.dumps(list(entry.provenance_ids), separators=(",", ":")),
                entry.metadata_sha256,
            ),
        )
        self._connection.commit()

    @staticmethod
    def _time(value: str | None) -> datetime | None:
        return None if value is None else datetime.fromisoformat(value)

    def scoped_records(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        domain: str,
    ) -> tuple[GovernedKnowledgeRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT c.*, k.content, k.allowed_audiences_json,
                   k.allowed_purposes_json, k.privacy_class,
                   k.provenance_ids_json
            FROM canonical_records c
            JOIN hosted_knowledge_content k
              ON k.tenant_id = c.tenant_id AND k.record_id = c.record_id
            WHERE c.tenant_id = ? AND c.subject_id = ? AND c.domain = ?
            ORDER BY c.recorded_at, c.record_id
            """,
            (tenant_id, subject_id, domain),
        ).fetchall()
        records: list[GovernedKnowledgeRecord] = []
        for row in rows:
            envelope = TemporalAuthorityEnvelope(
                record_id=row["record_id"],
                subject_id=row["subject_id"],
                domain=row["domain"],
                authority_class=row["authority_class"],
                content_hash=row["content_hash"],
                schema_version=row["schema_version"],
                recorded_at=self._time(row["recorded_at"]),
                effective_from=self._time(row["effective_from"]),
                effective_to=self._time(row["effective_to"]),
                authority_valid_from=self._time(row["authority_valid_from"]),
                authority_valid_to=self._time(row["authority_valid_to"]),
                superseded_at=self._time(row["superseded_at"]),
                revoked_at=self._time(row["revoked_at"]),
                consumed_at=self._time(row["consumed_at"]),
                retracted_at=self._time(row["retracted_at"]),
                supersedes_record_id=row["supersedes_record_id"],
                lineage_parent_ids=tuple(json.loads(row["lineage_parent_ids_json"])),
                disposition=TemporalAuthorityDisposition(row["disposition"]),
            )
            records.append(
                GovernedKnowledgeRecord(
                    envelope=envelope,
                    tenant_id=row["tenant_id"],
                    content=row["content"],
                    allowed_audiences=frozenset(json.loads(row["allowed_audiences_json"])),
                    allowed_purposes=frozenset(json.loads(row["allowed_purposes_json"])),
                    privacy_class=PrivacyClass(row["privacy_class"]),
                    provenance_ids=tuple(json.loads(row["provenance_ids_json"])),
                )
            )
        return tuple(records)


class HostedRetrievalService:
    def __init__(
        self,
        persistence: SQLiteCanonicalPersistence,
        identity_service: HostedIdentityService,
    ) -> None:
        self._persistence = persistence
        self._identity_service = identity_service
        self.catalog = HostedKnowledgeCatalog(persistence)

    def retrieve(
        self,
        request: HostedRetrievalRequest,
        *,
        credential: HostedCredential,
        subject_type: str = "ORGANIZATION",
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> HostedRetrievalResult:
        try:
            authorization = self._identity_service.require(
                credential,
                request.context,
                action=BoundaryAction.READ,
                now=request.requested_at,
                subject_type=subject_type,
                human_policy=human_policy,
            )
        except HostedIdentityError as exc:
            raise HostedRetrievalError(f"IDENTITY_{exc.reason_code}") from exc
        if authorization.boundary != request.context.boundary:
            raise HostedRetrievalError("IDENTITY_BOUNDARY_MISMATCH")

        records = self.catalog.scoped_records(
            tenant_id=request.context.tenant_id,
            subject_id=request.context.subject_id,
            domain=request.context.domain,
        )
        if request.view == HostedRetrievalView.AS_OF:
            projection = _retrieve_as_of_knowledge(records, request)
        else:
            retrieval_view = (
                RetrievalView.CURRENT
                if request.view == HostedRetrievalView.CURRENT_AUTHORITY
                else RetrievalView.HISTORICAL
            )
            assert request.effective_at is not None and request.authority_at is not None
            projection = retrieve_governed_knowledge(
                list(records),
                GovernedRetrievalRequest(
                    tenant_id=request.context.tenant_id,
                    subject_id=request.context.subject_id,
                    domain=request.context.domain,
                    audience=request.context.audience,
                    purpose=request.context.purpose,
                    query=request.query,
                    mode=request.mode,
                    view=retrieval_view,
                    effective_at=request.effective_at,
                    authority_at=request.authority_at,
                    page_size=request.page_size,
                    cursor=request.cursor,
                    expected_timeline_hash=request.expected_timeline_hash,
                ),
            )
        identity_decision = self._identity_service.decisions[-1]
        identity_scope_sha256 = canonical_sha256(
            {
                "credential_sha256": credential.credential_sha256,
                "context_sha256": request.context.context_sha256,
                "action": BoundaryAction.READ,
            }
        )
        payload = {
            "request_id": request.request_id,
            "identity_decision_sha256": identity_decision.event_sha256,
            "identity_scope_sha256": identity_scope_sha256,
            "projection": projection,
            "catalog_scope_sha256": canonical_sha256(
                {
                    "tenant_id": request.context.tenant_id,
                    "subject_id": request.context.subject_id,
                    "domain": request.context.domain,
                    "record_ids": [record.envelope.record_id for record in records],
                }
            ),
        }
        stable_payload = dict(payload)
        stable_payload.pop("identity_decision_sha256")
        return HostedRetrievalResult(
            **payload,
            result_sha256=canonical_sha256(stable_payload),
        )


def build_model_gateway_handoff(
    result: HostedRetrievalResult,
    request: HostedRetrievalRequest,
    *,
    subject_type: str,
    issued_by: str,
    authority_class: str,
) -> HostedModelGatewayHandoff:
    """Convert only filtered projection hits into the provider-neutral model gateway."""

    if result.request_id != request.request_id:
        raise HostedRetrievalError("RESULT_REQUEST_MISMATCH")
    subject = SubjectRef(
        subject_id=request.context.subject_id,
        subject_type=subject_type,
    )
    items: list[EnkiModelUseItem] = []
    directives: list[EnkiModelUseDirective] = []
    temporal_state = (
        ModelUseTemporalState.HISTORICAL
        if request.view == HostedRetrievalView.HISTORICAL
        else ModelUseTemporalState.CURRENT
    )
    for index, hit in enumerate(result.projection.hits, start=1):
        item = EnkiModelUseItem(
            item_id=f"RETRIEVAL-{hit.record_id}",
            item_kind=ModelUseItemKind.FINDING,
            subject=subject,
            domain=request.context.domain,
            content_sha256=hit.content_hash,
            context=[request.context.purpose, request.context.audience],
            temporal_state=temporal_state,
            confidence=ConfidenceAssertion(
                level=ConfidenceLevel.HIGH,
                rationale="Deterministic governed hosted retrieval projection.",
                evidence_ids=list(hit.provenance_ids),
            ),
            sensitivity=ModelUseSensitivity.INTERNAL,
            consent_state=ModelUseConsentState.GRANTED,
            allowed_purposes={request.context.purpose},
            provenance_classification="GOVERNED_RETRIEVAL/TEST",
            metadata={
                "projection_sha256": result.projection.projection_hash,
                "retrieval_record_id": hit.record_id,
                "is_current_authority": hit.is_current_authority,
            },
        )
        directive = EnkiModelUseDirective(
            directive_id=f"RETRIEVAL-DIR-{index:04d}-{hit.record_id}",
            action=ModelUseDirectiveAction.INCLUDE,
            item_id=item.item_id,
            item_kind=item.item_kind,
            subject=subject,
            domain=request.context.domain,
            purpose=request.context.purpose,
            audience=ModelUseAudience.INTERNAL_MODEL,
            required_context={
                request.context.purpose,
                request.context.audience,
                ModelUseAudience.INTERNAL_MODEL.value,
            },
            rationale="Include only the exact governed retrieval hit in TEST model use.",
            issued_by=issued_by,
            authority_class=authority_class,
            issued_at=request.requested_at,
            metadata={"projection_sha256": result.projection.projection_hash},
        )
        items.append(item)
        directives.append(directive)

    model_request = EnkiModelUseRequest(
        package_id=f"RETRIEVAL-PKG-{request.request_id}",
        subject=subject,
        domain=request.context.domain,
        purpose=request.context.purpose,
        audience=ModelUseAudience.INTERNAL_MODEL,
        context={request.context.purpose, request.context.audience},
        execution_context=ExecutionContext.TEST,
        items=items,
        directives=directives,
        requested_at=request.requested_at,
        package_version="enki-hosted-retrieval-model-use/v1",
        metadata={
            "projection_sha256": result.projection.projection_hash,
            "retrieval_result_sha256": result.result_sha256,
        },
    )
    gateway_request = ModelGatewayExecutionRequest(
        gateway_request_id=f"GW-{request.request_id}",
        model_use_request=model_request,
        expected_context_sha256=model_use_context_sha256(model_request),
        requested_at=request.requested_at,
    )
    payload = {
        "projection_sha256": result.projection.projection_hash,
        "gateway_request": gateway_request,
        "canonical_mutation_authorized": False,
        "direct_provider_dispatch_authorized": False,
    }
    return HostedModelGatewayHandoff(
        **payload,
        handoff_sha256=canonical_sha256(payload),
    )
