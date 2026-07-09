# Drive Sync Ledger

This ledger tracks artifacts created or updated in GitHub that must later be synchronized into Google Drive when Drive write capability is available.

## Status Values

- `Not Needed`
- `Ready to Sync`
- `Synced to Drive`
- `Verified in Drive`
- `Blocked`

## Ledger

| ID | Artifact | GitHub Path | Drive Target | Status | Notes |
|---|---|---|---|---|---|
| SYNC-0001 | Project State Ledger | docs/project-state.md | 02_Editorial OS | Ready to Sync | Should become or update Master Project State in Drive. |
| SYNC-0002 | Execution Protocol | docs/execution-protocol.md | 02_Editorial OS | Ready to Sync | Should become OS execution protocol doc in Drive. |
| SYNC-0003 | Execution Queue | docs/execution-queue.md | 02_Editorial OS | Ready to Sync | Should become queue tab/doc in Drive. |
| SYNC-0004 | Media Blitz Charter | governance/media-blitz-charter.md | 02_Editorial OS | Ready to Sync | Strategic north-star document. |
| SYNC-0005 | OS Constitution | governance/os-constitution.md | 02_Editorial OS | Ready to Sync | Assistant operating rules. |
| SYNC-0006 | Artifact Metadata Schema | schemas/artifact-metadata-schema.md | Media Blitz Editorial OS Sheet | Ready to Sync | Should seed Knowledge Taxonomy tab. |
| SYNC-0007 | Publication Pipeline Schema | schemas/publication-pipeline-schema.md | Media Blitz Editorial OS Sheet | Ready to Sync | Should seed Publication Pipeline tab. |
| SYNC-0008 | Medium Article Template | templates/medium-article-template.md | 03_Medium Drafts / Templates | Ready to Sync | Canonical long-form template. |
| SYNC-0009 | LinkedIn Post Template | templates/linkedin-post-template.md | 04_LinkedIn / Templates | Ready to Sync | Distribution template. |
| SYNC-0010 | X Thread Template | templates/x-thread-template.md | 05_X / Templates | Ready to Sync | Distribution template. |
| SYNC-0011 | Instagram Carousel Template | templates/instagram-carousel-template.md | 07_Instagram / Templates | Ready to Sync | Visual template. |
| SYNC-0012 | Pinterest Framework Pin Template | templates/pinterest-framework-pin-template.md | 08_Pinterest / Templates | Ready to Sync | Evergreen template. |
| SYNC-0013 | Master State Index | docs/master-state-index.md | 02_Editorial OS | Ready to Sync | Authoritative project state. |
| SYNC-0014 | Corpus Core Files | corpus/ | 01_Source Corpus / 02_Editorial OS | Ready to Sync | Corpus specs, templates, source records, artifacts, indexes, and maps. |
| SYNC-0015 | Publishing Assets | publishing/ | 03_Medium Drafts and platform folders | Ready to Sync | Publication packages, drafts, reviews, and derivatives. |
| SYNC-0016 | Executive Source Cluster | corpus/sources/NKS-SRC-000002-architecture-of-inevitable-value.md | 01_Source Corpus | Ready to Sync | Executive profile source record. |
| SYNC-0017 | Executive Corpus Artifacts | corpus/artifacts/NKS-ART-000005-* through NKS-ART-000008-* | 01_Source Corpus | Ready to Sync | Four executive-value artifacts. |
| SYNC-0018 | AI Source Cluster | corpus/sources/NKS-SRC-000003-agentic-ai-security-whitepapers.md | 01_Source Corpus | Ready to Sync | AI whitepaper source record. |
| SYNC-0019 | AI Corpus Artifacts | corpus/artifacts/NKS-ART-000009-* through NKS-ART-000012-* | 01_Source Corpus | Ready to Sync | Four AI governance artifacts. |
| SYNC-0020 | Relationship Maps | corpus/relationships/ | 02_Editorial OS / Corpus | Ready to Sync | Architecture, executive value, and AI governance maps. |
| SYNC-0021 | Publication Index | publishing/publication-index.md | 02_Editorial OS | Ready to Sync | Updated publication registry. |

## Rule

Whenever GitHub is used as fallback because Drive writes are unavailable, add the artifact here before considering the sprint task complete.
