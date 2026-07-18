"""Governed, deterministic retrieval over Enki temporal-authority records."""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.enki.temporal_authority import TemporalAuthorityEnvelope, TemporalAuthorityTimeline


class RetrievalMode(StrEnum):
    STRUCTURED = "STRUCTURED"
    SEMANTIC = "SEMANTIC"


class RetrievalView(StrEnum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    ALL = "ALL"


class PrivacyClass(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class StaleKnowledgeStateError(RuntimeError):
    """Raised when a request or cursor targets a different canonical timeline."""


class RetrievalBoundaryError(PermissionError):
    """Raised when the request itself lacks a usable governed boundary."""


class GovernedKnowledgeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    envelope: TemporalAuthorityEnvelope
    tenant_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    allowed_audiences: frozenset[str] = Field(min_length=1)
    allowed_purposes: frozenset[str] = Field(min_length=1)
    privacy_class: PrivacyClass
    provenance_ids: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_content_integrity(self) -> "GovernedKnowledgeRecord":
        if self.envelope.content_hash != canonical_sha256(self.content):
            raise ValueError("knowledge record content hash is invalid")
        if len(self.provenance_ids) != len(set(self.provenance_ids)):
            raise ValueError("provenance ids must be unique")
        return self


class GovernedRetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    query: str = ""
    mode: RetrievalMode
    view: RetrievalView
    effective_at: datetime
    authority_at: datetime
    page_size: int = Field(default=50, ge=1, le=100)
    cursor: str | None = None
    expected_timeline_hash: str | None = None


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str
    content: str
    content_hash: str
    provenance_ids: tuple[str, ...]
    score: int
    is_current_authority: bool


class KnowledgeProjection(BaseModel):
    """Noncanonical governed retrieval projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: str
    subject_id: str
    domain: str
    audience: str
    purpose: str
    view: RetrievalView
    mode: RetrievalMode
    timeline_hash: str
    hits: tuple[RetrievalHit, ...]
    next_cursor: str | None
    withheld_count: int
    canonical: bool = False
    projection_hash: str

    @model_validator(mode="after")
    def validate_noncanonical_projection(self) -> "KnowledgeProjection":
        if self.canonical:
            raise ValueError("retrieval projections cannot be canonical")
        payload = self.model_dump(mode="python", exclude={"projection_hash"})
        if self.projection_hash != canonical_sha256(payload):
            raise ValueError("retrieval projection hash is invalid")
        return self


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _score(record: GovernedKnowledgeRecord, request: GovernedRetrievalRequest) -> int:
    if not request.query.strip():
        return 1
    if request.mode == RetrievalMode.STRUCTURED:
        query = request.query.casefold()
        return 1 if query in record.content.casefold() or query in record.envelope.record_id.casefold() else 0
    query_tokens = _tokens(request.query)
    if not query_tokens:
        return 1
    return len(query_tokens & _tokens(record.content))


def _boundary_allows(record: GovernedKnowledgeRecord, request: GovernedRetrievalRequest) -> bool:
    if record.tenant_id != request.tenant_id:
        return False
    if record.envelope.subject_id != request.subject_id:
        return False
    if record.envelope.domain != request.domain:
        return False
    if request.audience not in record.allowed_audiences:
        return False
    if request.purpose not in record.allowed_purposes:
        return False
    if record.privacy_class == PrivacyClass.RESTRICTED:
        return False
    return True


def _parse_cursor(cursor: str | None, timeline_hash: str) -> int:
    if cursor is None:
        return 0
    prefix = f"{timeline_hash}:"
    if not cursor.startswith(prefix):
        raise StaleKnowledgeStateError("retrieval cursor does not match current timeline")
    try:
        offset = int(cursor[len(prefix) :])
    except ValueError as exc:
        raise ValueError("retrieval cursor is invalid") from exc
    if offset < 0:
        raise ValueError("retrieval cursor offset cannot be negative")
    return offset


def retrieve_governed_knowledge(
    records: list[GovernedKnowledgeRecord],
    request: GovernedRetrievalRequest,
) -> KnowledgeProjection:
    """Retrieve only boundary-eligible state and return a noncanonical projection."""

    if not request.tenant_id or not request.subject_id or not request.domain:
        raise RetrievalBoundaryError("tenant, subject, and domain boundaries are required")

    # Apply tenant isolation before temporal reconstruction so another tenant
    # cannot influence authority conflicts, timeline hashes, cursors, or counts.
    relevant = [
        record
        for record in records
        if record.tenant_id == request.tenant_id
        and record.envelope.subject_id == request.subject_id
        and record.envelope.domain == request.domain
    ]
    timeline = TemporalAuthorityTimeline(record.envelope for record in relevant)
    timeline_hash = timeline.timeline_hash
    if request.expected_timeline_hash is not None and request.expected_timeline_hash != timeline_hash:
        raise StaleKnowledgeStateError("expected timeline hash is stale")

    resolution = timeline.resolve(
        effective_at=request.effective_at,
        authority_at=request.authority_at,
    )
    current_ids = set(resolution.current_record_ids)
    historical_ids = set(resolution.historical_record_ids)

    if request.view == RetrievalView.CURRENT:
        eligible_ids = current_ids
    elif request.view == RetrievalView.HISTORICAL:
        eligible_ids = historical_ids
    else:
        eligible_ids = current_ids | historical_ids

    boundary_eligible: list[tuple[GovernedKnowledgeRecord, int]] = []
    withheld_count = 0
    for record in relevant:
        if record.envelope.record_id not in eligible_ids:
            continue
        if not _boundary_allows(record, request):
            withheld_count += 1
            continue
        score = _score(record, request)
        if score > 0:
            boundary_eligible.append((record, score))

    boundary_eligible.sort(key=lambda item: (-item[1], item[0].envelope.record_id))
    offset = _parse_cursor(request.cursor, timeline_hash)
    page = boundary_eligible[offset : offset + request.page_size]
    next_offset = offset + len(page)
    next_cursor = (
        f"{timeline_hash}:{next_offset}"
        if next_offset < len(boundary_eligible)
        else None
    )

    hits = tuple(
        RetrievalHit(
            record_id=record.envelope.record_id,
            content=record.content,
            content_hash=record.envelope.content_hash,
            provenance_ids=record.provenance_ids,
            score=score,
            is_current_authority=record.envelope.record_id in current_ids,
        )
        for record, score in page
    )
    payload = {
        "tenant_id": request.tenant_id,
        "subject_id": request.subject_id,
        "domain": request.domain,
        "audience": request.audience,
        "purpose": request.purpose,
        "view": request.view,
        "mode": request.mode,
        "timeline_hash": timeline_hash,
        "hits": hits,
        "next_cursor": next_cursor,
        "withheld_count": withheld_count,
        "canonical": False,
    }
    return KnowledgeProjection(
        **payload,
        projection_hash=canonical_sha256(payload),
    )
