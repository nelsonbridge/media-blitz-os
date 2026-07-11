# Social Adapter Contract Verification — 2026-07-10

## Scope

Verified the vendor-neutral social publication and JSON/HTTP transport contracts before implementing TryPost- or Postiz-specific mappings.

## Dispatch Contract Result

Observed locally:

```text
6 checks passed
```

Verified:

- unapproved requests are rejected before adapter invocation;
- dry runs return structured receipts;
- repeated idempotency keys do not cause duplicate adapter calls;
- successful publication receipts include external identifiers and URLs;
- timeouts are classified as retryable and queue manual fallback;
- permission failures are terminal and queue manual fallback;
- possible secret material is rejected from canonical payloads.

## HTTP Transport Result

Observed locally:

```text
9 HTTP adapter checks passed
```

Verified:

- dry runs map payloads without resolving credentials or calling a network transport;
- credentials are resolved only from an external reference;
- live requests carry an idempotency header;
- successful vendor responses normalize to the NKS result object;
- authentication and scope failures become permission errors;
- rate limits and server failures become retryable errors;
- other non-success responses become terminal adapter failures;
- empty credential bindings are rejected;
- credentials do not appear in audit logs.

## Files Verified

- `src/nks/ports/social_publication.py`
- `src/nks/application/social_dispatch.py`
- `src/nks/adapters/social_memory.py`
- `src/nks/adapters/social_http.py`
- `tests/test_social_publication_contract.py`
- `tests/test_social_http_adapter.py`

## Result

PASS — vendor-neutral social adapter boundary.

## Remaining Vendor Validation

TryPost and Postiz still require live schema validation for endpoint paths, authentication, exact request fields, response receipts, idempotency behavior, and rate-limit/error structures.

No external dispatch was attempted. Publication remains gated by rendered-asset review and explicit user approval.
