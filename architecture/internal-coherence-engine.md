# Internal Coherence Engine

## Purpose

The Internal Coherence Engine determines whether a knowledge artifact strengthens the Nelson Knowledge System or merely adds more stored material.

It exists to prevent the corpus from becoming a prettier archive.

## Core Principle

An artifact is valuable when it increases system capability, not merely when it creates an output.

## Coherence Object

Every artifact should be evaluated using this object:

```yaml
coherence_record:
  artifact_id:
  source_record_id:
  title:
  strategic_objective:
  capability_area:
  capability_maturity_delta:
  proof_boundary:
  relationship_density:
  downstream_uses:
  visual_representation:
  publication_relevance:
  opportunity_relevance:
  automation_relevance:
  risk:
  recommended_next_action:
```

## Scoring Model

| Dimension | Max Points | Question |
|---|---:|---|
| Strategic Alignment | 20 | Does this directly advance a current NKS objective? |
| Capability Growth | 20 | Does this mature a durable capability? |
| Proof Strength | 15 | Is the evidence boundary clear and useful? |
| Relationship Density | 15 | Does this strengthen links among existing artifacts? |
| Reuse Potential | 15 | Can this support multiple downstream uses? |
| Automation Leverage | 10 | Does this help the system operate with less manual intervention? |
| Risk Control | 5 | Does this reduce ambiguity, unsupported claims, or workflow fragility? |

Maximum score: 100.

## Interpretation

| Score | Meaning | Default Action |
|---:|---|---|
| 85–100 | Core capability artifact | Prioritize immediately. |
| 70–84 | Strong reusable artifact | Process after current critical path. |
| 50–69 | Useful but incomplete | Park until proof/relationship gaps are resolved. |
| 30–49 | Low leverage | Store as source material; do not manufacture yet. |
| 0–29 | Noise or premature | Do not promote to corpus. |

## Required Answers

Before an artifact becomes canonical, it must answer:

1. Which strategic objective does this support?
2. Which capability does this mature?
3. What proof boundary applies?
4. Which existing artifacts does it strengthen?
5. Which future artifacts could depend on it?
6. What downstream uses can it serve?
7. What visual representation belongs to it?
8. What next action should the engine take?

## Current Priority Logic

The engine prioritizes work in this order:

1. Capability growth.
2. Corpus coherence.
3. Proof strength.
4. Reuse potential.
5. Publication readiness.
6. Distribution readiness.

Publication is a downstream beneficiary, not the objective.

## Example: NKS-PUB-000001 Cluster

The Publication #1 cluster scores high because it establishes the core operating model: source material becomes proof-bounded canonical artifacts, which become reusable knowledge infrastructure. Its downstream use is not merely a Medium article; it provides the mental model for corpus manufacturing, visuals, contracts, future briefings, and platform positioning.

## Status

Implemented as governance/specification layer. Next step: create machine-readable scorecards for current artifact clusters.