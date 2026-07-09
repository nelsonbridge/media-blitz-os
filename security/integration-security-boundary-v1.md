# Integration Security Boundary v1

## Purpose

Defines the security posture for integrating the Nelson Knowledge System with external publishing, storage, visual, analytics, and automation systems.

## Core Principle

External systems are replaceable execution surfaces. They must not become authoritative for source lineage, proof posture, narrative state, visual state, approval state, or corpus identity.

## Protected NKS Assets

- Source records
- Corpus artifacts
- Proof ledgers
- Narrative arc ledgers
- Visual package records
- Publication package records
- Approval records
- Contract definitions
- Adapter audit logs

## Credential Rules

1. Credentials must not be stored in publication packages.
2. Credentials must not be committed to GitHub.
3. Adapters may reference credential names, not secret values.
4. External tools receive the minimum scopes necessary.
5. Separate credentials should be used per service where practical.

## Approval Boundary

No adapter may publish, schedule, or externally distribute an asset unless:

- approval required is true,
- approval approved is true,
- approver is recorded,
- approval timestamp is recorded,
- contract validation succeeds.

## Data Boundary

External services may receive only the data required for their task.

Publishing services may receive:
- title,
- body,
- approved visual assets,
- schedule,
- platform metadata.

Publishing services must not receive:
- unrelated corpus notes,
- private source material not included in publication,
- internal evaluation notes,
- credentials,
- unapproved draft variants,
- private reasoning.

## Failure Boundary

External failure must not corrupt NKS state.

If a platform call fails:

- mark adapter result as failed,
- preserve the original contract,
- queue retry if retryable,
- log manual fallback if not retryable,
- do not change publication status to published.

## Audit Requirements

Each adapter run must record:

- contract ID,
- adapter name,
- adapter version,
- execution time,
- execution mode,
- result,
- external IDs/URLs if created,
- error details if failed,
- retry recommendation.

## Current Status

Draft v1. Ready to govern publishing and integration adapter evaluation.