# Publication Contract v1

## Purpose

Defines the stable NKS-owned payload for moving approved publication assets from the Nelson Knowledge System into any publishing adapter or external distribution engine.

External systems must adapt to this contract. The NKS core must not adapt its internal model to external vendor assumptions.

## Contract Object

```yaml
contract_version: 1.0
contract_type: publication
package_id:
artifact_id:
source_record_id:
proof_record_id:
narrative_record_id:
visual_package_id:
status:
approval:
  required: true
  approved: false
  approved_by:
  approved_at:
publication:
  title:
  subtitle:
  body_markdown:
  canonical_slug:
  excerpt:
  tags: []
  canonical_url:
visuals:
  hero_image_id:
  signature_diagram_id:
  carousel_ids: []
  quote_card_ids: []
  pinterest_ids: []
distribution:
  channels: []
  schedule:
    publish_now: false
    publish_at:
  adapter_target:
metadata:
  audience:
  pillar:
  risk_level:
  proof_status:
  narrative_arc_status:
  visual_status:
audit:
  created_at:
  updated_at:
  created_by:
  last_validated_by:
```

## Required Validation Before Adapter Dispatch

1. Source lineage recorded.
2. Proof boundary recorded.
3. Narrative arc status at least review-ready.
4. Visual Package created or waived.
5. User approval recorded.
6. Distribution channel selected.
7. Adapter target selected.

## Adapter Responsibility

Adapters may transform this contract into vendor-specific API requests, but may not alter the NKS source, proof, narrative, visual, or approval fields.

## Prohibited Adapter Behavior

- Publishing without approval.
- Dropping proof boundaries.
- Rewriting claims outside the approved body.
- Replacing visual assets with unsupported alternatives.
- Creating platform-only metadata that cannot be reconciled back to the NKS.

## Current Status

Draft v1. Ready for use in integration evaluation and adapter design.