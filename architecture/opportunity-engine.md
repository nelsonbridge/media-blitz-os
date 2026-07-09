# Opportunity Engine

## Purpose

The Opportunity Engine evaluates what each canonical artifact can become.

It prevents the Nelson Knowledge System from treating publication as the default or highest-value output.

## Core Principle

One extraction should create many possible downstream options.

Publication is one option. It is not the objective.

## Opportunity Types

| Opportunity Type | Description |
|---|---|
| Publication | Article, essay, newsletter, post, thread, carousel. |
| Executive Briefing | Short decision-maker briefing or board-facing narrative. |
| Whitepaper | Longer evidence-backed treatment of a framework or capability. |
| Book Chapter | Expansion candidate for long-form manuscript structure. |
| Presentation | Slide deck, keynote, workshop, or internal enablement asset. |
| Consulting Framework | Repeatable diagnostic or operating model. |
| Resume Evidence | Proof point or achievement framing. |
| Interview Story | STAR/CAR/leadership narrative. |
| Training Module | Teach-back asset or curriculum unit. |
| Product Feature | Platform capability or automatable workflow. |
| AI Context | Durable context for future reasoning or agents. |

## Opportunity Record Format

```yaml
opportunity_record:
  opportunity_id:
  source_artifact_id:
  title:
  opportunity_type:
  audience:
  value:
  effort:
  dependencies:
  proof_needs:
  visual_needs:
  risk:
  recommended_priority:
  next_action:
```

## Scoring Model

| Dimension | Max Points | Question |
|---|---:|---|
| Strategic Value | 25 | Does this strengthen the NKS mission or executive positioning? |
| Reuse Multiplication | 20 | Does this create multiple downstream surfaces? |
| Capability Growth | 20 | Does this mature the platform itself? |
| Evidence Strength | 10 | Is the proof boundary strong enough? |
| Visual Leverage | 10 | Can this be represented or taught visually? |
| Effort Efficiency | 10 | Is the effort proportional to value? |
| Timing / Sequence Fit | 5 | Is now the right time? |

Maximum score: 100.

## Priority Bands

| Score | Priority | Action |
|---:|---|---|
| 85–100 | P0 | Execute immediately if unblocked. |
| 70–84 | P1 | Queue after current P0 work. |
| 50–69 | P2 | Hold for proof/source enrichment. |
| 0–49 | P3 | Store only; do not pursue. |

## Anti-Pattern Guardrails

The engine must reject these false priorities:

- Publish because something is ready.
- Create a visual because visuals are attractive.
- Produce social derivatives because a platform exists.
- Expand content volume without increasing corpus capability.
- Treat output count as success.

## Correct Priority Test

A downstream output is worth pursuing when it:

1. strengthens the corpus,
2. matures a reusable capability,
3. has a clear proof boundary,
4. supports multiple future uses,
5. and does not distort the system toward vanity metrics.

## Status

Implemented as opportunity governance/specification layer. Next step: seed opportunities for the foundational operating model cluster.