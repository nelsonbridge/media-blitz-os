#!/usr/bin/env python3
from pathlib import Path

path = Path('src/nks/application/hosted_retrieval.py')
text = path.read_text(encoding='utf-8')
text = text.replace('import json\nimport sqlite3\n', 'import json\nimport re\nimport sqlite3\n')
text = text.replace(
    '    KnowledgeProjection,\n    PrivacyClass,\n',
    '    KnowledgeProjection,\n    PrivacyClass,\n    RetrievalHit,\n    StaleKnowledgeStateError,\n',
)
text = text.replace(
    'from nks.enki.temporal_authority import TemporalAuthorityDisposition, TemporalAuthorityEnvelope\n',
    'from nks.enki.temporal_authority import (\n    TemporalAuthorityConflict,\n    TemporalAuthorityDisposition,\n    TemporalAuthorityEnvelope,\n    TemporalAuthorityTimeline,\n)\n',
)

result_start = text.index('class HostedRetrievalResult(BaseModel):')
result_end = text.index('\n\nclass HostedModelGatewayHandoff', result_start)
result_block = '''class HostedRetrievalResult(BaseModel):
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
'''
text = text[:result_start] + result_block + text[result_end:]

catalog_marker = 'class HostedKnowledgeCatalog:'
helper = r'''

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
    return len(query_tokens.intersection(content_tokens)) / len(query_tokens)


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
        "request_id": request.request_id,
        "tenant_id": request.context.tenant_id,
        "subject_id": request.context.subject_id,
        "domain": request.context.domain,
        "view": RetrievalView.CURRENT,
        "effective_at": request.as_of,
        "authority_at": request.as_of,
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

'''
if catalog_marker not in text:
    raise SystemExit('catalog marker missing')
text = text.replace(catalog_marker, helper + catalog_marker, 1)

service_start = text.index('class HostedRetrievalService:')
retrieve_start = text.index('    def retrieve(', service_start)
retrieve_end = text.index('\n\ndef build_model_gateway_handoff', retrieve_start)
retrieve_block = '''    def retrieve(
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
'''
text = text[:retrieve_start] + retrieve_block + text[retrieve_end:]
path.write_text(text, encoding='utf-8')
