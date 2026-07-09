# NKS-GPH-000007 — Transport Language Layer Graph

```yaml
graph_record:
  graph_id: NKS-GPH-000007
  title: Transport Language Layer
  nodes:
    - id: ARCH-TRANSPORT-LANGUAGE
      type: Architecture
      title: Transport Language Layer
      path: architecture/transport-language-layer.md
    - id: SCHEMA-TRANSPORT-PROFILE
      type: Schema
      title: Transport Language Profile Schema
      path: schemas/transport-language-profile-schema.md
    - id: PROFILE-GITHUB-TRANSPORT
      type: Profile
      title: GitHub Transport Language Profile
      path: adapters/language-profiles/github-transport-language-profile.md
    - id: VALIDATION-TRANSPORT-LANGUAGE
      type: Validation
      title: Transport Language Validation Checklist
      path: validation/transport-language-validation-checklist.md
    - id: CAP-CONNECTOR-RESILIENCE
      type: Capability
      title: Connector Resilience
      path: roadmap/platform-capability-roadmap.md
  edges:
    - from: ARCH-TRANSPORT-LANGUAGE
      edge: defines
      to: CAP-CONNECTOR-RESILIENCE
      rationale: Transport language preserves canonical meaning across target surfaces.
    - from: SCHEMA-TRANSPORT-PROFILE
      edge: validates
      to: PROFILE-GITHUB-TRANSPORT
      rationale: Profile schema defines required profile structure.
    - from: PROFILE-GITHUB-TRANSPORT
      edge: supports
      to: CAP-CONNECTOR-RESILIENCE
      rationale: GitHub profile reduces connector friction without rewriting the corpus.
    - from: VALIDATION-TRANSPORT-LANGUAGE
      edge: governs
      to: PROFILE-GITHUB-TRANSPORT
      rationale: Validation checklist confirms surface wording preserves meaning.
    - from: ARCH-TRANSPORT-LANGUAGE
      edge: supports
      to: VALIDATION-TRANSPORT-LANGUAGE
      rationale: Architecture layer defines what the validation checklist enforces.
```

## Status

Seed graph complete.