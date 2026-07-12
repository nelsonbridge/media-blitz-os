# Temporal Human Evolution Feedback Architecture

> **Authority class: Class 3 — architecture and implementation contract.**
> Canonical observations, transitions, policies, and receipts remain operationally authoritative.

## Governing Principle

Canonicalization stabilizes the attributable record of an observation. It must not stabilize the human being described.

The system models a person as a temporally ordered lineage of observations and governed transitions. A newer state may supersede the behavioral authority of an older state without erasing the fact that the older state was once observed.

## Implemented Record Families

- `HumanStateObservation` records attributable, time-bounded human states.
- `HumanStateTransition` records how and under whose authority two observations relate.
- `ModelIngestionPolicy` independently authorizes model-use scopes and binds authorization to the exact current observation hash.
- `ModelFeedbackPackage` presents current state, historical context, approved transitions, and behavioral constraints.
- `ModelFeedbackReceipt` records the exact model-facing payload hash and authorization used.

## Authority Separation

The implementation keeps these decisions independent:

1. provenance of the observation;
2. temporal and interpretive status;
3. whether a transition is subject-declared, human-reviewed, or inferred;
4. whether the observation is canonical;
5. whether a specific model-use scope is approved;
6. whether a transition may influence model behavior.

No generic `approved: true` field grants all of those privileges.

## Temporal Semantics

Supported states include current, historical, superseded, retracted, conditional, context-specific, tentative, disputed, unresolved, and expired.

The model-facing publisher:

- selects the latest eligible current state;
- preserves eligible historical observations;
- excludes retracted, expired, and disputed observations from active payloads;
- includes only transitions explicitly approved for model feedback;
- rejects stale policy authorization when the current observation changes;
- preserves uncertainty and context in behavioral instructions.

## Model-Ingestion Control

Policy is scoped independently to:

- personalization;
- retrieval;
- evaluation;
- replay testing;
- fine-tuning;
- training;
- external model transmission.

Approval for one scope does not imply approval for another. Revoked, expired, stale, mismatched, or denied policies fail closed.

## Human Agency

An inferred transition never becomes equivalent to a subject declaration. Governed inference requires explicit causes, preserved uncertainty, and separate approval before it may influence model behavior.

The subject or authorized operator may create a later observation, retract an earlier one, revoke a model-ingestion policy, or narrow permitted scope. History remains reconstructable, while revoked or superseded state ceases to control current behavior.

## Model Behavioral Contract

Published feedback packages instruct the consuming model to:

- use the current approved state;
- preserve historical context;
- avoid generalization beyond the recorded domain and context;
- preserve uncertainty;
- and never treat inference as self-declaration.

## Verification

Regression tests cover:

- preservation of historical state during conditional revision;
- independently scoped model-ingestion approval;
- content-hash binding;
- stale-policy rejection after human change;
- expired and denied-policy rejection;
- and stricter requirements for governed inference.

## Remaining Work

- runtime CLI commands for record, transition, policy, revoke, and publish workflows;
- deterministic human-state and transition indexes;
- append-only workflow events for every decision and failure;
- audit reconstruction across observations, transitions, policies, payloads, and receipts;
- explicit redaction and privacy policy before external model transmission;
- policy replacement and revocation receipts;
- and evaluation fixtures measuring whether consuming models stop applying superseded assumptions.
