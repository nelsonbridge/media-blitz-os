# NKS-GPH-000002 — Executive Value Cluster Graph

```yaml
graph_record:
  graph_id: NKS-GPH-000002
  title: Executive Value / Clarity / Coherence Cluster
  nodes:
    - id: NKS-SRC-000002
      type: Source
      title: Architecture of Inevitable Value Source Cluster
      path: corpus/sources/NKS-SRC-000002-architecture-of-inevitable-value.md
    - id: NKS-ART-000005
      type: Artifact
      title: Clarity Is an Economic Instrument
      path: corpus/artifacts/NKS-ART-000005*
    - id: NKS-ART-000006
      type: Artifact
      title: Coherence Beats Compliance
      path: corpus/artifacts/NKS-ART-000006*
    - id: NKS-ART-000007
      type: Artifact
      title: Capability From Ambiguity
      path: corpus/artifacts/NKS-ART-000007*
    - id: NKS-ART-000008
      type: Artifact
      title: Executive Value Before Resume
      path: corpus/artifacts/NKS-ART-000008*
    - id: NKS-COH-000002
      type: Coherence
      title: Executive Value Cluster Coherence Scorecard
      path: corpus/coherence/NKS-COH-000002-executive-value-cluster.md
    - id: CAP-EXECUTIVE-POSITIONING
      type: Capability
      title: Executive Positioning
      path: roadmap/knowledge-roadmap.md
    - id: CAP-OPPORTUNITY-DEVELOPMENT
      type: Capability
      title: Opportunity Development
      path: architecture/opportunity-engine.md
  edges:
    - from: NKS-ART-000005
      edge: derived_from
      to: NKS-SRC-000002
      rationale: Clarity-as-value claim originates in executive profile source material.
    - from: NKS-ART-000006
      edge: derived_from
      to: NKS-SRC-000002
      rationale: Coherence concept originates in executive operating model source material.
    - from: NKS-ART-000007
      edge: derived_from
      to: NKS-SRC-000002
      rationale: Ambiguity-to-capability model is extracted from executive transformation experience.
    - from: NKS-ART-000008
      edge: derived_from
      to: NKS-SRC-000002
      rationale: Resume-before-signal concept emerges from executive positioning strategy.
    - from: NKS-ART-000005
      edge: supports
      to: NKS-ART-000006
      rationale: Clarity and coherence are mutually reinforcing operating constructs.
    - from: NKS-ART-000007
      edge: supports
      to: NKS-ART-000005
      rationale: Converting ambiguity into capability requires clarity as a value instrument.
    - from: NKS-ART-000008
      edge: packaged_as
      to: CAP-EXECUTIVE-POSITIONING
      rationale: Executive value should be visible before a resume is used as the first signal.
    - from: NKS-COH-000002
      edge: evaluates
      to: NKS-SRC-000002
      rationale: The coherence record evaluates the source cluster and related artifacts.
    - from: NKS-ART-000005
      edge: matures
      to: CAP-OPPORTUNITY-DEVELOPMENT
      rationale: Clarity-as-value can become consulting, briefing, and interview assets.
```

## Status

Seed graph complete.