# NKS-GPH-000004 — Visual Knowledge System Graph

```yaml
graph_record:
  graph_id: NKS-GPH-000004
  title: Visual Knowledge System
  nodes:
    - id: GOV-VISUAL-KNOWLEDGE
      type: Governance
      title: Visual Knowledge System Governance
      path: governance/visual-knowledge-system.md
    - id: GOV-DIAGRAM-LANGUAGE
      type: Governance
      title: Diagram Language Standard
      path: governance/diagram-language-standard.md
    - id: SCHEMA-VISUAL-ARTIFACT
      type: Schema
      title: Visual Artifact Schema
      path: schemas/visual-artifact-schema.md
    - id: NKS-VIS-000001
      type: Visual
      title: Foundational Visual Package
      path: visuals/packages/NKS-VIS-000001.md
    - id: NKS-DGM-000001
      type: Visual
      title: Knowledge Manufacturing Loop
      path: visuals/generated/NKS-DGM-000001-knowledge-manufacturing-loop.svg
    - id: NKS-HRO-000001
      type: Visual
      title: Knowledge System Hero
      path: visuals/generated/NKS-HRO-000001-knowledge-system-hero.svg
    - id: CAP-VISUAL-KNOWLEDGE
      type: Capability
      title: Visual Knowledge
      path: roadmap/knowledge-roadmap.md
  edges:
    - from: GOV-VISUAL-KNOWLEDGE
      edge: governs
      to: NKS-VIS-000001
      rationale: Visual packages are first-class knowledge artifacts governed by visual knowledge rules.
    - from: GOV-DIAGRAM-LANGUAGE
      edge: governs
      to: NKS-DGM-000001
      rationale: Diagram language standard defines how diagrams express system relationships.
    - from: SCHEMA-VISUAL-ARTIFACT
      edge: validates
      to: NKS-VIS-000001
      rationale: Visual artifact schema defines required metadata and state.
    - from: NKS-DGM-000001
      edge: represents
      to: CAP-VISUAL-KNOWLEDGE
      rationale: Signature diagram demonstrates visual knowledge as a reusable capability.
    - from: NKS-HRO-000001
      edge: supports
      to: NKS-VIS-000001
      rationale: Hero image supports the foundational visual package.
    - from: NKS-VIS-000001
      edge: matures
      to: CAP-VISUAL-KNOWLEDGE
      rationale: First generated visual package increases visual capability maturity.
```

## Status

Seed graph complete.