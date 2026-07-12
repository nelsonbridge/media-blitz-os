# NKS-STD-002 — Role Independence

Status: Approved  
Version: 1.0

## Requirement

Every canonical role shall be defined as a capability, never as a person, product, vendor, model, or implementation.

## Role Model

A role record defines:

- purpose;
- authority;
- responsibilities;
- parent capability;
- allowed delegation;
- approval boundaries;
- continuity requirements.

A stewardship record defines:

- current holder or implementation;
- scope;
- effective period;
- authority limits;
- replacement status.

The role and its steward must never be stored as the same object.

## ANU

ANU is the Origin Authority capability.

The current founder occupies ANU. The founder is not hard-coded as ANU in domain logic. Transfer, succession, delegation, or temporary representation must be possible through stewardship data without renaming the capability.

## ENKI

ENKI is the Knowledge Engine capability.

ENKI may be realized collectively by humans, AI systems, local models, hosted models, automation, or future implementations. No current implementation may claim exclusive identity with ENKI.

## Prohibited Coupling

Canonical code and records must not require:

- a specific founder identity;
- a specific AI model;
- a specific AI vendor;
- a specific repository host;
- a specific document workspace;
- a specific publishing provider.

## Continuity Test

A role-independent component must continue to function when:

1. the current steward is replaced;
2. the provider is unavailable;
3. the display name changes;
4. the commercial tier changes;
5. the runtime host changes.

Failure of any test identifies architectural coupling that must be removed or explicitly governed.
