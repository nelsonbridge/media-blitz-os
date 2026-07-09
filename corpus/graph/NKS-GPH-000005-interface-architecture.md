# NKS-GPH-000005 — Interface Architecture Graph

```yaml
graph_record:
  graph_id: NKS-GPH-000005
  title: Interface Architecture
  nodes:
    - id: ADR-0001
      type: Decision
      title: Own the Contract Layer
      path: architecture/adr/ADR-0001-own-the-contract-layer.md
    - id: ADR-0002
      type: Decision
      title: Hybrid Buy, Modular Design
      path: architecture/adr/ADR-0002-hybrid-buy-modular-design.md
    - id: CONTRACT-PUBLICATION-V1
      type: Contract
      title: Publication Contract v1
      path: contracts/publication-contract-v1.md
    - id: CONTRACT-ADAPTER-V1
      type: Contract
      title: Adapter Contract v1
      path: contracts/adapter-contract-v1.md
    - id: BOUNDARY-INTEGRATION-V1
      type: Governance
      title: Integration Boundary v1
      path: security/integration-security-boundary-v1.md
    - id: EVAL-INTERFACE-MATRIX
      type: Evaluation
      title: Integration Evaluation Matrix
      path: integrations/integration-evaluation-matrix.md
    - id: CAP-INTERFACE-OPTIONALITY
      type: Capability
      title: Interface Optionality
      path: roadmap/knowledge-roadmap.md
  edges:
    - from: ADR-0001
      edge: governs
      to: CONTRACT-PUBLICATION-V1
      rationale: Contract ownership requires NKS-owned publication interfaces.
    - from: ADR-0001
      edge: governs
      to: CONTRACT-ADAPTER-V1
      rationale: Replaceable modules require stable adapter interfaces.
    - from: ADR-0002
      edge: supports
      to: EVAL-INTERFACE-MATRIX
      rationale: Hybrid modular strategy drives evaluation of candidate tools.
    - from: BOUNDARY-INTEGRATION-V1
      edge: governs
      to: CONTRACT-ADAPTER-V1
      rationale: Interface behavior must preserve governance and approval boundaries.
    - from: CONTRACT-PUBLICATION-V1
      edge: enables
      to: CAP-INTERFACE-OPTIONALITY
      rationale: Stable payloads preserve optionality across downstream tools.
    - from: CONTRACT-ADAPTER-V1
      edge: enables
      to: CAP-INTERFACE-OPTIONALITY
      rationale: Adapter standard supports replaceable execution surfaces.
    - from: EVAL-INTERFACE-MATRIX
      edge: supports
      to: CAP-INTERFACE-OPTIONALITY
      rationale: Evaluation matrix identifies candidate modules without making them authoritative.
```

## Status

Seed graph complete.