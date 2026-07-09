# Knowledge Graph Model

## Purpose

The Knowledge Graph makes the Nelson Knowledge System traversable.

The corpus should not merely contain artifacts. It should understand how source material, proof, artifacts, visuals, contracts, outputs, opportunities, and feedback relate.

## Core Principle

Every object in the system should be able to answer:

- What produced me?
- What do I support?
- What depends on me?
- What evidence bounds me?
- What can I become?

## Node Types

| Node Type | Description |
|---|---|
| Source | Raw material: conversation, document, whitepaper, resume, role analysis, feedback. |
| Artifact | Canonical extracted idea with stable identity. |
| Proof | Evidence boundary, citation set, or claim limitation. |
| Capability | Durable system ability matured by artifacts. |
| Narrative | Reader or stakeholder progression model. |
| Visual | Diagram, hero, carousel, quote card, infographic, slide. |
| Contract | Machine-readable interface object for adapters or validation. |
| Package | Publication, briefing, deck, book chapter, or derivative output package. |
| Opportunity | Possible downstream use: executive briefing, consulting framework, interview story, etc. |
| Feedback | Public response, editorial comment, analytics, objection, revision trigger. |
| Roadmap | Strategic direction or capability target. |

## Edge Types

| Edge | Meaning |
|---|---|
| derived_from | Child object originated from source object. |
| supports | Object strengthens another object. |
| bounded_by | Claim/artifact is constrained by proof boundary. |
| matures | Object increases capability maturity. |
| represented_by | Idea is represented visually by an asset. |
| packaged_as | Artifact becomes a publication/brief/deck/etc. |
| produces | Object creates or enables another object. |
| depends_on | Object cannot be complete without another object. |
| contradicts | Object conflicts with another and requires resolution. |
| enriches | Feedback improves corpus object. |
| advances | Object advances roadmap item or strategic objective. |

## Graph Record Format

```yaml
graph_record:
  graph_id:
  nodes:
    - id:
      type:
      title:
      path:
  edges:
    - from:
      edge:
      to:
      rationale:
```

## Graph Rules

1. Every canonical artifact must link to at least one source.
2. Every public-facing output must link to proof.
3. Every visual must link to the artifact or package it represents.
4. Every opportunity must link to at least one artifact and one capability.
5. Feedback must never overwrite source; it enriches downstream records.
6. Contradictions must create resolution work, not be silently merged.

## Current Implementation

The graph is stored as Markdown/YAML hybrid records under `corpus/graph/`.

Future implementation may serialize to JSON-LD, RDF, Neo4j, SQLite, or another graph database. The model is intentionally storage-independent.

## Status

Implemented as graph model v1.