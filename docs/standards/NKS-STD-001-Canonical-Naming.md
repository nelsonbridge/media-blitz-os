# NKS-STD-001 — Canonical Naming Standard

Status: Approved  
Version: 1.0

## Purpose

Establish immutable internal identifiers that survive commercial renaming, tier changes, vendor replacement, and implementation turnover.

## Core Rule

Human-facing names are ephemeral. Architectural identifiers are durable.

## Naming Hierarchy

### Level 0 — Fundamental Capability

Reserved prefix: `ME`

`ME` identifies foundational capability classes that may span multiple domains.

Format:

`ME-<NUMBER>`

### Level 1 — Deity Domain

A Sumerian deity name identifies an enduring architectural domain or capability family.

Examples:

- `ANU` — origin authority and constitutional intent
- `ENKI` — knowledge synthesis, architecture, and technical continuity

A deity identifier must be selected by:

1. historical attribution;
2. semantic alignment;
3. relative hierarchical fit;
4. architectural durability.

### Level 2 — King Program

A Sumerian or Mesopotamian king name identifies an implementation, initiative, release train, operational program, or campaign built upon one or more deity domains.

Deities define enduring capability. Kings define time-bounded realization.

### Level 3 — Component Identifier

Format:

`<DOMAIN>-<TYPE>-<NUMBER>`

Examples:

- `ENKI-RUN-001`
- `ENKI-GRAPH-014`
- `ANU-POL-001`

## Reserved Type Codes

- `CAP` — capability
- `POL` — policy
- `RUN` — runtime
- `SVC` — service
- `REC` — record
- `EVT` — event
- `VAL` — validator
- `ADP` — adapter
- `LIC` — licensing rule or bundle
- `PRG` — program
- `REL` — release
- `DOC` — canonical documentation

Additional codes require governance review.

## Brand Isolation

Commercial names may appear only in configuration, localization, presentation metadata, marketing assets, and external contracts.

Commercial names must not control runtime branching, domain logic, canonical IDs, or persistence paths.

## Assignment Rule

Names are assigned once and remain stable. Corrections require an explicit migration record; cosmetic rebranding never triggers identifier replacement.
