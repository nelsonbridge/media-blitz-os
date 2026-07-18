#!/usr/bin/env python3
from pathlib import Path

path = Path('src/nks/application/hosted_retrieval.py')
text = path.read_text(encoding='utf-8')
old = '            required_context={request.context.purpose, request.context.audience},\n'
new = '''            required_context={
                request.context.purpose,
                request.context.audience,
                ModelUseAudience.INTERNAL_MODEL.value,
            },
'''
if old not in text:
    raise SystemExit('gateway required_context target not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
