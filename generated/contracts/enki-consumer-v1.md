# Enki Consumer Contract v1.0

> Generated deterministically from the Sprint 21 stable consumer boundary.

## Supported version

- `1.0`

## Request

Required fields: `request_id`, `contract_version`, `operation`, `boundary`,
`authorization_id`, `idempotency_key`, `payload`, and `pagination`.

Operations are `QUERY` and `COMMAND`. Both are executed through the same governed
application gateway. Repository paths, canonical-record shortcuts, and direct
approval-consumption fields are prohibited.

## Response

Successful responses contain `status=OK`, `data`, `items`, `pagination`, and an
immutable hash-bound `receipt`.

## Errors

Errors use stable codes: `UNSUPPORTED_VERSION`, `AMBIGUOUS_VERSION`,
`INVALID_REQUEST`, `AUTHORITY_DENIED`, `IDEMPOTENCY_CONFLICT`,
`REPOSITORY_SHORTCUT_DENIED`, and `OPERATION_UNAVAILABLE`.

## Pagination

`page_size` is bounded to 1..100. `cursor` is opaque to consumers. Responses expose
`returned` and `next_cursor`.

## Idempotency

An exact retry with the same boundary, operation, idempotency key, and request
fingerprint returns the original response and receipt. Reuse with divergent content
fails closed with `IDEMPOTENCY_CONFLICT`.

## Compatibility

Consumers must send exactly one supported version. Wildcards, version ranges,
comma-separated alternatives, and unknown versions fail closed.
