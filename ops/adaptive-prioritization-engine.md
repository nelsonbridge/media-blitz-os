# Adaptive Prioritization Engine

## Purpose

Convert static backlog execution into gap-driven platform improvement.

The engine selects work based on the current health of the Nelson Knowledge System, not on the nearest visible output.

## Core Principle

The next action should close the highest-value capability gap.

## Inputs

| Input | Source |
|---|---|
| Capability Roadmap | roadmap/platform-capability-roadmap.md |
| Corpus Health Score | metrics/corpus-health-model.md |
| Manufacturing Metrics | metrics/manufacturing-metrics-framework.md |
| Validation Failures | validation/continuous-validation-framework.md |
| Opportunity Scores | opportunities/*.md |
| Coherence Scores | corpus/coherence/*.md |
| Graph Coverage | corpus/graph/*.md |
| User Direction | Current approved strategic direction |

## Priority Formula

```text
Adaptive Priority =
  (Capability Gap Severity × 0.25)
+ (Corpus Health Impact × 0.20)
+ (Reuse Multiplication × 0.15)
+ (Validation Risk Reduction × 0.15)
+ (Strategic Alignment × 0.15)
+ (Execution Readiness × 0.10)
- (Trajectory Risk Penalty)
```

## Capability Gap Severity

| Severity | Meaning |
|---:|---|
| 5 | Blocks V2 self-assessment. |
| 4 | Weakens corpus health or release safety. |
| 3 | Limits reuse or graph expansion. |
| 2 | Improves convenience but not strategic capability. |
| 1 | Nice-to-have or cosmetic. |

## Trajectory Risk Penalty

Apply penalty when work:

- increases output volume without improving capability,
- over-optimizes for publication,
- weakens proof boundaries,
- introduces unvalidated automation,
- creates content without graph or opportunity integration,
- rewards vanity metrics.

## Current Adaptive Queue

| Rank | Work Item | Reason |
|---:|---|---|
| 1 | Update graph index with NKS-GPH-000004 and NKS-GPH-000005 | Improves graph coverage and corpus health. |
| 2 | Create Capability Gap Register | Required for V2 self-assessment. |
| 3 | Create Corpus Health Register | Converts health model into trackable state. |
| 4 | Create Proof Confidence Scorecard | Strengthens release safety and public-claim governance. |
| 5 | Create Release Test Harness | Allows controlled release tests without trajectory drift. |
| 6 | Create Orphan Artifact Report | Reduces archive drift. |
| 7 | Create Graph Coverage Matrix | Makes relationship completeness measurable. |

## Execution Rule

When `@GitHub execute` is invoked, choose the highest-ranked unblocked item unless the user explicitly overrides it.

## Status

Implemented as adaptive prioritization engine v1.