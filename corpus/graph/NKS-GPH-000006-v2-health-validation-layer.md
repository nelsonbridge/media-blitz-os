# NKS-GPH-000006 — V2 Health / Validation Layer Graph

```yaml
graph_record:
  graph_id: NKS-GPH-000006
  title: V2 Health / Validation Layer
  nodes:
    - id: ROADMAP-PLATFORM-CAPABILITY
      type: Roadmap
      title: Platform Capability Roadmap
      path: roadmap/platform-capability-roadmap.md
    - id: METRIC-CORPUS-HEALTH-MODEL
      type: Metric
      title: Corpus Health Model
      path: metrics/corpus-health-model.md
    - id: METRIC-CORPUS-HEALTH-REGISTER
      type: Metric
      title: Corpus Health Register
      path: metrics/corpus-health-register.md
    - id: METRIC-MANUFACTURING
      type: Metric
      title: Manufacturing Metrics Framework
      path: metrics/manufacturing-metrics-framework.md
    - id: VALIDATION-CONTINUOUS
      type: Validation
      title: Continuous Validation Framework
      path: validation/continuous-validation-framework.md
    - id: VALIDATION-PROOF-CONFIDENCE
      type: Validation
      title: Proof Confidence Scorecard
      path: validation/proof-confidence-scorecard.md
    - id: VALIDATION-RELEASE-HARNESS
      type: Validation
      title: Release Test Harness
      path: validation/release-test-harness.md
    - id: OPS-ADAPTIVE-PRIORITIZATION
      type: Operations
      title: Adaptive Prioritization Engine
      path: ops/adaptive-prioritization-engine.md
    - id: GAP-REGISTER
      type: Roadmap
      title: Capability Gap Register
      path: roadmap/capability-gap-register.md
    - id: METRIC-ORPHAN-REPORT
      type: Metric
      title: Orphan Artifact Report
      path: metrics/orphan-artifact-report.md
    - id: METRIC-GRAPH-COVERAGE
      type: Metric
      title: Graph Coverage Matrix
      path: metrics/graph-coverage-matrix.md
    - id: CAP-V2-SELF-ASSESSMENT
      type: Capability
      title: V2 Self-Assessment
      path: roadmap/platform-capability-roadmap.md
  edges:
    - from: ROADMAP-PLATFORM-CAPABILITY
      edge: defines
      to: CAP-V2-SELF-ASSESSMENT
      rationale: Roadmap defines the V2 self-assessment objective.
    - from: METRIC-CORPUS-HEALTH-MODEL
      edge: measures
      to: CAP-V2-SELF-ASSESSMENT
      rationale: Health model defines corpus-level measurement dimensions.
    - from: METRIC-CORPUS-HEALTH-REGISTER
      edge: tracks
      to: METRIC-CORPUS-HEALTH-MODEL
      rationale: Register turns the health model into active state.
    - from: METRIC-MANUFACTURING
      edge: measures
      to: CAP-V2-SELF-ASSESSMENT
      rationale: Manufacturing metrics measure capability growth and reuse.
    - from: VALIDATION-CONTINUOUS
      edge: governs
      to: VALIDATION-RELEASE-HARNESS
      rationale: Continuous validation supplies gates used by release tests.
    - from: VALIDATION-PROOF-CONFIDENCE
      edge: supports
      to: VALIDATION-RELEASE-HARNESS
      rationale: Release candidates depend on proof confidence boundaries.
    - from: OPS-ADAPTIVE-PRIORITIZATION
      edge: uses
      to: GAP-REGISTER
      rationale: Adaptive prioritization selects work from measured capability gaps.
    - from: METRIC-ORPHAN-REPORT
      edge: repairs
      to: METRIC-CORPUS-HEALTH-REGISTER
      rationale: Orphan control improves corpus health.
    - from: METRIC-GRAPH-COVERAGE
      edge: repairs
      to: METRIC-CORPUS-HEALTH-REGISTER
      rationale: Graph coverage improves corpus health and relationship visibility.
    - from: GAP-REGISTER
      edge: advances
      to: CAP-V2-SELF-ASSESSMENT
      rationale: Closing capability gaps matures V2 platform behavior.
```

## Status

Seed graph complete.