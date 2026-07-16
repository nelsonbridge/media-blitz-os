# Enki Knowledge System — Split-Cloud Reference Architecture

Reference architecture: `CF-NEON-R2`

Status: **Architecture documentation only**

Core provider set:

- Cloudflare Workers — compute and edge runtime
- Neon Postgres — canonical structured data
- Cloudflare R2 — evidence, artifacts, packages, exports, and backups

This document is the corrected split-cloud architecture view. Optional provider services are explicitly identified as optional or candidate capabilities and are not implied dependencies of Enki core.

```mermaid
flowchart TB
  subgraph L1["Layer 1 — Ecosystem & Consumer Context"]
    H[Human users]
    S[Source artifacts]
    X[External systems]
    C[Downstream product suites\nMedia Blitz\nCareer Intelligence & Placement\nPersonal Cognitive Continuity\nResearch & Decision Support]
  end

  subgraph L2["Layer 2 — Hosted Deployment Topology"]
    CF[Cloudflare global edge]
    ACC[Cloudflare account boundary]
    REG[Region strategy]
    NEON[(Neon Postgres\nCanonical data)]
    R2[(Cloudflare R2\nObjects / evidence)]
  end

  subgraph L3["Layer 3 — Edge, Identity & Access"]
    DNS[DNS & traffic management]
    WAF[WAF / rate limiting / edge security]
    AUTH[Authentication & authorization]
    TENANT[Tenant & context resolution]
    API[API gateway / request validation]
  end

  subgraph L4["Layer 4 — Runtime & Service Bindings"]
    ROUTER[Request router]
    CTX[Auth / context resolver]
    MID[Middleware pipeline]
    HANDLER[Handler modules]
    RESP[Response orchestration]
    NB[Neon binding]
    R2B[R2 binding]
    OPT[Optional adapters\nKV / Queues / Durable Objects / Cache]
    SEC[Secrets binding]
  end

  subgraph L5["Layer 5 — Application & Product-Neutral Knowledge Services"]
    CAP[Capture & ingest]
    NORM[Normalize & resolve]
    STATE[Knowledge state & context]
    INTERP[Interpretation & reasoning]
    RETR[Retrieval & search]
    PACK[Packaging & projection]
    DISC[Controlled disclosure & delivery]
  end

  subgraph L6["Layer 6 — Governance & Governed Execution"]
    AA[Authority & approval]
    POL[Policy engine]
    PROV[Provenance & lineage]
    TX[Transactions & journaling]
    RES[Reservations & claims]
    REC[Receipts & attestations]
    MODEL[Model-use guardrails]
  end

  subgraph L7["Layer 7 — Persistence, Recovery & Lifecycle"]
    SNAP[Snapshots & checkpoints]
    REPLAY[Replay & reconstruction]
    RET[Retention & lifecycle]
    BAK[Backup / export / import]
    RECON[Recovery & reconciliation]
    CONFLICT[Conflict resolution]
    AUDIT[Compliance & audit]
  end

  subgraph L8["Layer 8 — Storage Adapters & Physical Persistence"]
    REL[Relational adapter\nNeon Postgres]
    OBJ[Object adapter\nCloudflare R2]
    IDX[Index / cache adapters\noptional]
  end

  subgraph L9["Layer 9 — Canonical Record & Knowledge Model"]
    ENT[Canonical entities\nTenant / Domain / Subject / Source / Artifact]
    KNOW[Knowledge entities\nAssertion / Evidence / Confidence / Interpretation / Context]
    GOV[Governance entities\nAuthority / Approval / Policy / Transition / Provenance / Lineage]
    OPS[Operational entities\nTransaction / Reservation / Receipt / Snapshot / Conflict / Recovery / Audit]
    TEMP[Temporal dimensions\nrecorded_at / effective_from / effective_to / superseded_at]
  end

  H --> CF
  S --> CF
  X --> CF
  C --> CF
  CF --> DNS --> WAF --> AUTH --> TENANT --> API
  API --> ROUTER --> CTX --> MID --> HANDLER --> RESP
  HANDLER --> NB
  HANDLER --> R2B
  HANDLER -. optional .-> OPT
  HANDLER --> SEC
  NB --> NEON
  R2B --> R2
  RESP --> CAP --> NORM --> STATE --> INTERP --> RETR --> PACK --> DISC
  STATE --> AA
  INTERP --> POL
  PACK --> PROV
  AA --> TX
  POL --> TX
  PROV --> TX
  TX --> RES --> REC --> MODEL
  TX --> SNAP
  REC --> REPLAY
  REPLAY --> RET
  RET --> BAK
  BAK --> RECON
  RECON --> CONFLICT
  CONFLICT --> AUDIT
  SNAP --> REL
  REPLAY --> REL
  BAK --> OBJ
  AUDIT --> OBJ
  REL --> ENT
  REL --> KNOW
  REL --> GOV
  REL --> OPS
  ENT --> TEMP
  KNOW --> TEMP
  GOV --> TEMP
  OPS --> TEMP
```

## Cross-cutting planes

The following planes span Layers 2–9 and are **not additional stacked layers**.

### Governance & Authority Plane

Ensures every governed action is authorized, traceable, policy-constrained, and subject to explicit human authority where required.

### Security & Privacy Plane

Covers identity, least privilege, secrets, encryption hooks, tenant and subject isolation, consent, redaction, privacy preservation, and deny-by-default behavior.

### Observability & Audit Plane

Covers privacy-preserving metrics, traces, structured logs, immutable audit evidence, health signals, incident reconstruction, and compliance evidence.

### Portability & Recovery Plane

Covers governed export/import, backup, disaster recovery, replay, deterministic reconstruction, migration, rollback, and provider-exit portability.

## Provider boundary rules

1. Neon Postgres is the canonical structured-data system of record unless a later governed architecture decision explicitly changes that role.
2. Cloudflare R2 stores evidence objects, generated packages, publication assets, exports, recovery bundles, and related object artifacts.
3. D1 is **not** part of the CF-NEON-R2 core architecture.
4. KV, Queues, Durable Objects, Cache, Images, Stream, and similar Cloudflare services are optional candidates only and must earn adoption through a separate architectural decision.
5. No queue or event bus is assumed to be the authoritative canonical mutation path.
6. Downstream product suites consume Enki through governed consumer boundaries; they do not become Enki core domain services.
7. Production infrastructure validation remains separate from architecture documentation and TEST validation.
