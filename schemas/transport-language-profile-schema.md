# Transport Language Profile Schema

## Purpose

Define the required structure for connector-specific language profiles.

## Schema

```yaml
transport_language_profile:
  profile_id:
  target_surface:
  owner:
  purpose:
  canonical_policy:
    preserve_meaning: true
    preserve_source_lineage: true
    preserve_proof_boundary: true
    preserve_graph_identity: true
  preferred_terms:
    - canonical_concept:
      transport_label:
      applies_to:
        - filename
        - heading
        - summary
        - commit_message
      preserved_meaning:
  avoid_terms:
    - term_pattern:
      reason:
      replacement:
      applies_to:
        - filename
        - payload
        - summary
  review_rules:
    - rule:
      action:
  validation:
    profile_state:
    last_reviewed:
    next_review:
```

## Required Fields

| Field | Required | Notes |
|---|---|---|
| profile_id | Yes | Stable identifier. |
| target_surface | Yes | Destination or connector. |
| canonical_policy | Yes | Must preserve semantic identity. |
| preferred_terms | Yes | Terms to use in transport. |
| avoid_terms | Yes | Terms or patterns likely to cause friction. |
| review_rules | Yes | How the profile is applied. |
| validation | Yes | Review state. |

## Validation Rules

1. A transport label may simplify wording but must not change meaning.
2. A replacement may reduce friction but must not erase proof boundaries.
3. A connector profile cannot override canonical records.
4. A profile must state where it applies.
5. If meaning would be distorted, the write must be split, delayed, or manually reviewed.

## Status

Implemented as schema v1.