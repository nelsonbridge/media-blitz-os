# Continuous Validation Framework

## Purpose

Define validation gates that keep the Nelson Knowledge System coherent as it manufactures more knowledge.

## Core Principle

Validation exists to protect trajectory, proof, and reuse — not to slow useful manufacturing.

## Validation Gates

| Gate | Required Check | Failure Result |
|---|---|---|
| Source Lineage | Artifact links to source record. | Park artifact until source is attached. |
| Proof Boundary | Claims are classified and bounded. | Block external use. |
| Coherence Score | Artifact or cluster has scorecard. | Queue coherence review. |
| Graph Linkage | Artifact appears in graph or graph backlog. | Queue graph linking. |
| Opportunity Coverage | Artifact has downstream use evaluation. | Queue opportunity record. |
| Template Compliance | Record follows required template. | Queue repair. |
| Duplicate / Overlap Check | Artifact is not redundant without added value. | Merge, relate, or retire. |
| Orphan Check | No unsupported standalone objects. | Link or park. |
| Trajectory Check | Work supports capability roadmap. | Re-rank or defer. |
| Release Readiness | Release candidate passes proof, narrative, visual, feedback gates. | Do not release. |

## Validation States

| State | Meaning |
|---|---|
| Validated | Passes required checks. |
| Validated with Boundary | Usable under documented constraints. |
| Needs Repair | Useful but incomplete. |
| Parked | Source retained; not manufactured yet. |
| Retired | No longer useful or superseded. |
| Blocked | Cannot proceed without source, approval, or external dependency. |

## Validation Record Format

```yaml
validation_record:
  target_id:
  target_path:
  source_lineage: pass|fail|bounded
  proof_boundary: pass|fail|bounded
  coherence_score: pass|fail|bounded
  graph_linkage: pass|fail|bounded
  opportunity_coverage: pass|fail|bounded
  template_compliance: pass|fail|bounded
  duplicate_check: pass|fail|bounded
  orphan_check: pass|fail|bounded
  trajectory_check: pass|fail|bounded
  release_readiness: pass|fail|bounded
  validation_state:
  repair_actions:
```

## Release Test Harness

A release is a test of the knowledge manufacturing system.

Before release, verify:

1. The release is downstream of a durable artifact.
2. The release does not become the objective.
3. Feedback can enrich the corpus.
4. Proof boundaries are preserved.
5. The release tests a platform capability.
6. The release can be paused without harming the roadmap.

## Initial Priority

Build validators in this order:

1. Source lineage validator.
2. Proof boundary validator.
3. Graph coverage validator.
4. Opportunity coverage validator.
5. Release readiness validator.
6. Corpus health validator.

## Status

Implemented as continuous validation framework v1.