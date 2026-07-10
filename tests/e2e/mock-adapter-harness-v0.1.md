# Mock Adapter E2E Harness v0.1

## Purpose

Run non-live end-to-end tests for NKS packages without external publication, platform credentials, or live distribution.

## Scope

This harness validates the closest available end-to-end path:

```text
Source
→ Artifact
→ Proof Boundary
→ Narrative
→ Visual Package / Visual Requirement
→ Publication Contract Shape
→ Mock Adapter Mapping
→ Feedback Stub
→ Corpus Enrichment Stub
```

## Non-Live Guarantee

This harness does not publish, schedule, call platform APIs, send notifications, or create external posts.

## Pass Criteria

A test package passes v0.1 if it has:

1. publication package,
2. draft path,
3. source artifact,
4. proof posture or proof boundary,
5. narrative status,
6. visual package or explicit visual gap,
7. mock adapter payload,
8. feedback stub,
9. enrichment action.

## Result Categories

- `PASS`: enough structure exists for non-live package traversal.
- `PASS_WITH_GAPS`: path is testable, but gaps remain before live use.
- `FAIL`: required internal package path cannot be traversed.

## Mock Adapter Payload

```yaml
mock_adapter:
  mode: dry_run
  external_calls: false
  target: mock-distribution-layer
  validates:
    - package_identity
    - source_linkage
    - proof_boundary
    - narrative_state
    - visual_state
    - output_mapping
    - feedback_stub
    - enrichment_stub
```

## Current Test Set

- NKS-E2E-000001: NKS-PUB-000001
- NKS-E2E-000002: NKS-PUB-000002
- NKS-E2E-000003: NKS-PUB-000003
- NKS-E2E-000004: NKS-PUB-000004
- NKS-E2E-000005: NKS-PUB-000005
- NKS-E2E-000006: NKS-PUB-000006

## Status

Implemented for dry-run test records.