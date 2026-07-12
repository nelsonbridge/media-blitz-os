# NKS-STD-004 — Capability Licensing Model

Status: Approved  
Version: 1.0

## Purpose

Define licensing as governed capability enablement rather than product-specific code branching.

## Core Rule

Licenses bind capabilities. Products assemble licensed capabilities. Brands describe the resulting experience.

## Requirements

1. Every licensable capability has an immutable canonical ID.
2. Every commercial tier references capability IDs through configuration.
3. Runtime authorization evaluates entitlements, not marketing names.
4. Commercial renaming must not alter canonical IDs or domain logic.
5. Tier changes must not require forks of core code.
6. Feature availability must be explainable from a license manifest.
7. Manual override, trial access, and enterprise policy must remain auditable.

## License Bundle Record

A license bundle must define:

- bundle ID;
- display name metadata;
- enabled capability IDs;
- usage limits;
- data-retention policy;
- approval requirements;
- effective period;
- jurisdiction or contract constraints;
- upgrade and downgrade behavior.

## Tier Neutrality

Commercial tier names are configuration and may change without migration.

Recommended immutable bundle identifiers use neutral codes such as:

- `LIC-BUNDLE-000`
- `LIC-BUNDLE-100`
- `LIC-BUNDLE-200`

The display names attached to those bundles may change independently.

## Capability Composition

A lower-scope offering may license only résumé and professional-record capabilities.

A broader offering may additionally license professional image, publication, knowledge, feedback, intelligence, or enterprise-governance capabilities.

The architecture must support both without maintaining separate products or duplicated implementations.

## Enforcement Boundary

License checks belong at application and policy boundaries. They must not contaminate canonical domain models with commercial names.

## Audit Requirement

Every denied or enabled capability decision must be traceable to:

- license bundle;
- entitlement source;
- policy version;
- subject;
- timestamp;
- decision result.
