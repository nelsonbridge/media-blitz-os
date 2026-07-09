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
| SYNC-0012 | Pinterest Framework Pin Template | templates/pinterest-framework-pin-template.md | 08_Pinterest / Templates | Ready to Sync | Evergreen discovery template. |
| SYNC-0013 | Master State Index | docs/master-state-index.md | 02_Editorial OS | Ready to Sync | Authoritative project state. |
| SYNC-0014 | Canonical Artifact Specification | corpus/artifact-specification.md | 02_Editorial OS / Corpus | Ready to Sync | Defines unit of knowledge. |
| SYNC-0015 | Corpus Construction Workflow | corpus/corpus-construction-workflow.md | 02_Editorial OS / Corpus | Ready to Sync | Defines manufacturing process. |
| SYNC-0016 | Source Record Template | corpus/templates/source-record-template.md | Corpus Templates | Ready to Sync | Template for source records. |
| SYNC-0017 | Artifact Record Template | corpus/templates/artifact-record-template.md | Corpus Templates | Ready to Sync | Template for artifact records. |
| SYNC-0018 | Source Record NKS-SRC-000001 | corpus/sources/NKS-SRC-000001-media-blitz-os-architecture-conversation.md | 01_Source Corpus | Ready to Sync | First source record. |
| SYNC-0019 | Corpus Artifacts NKS-ART-000001-000004 | corpus/artifacts/ | 01_Source Corpus / Corpus | Ready to Sync | First four corpus artifacts. |
| SYNC-0020 | Corpus Index | corpus/corpus-index.md | 02_Editorial OS / Corpus | Ready to Sync | Navigable artifact index. |
| SYNC-0021 | Initial Architecture Relationship Map | corpus/relationships/initial-architecture-relationship-map.md | 02_Editorial OS / Corpus | Ready to Sync | First relationship map. |
| SYNC-0022 | Publication Package NKS-PUB-000001 | publishing/packages/NKS-PUB-000001-the-corpus-is-manufactured-not-found.md | 03_Medium Drafts | Ready to Sync | First publication package. |
| SYNC-0023 | Medium Draft NKS-PUB-000001 | publishing/medium-drafts/NKS-PUB-000001-the-corpus-is-manufactured-not-found-draft.md | 03_Medium Drafts | Ready to Sync | First full Medium draft. |
| SYNC-0024 | Derivative Packages NKS-DER-000001-000004 | publishing/derivatives/ | Platform folders | Ready to Sync | LinkedIn, X, Instagram, Pinterest derivatives. |
| SYNC-0025 | Publication Review Checklist | publishing/reviews/NKS-PUB-000001-review-checklist.md | 03_Medium Drafts / Reviews | Ready to Sync | Review checklist. |
| SYNC-0026 | Publication Index | publishing/publication-index.md | 02_Editorial OS | Ready to Sync | Publication registry. |

## Rule

Whenever GitHub is used as fallback because Drive writes are unavailable, add the artifact here before considering the sprint task complete.
