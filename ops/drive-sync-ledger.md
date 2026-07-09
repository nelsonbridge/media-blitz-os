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

## Rule

Whenever GitHub is used as fallback because Drive writes are unavailable, add the artifact here before considering the sprint task complete.
