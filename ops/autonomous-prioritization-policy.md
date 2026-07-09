# Autonomous Prioritization Policy

## Purpose

Defines how the Nelson Knowledge System selects the next executable work item without treating visible outputs as the objective.

## Core Principle

Capability growth outranks output production.

## Priority Formula

```text
Priority Score =
  (Capability Growth × 0.30)
+ (Corpus Coherence × 0.25)
+ (Proof Strength × 0.15)
+ (Reuse Multiplication × 0.15)
+ (Automation Leverage × 0.10)
+ (Timing Fit × 0.05)
- (Risk Penalty)
```

## Required Inputs

Each candidate work item must have:

- related artifact or source,
- capability area,
- coherence score,
- opportunity score,
- dependencies,
- risk boundary,
- next executable action.

## Default Execution Order

1. P0 capability multipliers.
2. Missing graph/coherence records for existing high-value artifacts.
3. Proof boundary upgrades.
4. Reusable templates/contracts/validation.
5. Visual/briefing assets that teach core capabilities.
6. Publication packages.
7. Platform-specific derivatives.

## Anti-Regression Rule

If the system starts ranking publication ahead of capability growth without a documented reason, the ranking is invalid.

## Current P0 Queue

1. Coherence Scorecard Template — complete.
2. Opportunity Record Template — complete.
3. Archive-to-Corpus Diagnostic — pending.
4. Executive Briefing — pending.
5. NKS Operating Model AI Context Pack — pending.
6. Knowledge Graph records for remaining clusters — pending.
7. Continuous Ingestion Workflow — pending.

## Status

Implemented. Use this policy for all future `@GitHub execute` runs.