#!/usr/bin/env python3
from pathlib import Path

path = Path('src/nks/application/hosted_retrieval.py')
text = path.read_text(encoding='utf-8')
text = text.replace(
    '    return len(query_tokens.intersection(content_tokens)) / len(query_tokens)\n',
    '    return len(query_tokens.intersection(content_tokens))\n',
    1,
)
old = '''    payload = {
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
'''
new = '''    payload = {
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
'''
if old not in text:
    raise SystemExit('as-of projection payload target not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
