# NKS-GPH-000001 — Foundational Operating Model Graph

```yaml
graph_record:
  graph_id: NKS-GPH-000001
  title: Foundational Operating Model
  nodes:
    - id: NKS-SRC-000001
      type: Source
      title: Initial NKS Architecture Source Cluster
      path: corpus/sources/NKS-SRC-000001*
    - id: NKS-ART-000001
      type: Artifact
      title: The Corpus Is Manufactured, Not Found
      path: corpus/artifacts/NKS-ART-000001*
    - id: NKS-COH-000001
      type: Coherence
      title: Publication One Cluster Coherence Scorecard
      path: corpus/coherence/NKS-COH-000001-publication-one-cluster.md
    - id: NKS-VIS-000001
      type: Visual
      title: Foundational Visual Package
      path: visuals/packages/NKS-VIS-000001.md
    - id: NKS-DGM-000001
      type: Visual
      title: Knowledge Manufacturing Loop
      path: visuals/generated/NKS-DGM-000001-knowledge-manufacturing-loop.svg
    - id: NKS-HRO-000001
      type: Visual
      title: Knowledge System Hero
      path: visuals/generated/NKS-HRO-000001-knowledge-system-hero.svg
    - id: NKS-CAR-000001
      type: Visual
      title: Corpus Manufacturing Carousel
      path: visuals/generated/NKS-CAR-000001-carousel-deck.svg
    - id: NKS-QTC-000001
      type: Visual
      title: Publishing Is Downstream Quote Card
      path: visuals/generated/NKS-QTC-000001-publishing-downstream.svg
    - id: NKS-PIN-000001
      type: Visual
      title: Knowledge Manufacturing Pipeline Pinterest Graphic
      path: visuals/generated/NKS-PIN-000001-knowledge-manufacturing-pipeline.svg
    - id: NKS-PUB-000001
      type: Package
      title: The Corpus Is Manufactured, Not Found
      path: publishing/medium-drafts/NKS-PUB-000001-the-corpus-is-manufactured-not-found-draft.md
    - id: NKS-CON-PUB-000001
      type: Contract
      title: Publication Contract Payload for NKS-PUB-000001
      path: contracts/payloads/NKS-PUB-000001-publication-contract.yaml
    - id: CAP-CORPUS-MANUFACTURING
      type: Capability
      title: Corpus Manufacturing
      path: roadmap/knowledge-roadmap.md
  edges:
    - from: NKS-ART-000001
      edge: derived_from
      to: NKS-SRC-000001
      rationale: Artifact emerged from the initial architecture/source cluster.
    - from: NKS-ART-000001
      edge: matures
      to: CAP-CORPUS-MANUFACTURING
      rationale: Artifact defines the manufacturing premise for the corpus.
    - from: NKS-COH-000001
      edge: evaluates
      to: NKS-ART-000001
      rationale: Scorecard evaluates strategic coherence and capability contribution.
    - from: NKS-PUB-000001
      edge: packaged_as
      to: NKS-ART-000001
      rationale: Publication package expresses the artifact for an external reader.
    - from: NKS-PUB-000001
      edge: bounded_by
      to: NKS-COH-000001
      rationale: Coherence scorecard includes proof and risk boundaries.
    - from: NKS-VIS-000001
      edge: represents
      to: NKS-ART-000001
      rationale: Visual package represents the core artifact across surfaces.
    - from: NKS-DGM-000001
      edge: represented_by
      to: NKS-ART-000001
      rationale: Signature diagram represents the knowledge manufacturing loop.
    - from: NKS-HRO-000001
      edge: represented_by
      to: NKS-PUB-000001
      rationale: Hero image represents the publication surface.
    - from: NKS-CAR-000001
      edge: represented_by
      to: NKS-PUB-000001
      rationale: Carousel translates the article into a multi-slide visual narrative.
    - from: NKS-QTC-000001
      edge: represented_by
      to: NKS-PUB-000001
      rationale: Quote card extracts the core public-facing line.
    - from: NKS-PIN-000001
      edge: represented_by
      to: NKS-ART-000001
      rationale: Pinterest vertical represents the operating pipeline as evergreen knowledge.
    - from: NKS-CON-PUB-000001
      edge: enables
      to: NKS-PUB-000001
      rationale: Contract payload enables adapter validation and future distribution.
```

## Status

Seed graph complete.