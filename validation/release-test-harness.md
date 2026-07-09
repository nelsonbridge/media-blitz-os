# Release Test Harness

## Purpose

Determine whether a release candidate can be tested externally without allowing publication, social output, or platform distribution to become the objective.

A release is a test of the knowledge manufacturing system.

## Core Principle

A release is permitted when it improves learning, proof, feedback, or capability without distorting trajectory.

## Release Candidate Gates

| Gate | Required Evidence | Pass Condition |
|---|---|---|
| Source Lineage | Source record or source note | Release derives from durable source. |
| Canonical Artifact | Artifact record or cluster record | Release expresses manufactured knowledge, not raw commentary. |
| Proof Boundary | Proof confidence or proof boundary record | Claims are bounded for intended surface. |
| Coherence | Coherence scorecard | Release supports capability growth. |
| Graph Linkage | Graph record or graph backlog entry | Release is connected to corpus relationships. |
| Opportunity Rationale | Opportunity portfolio or release rationale | Release serves identified downstream use. |
| Narrative Readiness | Narrative arc or briefing structure | Audience journey is coherent. |
| Visual Readiness | Visual package, visual plan, or no-visual justification | Visual dependency is resolved. |
| Feedback Capture | Feedback path or manual capture plan | Learning can return to corpus. |
| Trajectory Safety | Anti-regression review | Release does not become objective. |

## Release Readiness States

| State | Meaning |
|---|---|
| Ready to Test | All gates pass or have safe boundaries. |
| Ready with Boundary | Release can proceed only under stated limits. |
| Repair Before Test | One or more capability-critical gates fail. |
| Hold | Release risks trajectory drift or unsupported claims. |
| Retire | Release no longer serves platform learning. |

## Test Record Template

```yaml
release_test_record:
  release_id:
  candidate_path:
  source_lineage:
  canonical_artifact:
  proof_boundary:
  coherence:
  graph_linkage:
  opportunity_rationale:
  narrative_readiness:
  visual_readiness:
  feedback_capture:
  trajectory_safety:
  readiness_state:
  required_repairs:
  approved_test_surface:
```

## Current Candidate: NKS-PUB-000001

| Gate | Status | Notes |
|---|---|---|
| Source Lineage | Pass | Source record exists. |
| Canonical Artifact | Pass | NKS-ART-000001 exists. |
| Proof Boundary | Pass with Boundary | Internal architecture claims; no external performance claims. |
| Coherence | Pass | NKS-COH-000001 scored 93 / 100. |
| Graph Linkage | Pass | NKS-GPH-000001 exists. |
| Opportunity Rationale | Pass | NKS-OPP-000001 exists. |
| Narrative Readiness | Pass | Readiness checklist records full arc. |
| Visual Readiness | Pass | Visual package and generated SVG assets exist. |
| Feedback Capture | Bounded | Manual feedback capture required until feedback contract exists. |
| Trajectory Safety | Pass | Release tests system explanation and does not drive roadmap. |

## Current Candidate State

Ready with Boundary.

Boundary: release may be tested only as a learning loop for proof, feedback, narrative, and system explanation. It must not become the objective or success metric.

## Status

Implemented as release test harness v1.