# Canonical Artifact Specification

## Purpose

The Canonical Artifact Specification defines the smallest durable unit of knowledge in the Nelson Knowledge System.

A corpus artifact is not a document, conversation, note, post, or draft. It is a curated unit of reusable knowledge extracted from one or more source materials and made durable through metadata, relationships, evidence posture, and derivative potential.

## Definition

A canonical artifact is a structured knowledge object that captures one durable idea, framework, argument, model, observation, or reusable intellectual asset.

## Artifact ID Standard

Format:

`NKS-ART-000001`

Prefixes:

- `NKS-ART` — canonical knowledge artifact.
- `NKS-SRC` — source artifact.
- `NKS-FWK` — framework artifact.
- `NKS-PUB` — publication artifact.
- `NKS-DER` — derivative artifact.
- `NKS-EVD` — evidence artifact.

## Required Fields

| Field | Description |
|---|---|
| Artifact ID | Stable identifier. |
| Title | Clear artifact title. |
| Artifact Type | Idea, framework, argument, model, observation, evidence, draft, publication, derivative. |
| Status | Candidate, Extracted, Refined, Canonical, Published, Superseded, Retired. |
| Source Lineage | Source documents, conversations, files, or notes. |
| Summary | Short description of the artifact. |
| Core Idea | The essential claim or concept. |
| Pillar | Primary strategic pillar. |
| Subpillar | More specific thematic location. |
| Audience | Primary intended audience. |
| Evidence Posture | None, anecdotal, experiential, documented, externally verified. |
| Confidence | Low, Medium, High. |
| Strategic Value | Why the artifact matters to the system. |
| Career Value | How it supports positioning or opportunity. |
| Related Artifacts | Linked artifact IDs. |
| Derivative Potential | Medium, LinkedIn, X, Instagram, Pinterest, whitepaper, book, keynote, resume, interview. |
| Canonical Location | GitHub path, Drive URL, or other stable location. |
| Version | Semantic or dated version. |
| Last Reviewed | Date. |
| Next Review | Date or review trigger. |

## Optional Fields

- Keywords
- Quotes
- Supporting examples
- Counterarguments
- Failure modes
- Research required
- Visual model required
- Publication priority
- Brand-risk rating
- Legal/compliance concerns
- Notes

## Maturity Model

### Candidate

Potentially useful idea identified but not yet structured.

### Extracted

The idea has been separated from its source and given preliminary metadata.

### Refined

The artifact has been clarified, deduplicated, and connected to one or more pillars.

### Canonical

The artifact is stable enough to serve as a source for publications, derivatives, frameworks, or future analysis.

### Published

The artifact has produced a public-facing publication or derivative.

### Superseded

A newer or stronger artifact replaces this one, but lineage is preserved.

### Retired

The artifact is no longer strategically useful, accurate, or aligned.

## Source Lineage Rule

No canonical artifact may exist without traceable source lineage.

Source lineage may include:

- Chat conversation summary.
- Uploaded document.
- Google Drive file.
- GitHub file.
- Email thread.
- External research.
- Personal observation.

## One-Idea Rule

Each artifact should contain one durable idea. If an artifact contains multiple durable ideas, split it into related artifacts.

## Relationship Rule

Artifacts should not exist in isolation unless they are newly created candidates. Canonical artifacts must identify relationships to pillars, source materials, derivatives, or adjacent artifacts.

## Evidence Rule

Observation, inference, hypothesis, and conclusion must remain distinguishable. Public-facing artifacts require the evidence posture appropriate to their claim strength.

## Derivative Rule

Every canonical artifact should identify which downstream forms it can support.

## Merge Rule

If two artifacts substantially overlap, do not duplicate them indefinitely. Merge, supersede, or preserve one as a derivative of the stronger canonical artifact.

## Retirement Rule

Artifacts may be retired when they are stale, strategically irrelevant, misleading, duplicative, or no longer aligned with the system's purpose.
