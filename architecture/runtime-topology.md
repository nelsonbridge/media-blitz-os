# Nelson Knowledge System Runtime Topology

## Purpose

Defines how the connected ecosystem operates as one modular runtime without making any connector or platform part of the domain core.

## Topology

```text
User / Approval Authority
          |
          v
ChatGPT Orchestration Layer
          |
          v
NKS Application Services and Policy Gates
          |
          +-------------------------------+
          |                               |
          v                               v
Local Runtime / CLI                 Trigger Adapters
Tests, transforms, export           Automations, Calendar
          |                               |
          +---------------+---------------+
                          |
                          v
                   Repository Ports
                          |
          +---------------+------------------+
          |               |                  |
          v               v                  v
Filesystem Adapter   GitHub Adapter      Future Database
Offline execution    Current canonical   Durable production
and extraction       persistence         persistence
          |
          v
Generated Human Views and Sync Jobs
          |
     +----+---------+------------------+
     |              |                  |
     v              v                  v
Drive/Docs      Sheets/Dashboards   Email/Calendar
Editorial       Operational views   Communication
workspace                           and scheduling

Evidence Ports                         Rendering Ports
     |                                      |
     v                                      v
Web / Consensus / Files              Image Generation
     |                                      |
     +------------------+-------------------+
                        |
                        v
                 Publication Package
                        |
       +----------------+----------------+
       |                |                |
       v                v                v
    Medium          LinkedIn/X       IG/FB/Pinterest
```

## Execution Principles

### 1. Local Runtime Is a First-Class Execution Surface

The local isolated Python environment may execute tests, transformations, exports, reconciliation, and generated-view workflows even when direct repository cloning or external network access is unavailable.

Canonical files may be reconstructed from verified connector reads, processed locally, and written back through repository adapters.

### 2. GitHub Is Current Persistence, Not Runtime Identity

GitHub currently stores code, JSON records, governance, schemas, and audit history. The same application services must operate against filesystem and future database adapters.

### 3. CI Is Additive

GitHub Actions is useful for independent verification but is not the sole method of executing or validating the runtime. CI observability limitations do not block local functional tests.

### 4. Human Views Are Generated or Synchronized

Drive, Docs, and Sheets are human-facing workspaces. Their contents should be generated from or reconciled with canonical machine-readable records.

### 5. Research Is Evidence Input

Web, Consensus, and uploaded files supply proof material. Evidence enters through source and proof records and cannot bypass policy gates.

### 6. Rendering Is Downstream

Image generation consumes approved visual briefs and proof boundaries. Generated assets must retain their NKS IDs, parent relationships, and approval status.

### 7. Publication Is an Adapter Action

Medium and social channels consume approved publication contracts. Manual publishing remains a valid adapter fallback when no direct publishing connector is available.

## Runtime Modes

### Mode A — Connected Execution

- Read/write canonical state through GitHub adapter.
- Run application workflows locally.
- Synchronize human views to Drive when available.
- Perform current research as required.
- Generate visual assets when authorized.

### Mode B — Degraded Connector Execution

- Continue locally against an exported filesystem store.
- Queue GitHub or Drive writes.
- Preserve events and deterministic outputs.
- Reconcile when connector access returns.

### Mode C — Offline Extraction Test

- Export all canonical JSON and event data.
- Disable GitHub, Drive, research, rendering, and publication adapters.
- Execute validation, manufacturing, and reconciliation locally.
- Confirm no domain behavior changes.

### Mode D — Manual Publication Fallback

- Produce complete publication package and platform payloads.
- Generate a human checklist.
- User performs platform action.
- Record public URL and publication event afterward.

## Current Critical Path

The critical path no longer depends on GitHub Actions or Google Drive.

Current critical path:

1. GitHub or exported JSON provides canonical state.
2. Local runtime executes domain workflows and tests.
3. GitHub persists results.
4. Visual generation and public approval complete the package.
5. Manual or automated publishing adapter distributes the asset.
