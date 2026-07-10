# Execution Queue

This queue tracks artifacts and technical work that need to be created, updated, synchronized, reviewed, tested, or published.

## Status Values

- `Planned`
- `In Progress`
- `Written to GitHub`
- `Ready to Sync to Drive`
- `Written to Drive`
- `Verified`
- `Published`
- `Blocked`

## Content and Governance Queue

| ID | Artifact | Type | Target Surface | Status | Notes |
|---|---|---|---|---|---|
| EQ-0001 | Media Blitz Charter | Governance Document | GitHub + Google Drive | Written to GitHub | Strategic north-star document. |
| EQ-0002 | OS Constitution | Governance Document | GitHub + Google Drive | Written to GitHub | Defines assistant execution behavior and system rules. |
| EQ-0003 | Medium Article Template | Template | GitHub + Google Drive | Written to GitHub | Canonical long-form structure. |
| EQ-0004 | LinkedIn Post Template | Template | GitHub + Google Drive | Written to GitHub | Executive distribution format. |
| EQ-0005 | X Thread Template | Template | GitHub + Google Drive | Written to GitHub | Short-form argument structure. |
| EQ-0006 | Instagram Carousel Template | Template | GitHub + Google Drive | Written to GitHub | Visual framework format. |
| EQ-0007 | Pinterest Framework Pin Template | Template | GitHub + Google Drive | Written to GitHub | Evergreen visual discovery format. |
| EQ-0008 | Artifact Metadata Schema | Schema | GitHub | Written to GitHub | Defines asset metadata fields. |
| EQ-0009 | Publication Pipeline Schema | Schema | GitHub | Written to GitHub | Defines workflow and state transitions. |
| EQ-0010 | Drive Sync Ledger | Operations Ledger | GitHub + Google Drive | Written to GitHub | Tracks artifacts pending sync to Drive. |

## Runtime and Portability Queue

The authoritative implementation backlog is `docs/technical-backlog.md`.

| ID | Work Item | Priority | Status | Architectural Purpose |
|---|---|---:|---|---|
| EQ-0101 | TB-001 Runtime Package Boundaries | 1 | Planned | Separate domain, application, interfaces, adapters, CLI, and tests. |
| EQ-0102 | TB-002 Machine-Readable Canonical Schemas | 2 | Planned | Prevent Markdown and GitHub paths from becoming the database contract. |
| EQ-0103 | TB-003 Repository Interfaces | 3 | Planned | Remove direct platform access from workflows. |
| EQ-0104 | TB-004 Filesystem Adapter | 4 | Planned | Establish a neutral runtime independent of network services. |
| EQ-0105 | TB-007 Explicit State Machines | 5 | Planned | Make workflow behavior deterministic and testable. |
| EQ-0106 | TB-008 Governance as Code | 6 | Planned | Convert policy gates into executable validation. |
| EQ-0107 | TB-011 Runtime CLI | 7 | Planned | Allow the same runtime to execute locally, in CI, or through a future API. |
| EQ-0108 | TB-012 Functional Test Harness | 8 | Planned | Prove one complete manufacturing workflow. |
| EQ-0109 | TB-005 GitHub Adapter | 9 | Planned | Use GitHub through an adapter rather than as domain architecture. |
| EQ-0110 | TB-017 Dependency Extraction Test | 10 | Planned | Prove the runtime can operate without GitHub, Drive, or external services. |
| EQ-0111 | TB-006 Drive Adapter Contract | 11 | Planned | Isolate flaky connector behavior from domain execution. |
| EQ-0112 | TB-009 Event and Audit Model | 12 | Planned | Preserve platform-neutral workflow history. |
| EQ-0113 | TB-010 Generated Human Views | 13 | Planned | Generate indexes and ledgers from canonical records. |
| EQ-0114 | TB-013 Integration Contract Tests | 14 | Planned | Require consistent behavior across adapters. |
| EQ-0115 | TB-014 Export and Migration Capability | 15 | Planned | Ensure state can leave the current host. |
| EQ-0116 | TB-015 Database Adapter Runway | 16 | Planned | Preserve migration path to durable persistence. |
| EQ-0117 | TB-016 Orchestrator Independence | 17 | Planned | Keep business rules out of GitHub Actions. |

## Runtime Release Guardrail

Runtime v0.1 cannot be marked architecturally complete until the portable core, filesystem adapter, GitHub adapter, executable policy gates, CLI, functional test, and dependency-extraction test pass.

## Current Rule

If Drive is unavailable, continue writing artifacts to GitHub and mark them `Ready to Sync to Drive`.

If GitHub is the current runtime host, continue implementation through platform-neutral interfaces and adapters. Never place business rules exclusively in GitHub Actions, repository paths, connector calls, or platform metadata.