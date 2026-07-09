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
| SYNC-0006 | Artifact Metadata Schema | schemas/artifact-metadata-schema.md | Media Blitz Editorial OS Sheet | Ready to Sync | Updated with source/proof/arc/visual fields. |
| SYNC-0007 | Publication Pipeline Schema | schemas/publication-pipeline-schema.md | Media Blitz Editorial OS Sheet | Ready to Sync | Updated with source/proof/arc/visual workflow states. |
| SYNC-0008 | Medium Article Template | templates/medium-article-template.md | 03_Medium Drafts / Templates | Ready to Sync | Updated with narrative arc gates. |
| SYNC-0009 | LinkedIn Post Template | templates/linkedin-post-template.md | 04_LinkedIn / Templates | Ready to Sync | Updated with proof and arc boundaries. |
| SYNC-0010 | X Thread Template | templates/x-thread-template.md | 05_X / Templates | Ready to Sync | Updated with proof and arc boundaries. |
| SYNC-0011 | Instagram Carousel Template | templates/instagram-carousel-template.md | 07_Instagram / Templates | Ready to Sync | Updated with proof and arc boundaries. |
| SYNC-0012 | Pinterest Framework Pin Template | templates/pinterest-framework-pin-template.md | 08_Pinterest / Templates | Ready to Sync | Updated with proof and arc boundaries. |
| SYNC-0013 | Master State Index | docs/master-state-index.md | 02_Editorial OS | Ready to Sync | Authoritative project state. |
| SYNC-0014 | Corpus Core Files | corpus/ | 01_Source Corpus / 02_Editorial OS | Ready to Sync | Corpus specs, templates, source records, artifacts, indexes, and maps. |
| SYNC-0015 | Publishing Assets | publishing/ | 03_Medium Drafts and platform folders | Ready to Sync | Publication packages, drafts, reviews, derivatives, arc ledger, and readiness gate. |
| SYNC-0016 | Executive Source Cluster | corpus/sources/NKS-SRC-000002-architecture-of-inevitable-value.md | 01_Source Corpus | Ready to Sync | Executive profile source record. |
| SYNC-0017 | Executive Corpus Artifacts | corpus/artifacts/NKS-ART-000005-* through NKS-ART-000008-* | 01_Source Corpus | Ready to Sync | Four executive-value artifacts. |
| SYNC-0018 | AI Source Cluster | corpus/sources/NKS-SRC-000003-agentic-ai-security-whitepapers.md | 01_Source Corpus | Ready to Sync | AI whitepaper source record. |
| SYNC-0019 | AI Corpus Artifacts | corpus/artifacts/NKS-ART-000009-* through NKS-ART-000012-* | 01_Source Corpus | Ready to Sync | Four AI governance artifacts. |
| SYNC-0020 | Relationship Maps | corpus/relationships/ | 02_Editorial OS / Corpus | Ready to Sync | Architecture, executive value, and AI governance maps. |
| SYNC-0021 | Publication Index | publishing/publication-index.md | 02_Editorial OS | Ready to Sync | Updated publication registry. |
| SYNC-0022 | Source Proof Publication Rule | governance/source-proof-publication-rule.md | 02_Editorial OS | Ready to Sync | Governance rule for source/proof/publication sequence. |
| SYNC-0023 | Narrative Arc Standard | governance/narrative-arc-standard.md | 02_Editorial OS | Ready to Sync | Governance rule for reader progression. |
| SYNC-0024 | Proof Ledger | research/proof-ledger.md | 02_Editorial OS / Evidence Library | Ready to Sync | Tracks proof and arc readiness. |
| SYNC-0025 | Narrative Arc Ledger | publishing/narrative-arc-ledger.md | 02_Editorial OS / Publication Pipeline | Ready to Sync | Tracks arc readiness for all drafts. |
| SYNC-0026 | Publication Readiness Gate | governance/publication-readiness-gate.md | 02_Editorial OS / Publication Pipeline | Ready to Sync | Unified source/proof/arc/visual release gate. |
| SYNC-0027 | Proof Arc Retrofit Queue | publishing/proof-arc-retrofit-queue.md | 02_Editorial OS / Publication Pipeline | Ready to Sync | Queue for proof and arc retrofits. |
| SYNC-0028 | Visual Knowledge System Governance | governance/visual-knowledge-system.md | 09_Visual Frameworks / 02_Editorial OS | Ready to Sync | Explains why visuals are first-class artifacts. |
| SYNC-0029 | Diagram Language Standard | governance/diagram-language-standard.md | 09_Visual Frameworks | Ready to Sync | Visual grammar and style rules. |
| SYNC-0030 | Visual Artifact Schema | schemas/visual-artifact-schema.md | Media Blitz Editorial OS Sheet / 09_Visual Frameworks | Ready to Sync | Visual metadata standard. |
| SYNC-0031 | Visual Templates | templates/signature-diagram-template.md; templates/hero-image-brief-template.md; templates/visual-package-template.md; templates/carousel-visual-template.md; templates/proof-graphic-template.md | 09_Visual Frameworks / Templates | Ready to Sync | Visual manufacturing templates. |
| SYNC-0032 | Visual Package Index | visuals/visual-package-index.md | 09_Visual Frameworks | Ready to Sync | Tracks required visual packages. |
| SYNC-0033 | First Visual Package | visuals/packages/NKS-VIS-000001.md | 09_Visual Frameworks | Ready to Sync | First visual package for NKS-PUB-000001. |
| SYNC-0034 | First Signature Diagram Brief | visuals/diagrams/NKS-DGM-000001.md | 09_Visual Frameworks | Ready to Sync | Nelson Knowledge Manufacturing Loop diagram brief. |
| SYNC-0035 | First Hero Image Brief | visuals/hero/NKS-HRO-000001.md | 09_Visual Frameworks | Ready to Sync | Hero image brief for foundational NKS article. |
| SYNC-0036 | Visual Generation Queue | visuals/visual-generation-queue.md | 09_Visual Frameworks | Ready to Sync | Visual generation backlog. |
| SYNC-0037 | Publication One Final Draft | publishing/medium-drafts/NKS-PUB-000001-the-corpus-is-manufactured-not-found-draft.md | 03_Medium Drafts | Ready to Sync | Revised to public-readiness candidate. |
| SYNC-0038 | Publication One Visual Derivative Briefs | visuals/carousels/NKS-CAR-000001.md; visuals/quote-cards/NKS-QTC-000001.md; visuals/pinterest/NKS-PIN-000001.md | 09_Visual Frameworks | Ready to Sync | Carousel, quote card, and Pinterest briefs. |
| SYNC-0039 | ADRs | architecture/adr/ | 02_Editorial OS / Architecture | Ready to Sync | Contract ownership and hybrid buy decisions. |
| SYNC-0040 | Contracts | contracts/publication-contract-v1.md; contracts/adapter-contract-v1.md; contracts/payloads/NKS-PUB-000001-publication-contract.yaml | 02_Editorial OS / Integration Lab | Ready to Sync | Publication and adapter contract runway. |
| SYNC-0041 | Security Boundary | security/integration-security-boundary-v1.md | 02_Editorial OS / Security | Ready to Sync | Integration security model. |
| SYNC-0042 | Technical Backlog | engineering/technical-backlog.md | 02_Editorial OS / Engineering | Ready to Sync | Prioritized delivery backlog. |
| SYNC-0043 | Integration Evaluation Matrix | integrations/integration-evaluation-matrix.md | 02_Editorial OS / Integration Lab | Ready to Sync | TryPost/Postiz/BrightBean/Mixpost/Socioboard evaluation. |
| SYNC-0044 | Publication One Readiness | publishing/readiness/NKS-PUB-000001-publication-readiness.md | 03_Medium Drafts / Publication Pipeline | Ready to Sync | Gate checklist for first publication. |
| SYNC-0045 | Knowledge Roadmap | roadmap/knowledge-roadmap.md | 02_Editorial OS / Roadmap | Ready to Sync | Capability-driven extraction roadmap. |

## Rule

Whenever GitHub is used as fallback because Drive writes are unavailable, add the artifact here before considering the sprint task complete.