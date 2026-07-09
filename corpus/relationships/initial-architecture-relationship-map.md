# Initial Architecture Relationship Map

## Source

NKS-SRC-000001 — Media Blitz OS / Nelson Knowledge System Architecture Conversation

## Core Relationship

The key architectural chain is:

```text
Source Material
  ↓
Knowledge Extraction
  ↓
Canonical Artifacts
  ↓
Corpus
  ↓
Knowledge Graph
  ↓
Publication Engine / Career Engine / Executive Intelligence
```

## Artifact Relationships

### NKS-ART-000001 — Corpus Is Manufactured, Not Found

Parent concept for the corpus construction layer.

Related to:

- NKS-ART-000002 — clarifies that publishing is downstream of corpus construction.
- NKS-ART-000003 — requires a durable control plane to persist the manufacturing process.
- NKS-ART-000004 — requires execution discipline so corpus construction does not stall.

### NKS-ART-000002 — Media Blitz OS as Publishing Subsystem

Defines the boundary between the publishing engine and the broader Nelson Knowledge System.

Related to:

- NKS-ART-000001 — depends on the corpus as upstream knowledge supply.
- NKS-ART-000003 — GitHub records the architecture and publishing machinery.

### NKS-ART-000003 — GitHub as Knowledge-System Control Plane

Defines where governance, state, schemas, and fallback artifacts persist.

Related to:

- NKS-ART-000001 — stores the manufacturing rules and outputs.
- NKS-ART-000004 — enforces no-idle execution through durable governance.

### NKS-ART-000004 — No Idle State Rule

Defines execution behavior when work remains.

Related to:

- NKS-ART-000001 — ensures the corpus is continuously manufactured.
- NKS-ART-000003 — is implemented and preserved in GitHub governance.

## Publication Opportunities

1. Medium article: `The Corpus Is Manufactured, Not Found`
2. LinkedIn post: `The mistake is treating knowledge as storage instead of production.`
3. X thread: `A corpus is not a folder. It is a manufacturing output.`
4. Instagram carousel: `Source Material → Corpus → Knowledge Graph → Publishing Engine`
5. Pinterest framework: `Knowledge Manufacturing Loop`

## System Implication

The Nelson Knowledge System should prioritize corpus manufacturing before large-scale publication. Publishing from an unstructured source pool risks content volume without compounding architecture.
