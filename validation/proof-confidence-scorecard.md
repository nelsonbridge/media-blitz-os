# Proof Confidence Scorecard

## Purpose

Score how confidently a claim, artifact, briefing, or release candidate can be used across internal and external surfaces.

Proof confidence is not the same as certainty. It is a governed statement of evidence quality, scope, and safe use.

## Confidence Dimensions

| Dimension | Max Points | Question |
|---|---:|---|
| Source Traceability | 20 | Can the claim be traced to a source record or source document? |
| Evidence Specificity | 20 | Is the supporting evidence specific rather than generalized? |
| Scope Clarity | 15 | Is the scope of the claim clear? |
| Timeframe Clarity | 10 | Is the timeframe clear when relevant? |
| Claim Type Clarity | 10 | Is the claim classified as quantitative, qualitative, comparative, causal, interpretive, or illustrative? |
| External Support | 10 | Is external citation or standard support available when needed? |
| Risk Boundary | 10 | Are misuse, overstatement, or interpretation risks documented? |
| Release Surface Fit | 5 | Is the claim appropriate for the intended audience/surface? |

Maximum score: 100.

## Confidence Bands

| Score | Confidence Level | Allowed Use |
|---:|---|---|
| 90–100 | High | Public use permitted if wording matches evidence. |
| 75–89 | Moderate | Public use permitted with boundary language. |
| 60–74 | Bounded | Internal use or carefully qualified public use. |
| 40–59 | Weak | Private ideation only; needs evidence repair. |
| 0–39 | Unsupported | Do not use as claim. |

## Claim Type Rules

| Claim Type | Requirement |
|---|---|
| Quantitative | Source, scope, timeframe, and calculation basis required. |
| Comparative | Comparator and benchmark required. |
| Causal | Evidence chain required or reframe as contribution. |
| Qualitative | Source or firsthand attribution required. |
| Interpretive | Clearly label as interpretation or framework. |
| Illustrative | Do not present as factual proof. |

## Scorecard Template

```yaml
proof_confidence_record:
  target_id:
  claim:
  claim_type:
  source_traceability:
  evidence_specificity:
  scope_clarity:
  timeframe_clarity:
  claim_type_clarity:
  external_support:
  risk_boundary:
  release_surface_fit:
  total_score:
  confidence_level:
  allowed_use:
  required_repairs:
```

## Current Priority Applications

1. Executive Evidence Bank quantified claims.
2. Clarity as Economic Instrument briefing.
3. AI oversight governance briefing.
4. Operational automation governance whitepaper outline.
5. Foundational publication release candidate.

## Status

Implemented as proof confidence framework v1.