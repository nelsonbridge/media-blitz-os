# Adapter Contract v1

## Purpose

Defines how replaceable integration modules connect the Nelson Knowledge System to external tools and APIs.

Adapters are implementation modules. They do not own NKS logic.

## Adapter Responsibilities

An adapter must:

1. Accept an NKS contract payload.
2. Validate required fields.
3. Map NKS fields to the external service.
4. Preserve auditability.
5. Return a result object to the NKS.
6. Fail safely without corrupting NKS state.

## Adapter Types

- Publishing adapter
- Visual generation adapter
- Drive synchronization adapter
- Analytics adapter
- Notification adapter
- Search/index adapter
- Approval adapter

## Standard Adapter Input

```yaml
adapter_version: 1.0
adapter_type:
contract_type:
contract_version:
contract_payload:
execution_mode:
  dry_run: true
  publish: false
  schedule: false
security:
  credential_reference:
  scopes_required: []
  user_context:
```

## Standard Adapter Output

```yaml
adapter_result:
  success:
  external_id:
  external_url:
  status:
  error_code:
  error_message:
  retryable:
  audit_log:
  created_at:
```

## Required Failure Behavior

If an external service fails, the adapter must:

1. Return a structured failure.
2. Mark whether failure is retryable.
3. Avoid changing approval state.
4. Avoid deleting local assets.
5. Queue retry or manual fallback where applicable.

## Security Requirements

- Tokens are never stored in publication packages.
- Credentials are referenced by name or environment binding.
- Adapters request minimum practical scopes.
- Publishing adapters must verify approval before dispatch.
- Adapter logs must not expose secrets.

## Current Status

Draft v1. Ready for use in integration evaluation.