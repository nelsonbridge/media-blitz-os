# Transport Language Layer

## Purpose

Define how canonical Nelson Knowledge System concepts are expressed when passing through external tools, repositories, documents, or publishing surfaces.

This layer protects the corpus from being rewritten merely because a target system has vocabulary constraints.

## Core Principle

Canonical knowledge is stable. Transport representations are adaptable.

## Architecture

```text
Canonical Concept
  ↓
NKS Contract
  ↓
Transport Language Profile
  ↓
Target Surface
```

## Why This Exists

External systems may react differently to terminology depending on context, filename, payload, or surface. That does not mean the canonical concept is wrong.

It means the connector needs a representation profile.

## Canonical Layer

The canonical layer preserves the true semantic model of NKS.

It contains the durable concepts, decisions, relationships, and proof boundaries that define the system.

Canonical records should not be weakened to fit a specific vendor, platform, or connector.

## Transport Layer

The transport layer adapts wording for a specific destination while preserving meaning.

It may adjust:

- filenames,
- headings,
- summaries,
- metadata,
- commit messages,
- issue titles,
- document labels,
- surface-specific phrasing.

It must not alter:

- source lineage,
- proof boundary,
- graph relationships,
- capability intent,
- strategic meaning,
- canonical concept identity.

## Required Rule

Every connector should eventually have a language profile.

Each profile defines:

1. preferred terminology,
2. terms to avoid in transport payloads,
3. safe substitutions,
4. canonical concept preserved,
5. surfaces where the profile applies.

## Example Pattern

```yaml
transport_mapping:
  canonical_concept: durable internal concept
  transport_label: surface-safe label
  preserved_meaning: what must remain true
  applies_to:
    - filename
    - commit message
    - summary
  forbidden_change: what the adapter may not distort
```

## Operating Rule

Do not rewrite the corpus to satisfy a connector.

Write a connector language profile instead.

## Status

Implemented as architecture layer v1.