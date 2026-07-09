# Execution Queue

This queue tracks artifacts that need to be created, updated, synchronized, reviewed, or published.

## Status Values

- `Planned`
- `In Progress`
- `Written to GitHub`
- `Ready to Sync to Drive`
- `Written to Drive`
- `Verified`
- `Published`
- `Blocked`

## Queue

| ID | Artifact | Type | Target Surface | Status | Notes |
|---|---|---|---|---|---|
| EQ-0001 | Media Blitz Charter | Governance Document | GitHub + Google Drive | Planned | Strategic north-star document. |
| EQ-0002 | OS Constitution | Governance Document | GitHub + Google Drive | Planned | Defines assistant execution behavior and system rules. |
| EQ-0003 | Medium Article Template | Template | GitHub + Google Drive | Planned | Canonical long-form structure. |
| EQ-0004 | LinkedIn Post Template | Template | GitHub + Google Drive | Planned | Executive distribution format. |
| EQ-0005 | X Thread Template | Template | GitHub + Google Drive | Planned | Short-form argument structure. |
| EQ-0006 | Instagram Carousel Template | Template | GitHub + Google Drive | Planned | Visual framework format. |
| EQ-0007 | Pinterest Framework Pin Template | Template | GitHub + Google Drive | Planned | Evergreen visual discovery format. |
| EQ-0008 | Artifact Metadata Schema | Schema | GitHub | Planned | Defines asset metadata fields. |
| EQ-0009 | Publication Pipeline Schema | Schema | GitHub | Planned | Defines workflow and state transitions. |
| EQ-0010 | Drive Sync Ledger | Operations Ledger | GitHub + Google Drive | Planned | Tracks artifacts pending sync to Drive. |

## Current Rule

If Drive is unavailable, continue writing artifacts to GitHub and mark them `Ready to Sync to Drive`.
