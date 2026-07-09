# NKS-GPH-000003 — AI Governance Cluster Graph

```yaml
graph_record:
  graph_id: NKS-GPH-000003
  title: Agentic AI Governance / Security / DevOps / Resiliency Cluster
  nodes:
    - id: NKS-SRC-000003
      type: Source
      title: Agentic AI Security Whitepaper Source Cluster
      path: corpus/sources/NKS-SRC-000003-agentic-ai-security-whitepapers.md
    - id: NKS-ART-000009
      type: Artifact
      title: Agentic AI Requires Human Oversight Architecture
      path: corpus/artifacts/NKS-ART-000009*
    - id: NKS-ART-000010
      type: Artifact
      title: Security Automation Needs Guardrails
      path: corpus/artifacts/NKS-ART-000010*
    - id: NKS-ART-000011
      type: Artifact
      title: Agentic DevOps Beyond CI/CD
      path: corpus/artifacts/NKS-ART-000011*
    - id: NKS-ART-000012
      type: Artifact
      title: Self-Healing Systems Need Governance
      path: corpus/artifacts/NKS-ART-000012*
    - id: NKS-COH-000003
      type: Coherence
      title: AI Governance Cluster Coherence Scorecard
      path: corpus/coherence/NKS-COH-000003-ai-governance-cluster.md
    - id: CAP-AI-GOVERNANCE
      type: Capability
      title: AI Governance Architecture
      path: roadmap/knowledge-roadmap.md
    - id: CAP-PROOF-SYSTEM
      type: Capability
      title: Proof System
      path: research/proof-ledger.md
  edges:
    - from: NKS-ART-000009
      edge: derived_from
      to: NKS-SRC-000003
      rationale: Human oversight architecture extracted from agentic AI whitepaper material.
    - from: NKS-ART-000010
      edge: derived_from
      to: NKS-SRC-000003
      rationale: Guardrails concept extracted from security automation material.
    - from: NKS-ART-000011
      edge: derived_from
      to: NKS-SRC-000003
      rationale: Agentic DevOps concept extracted from DevOps whitepaper material.
    - from: NKS-ART-000012
      edge: derived_from
      to: NKS-SRC-000003
      rationale: Self-healing systems governance extracted from monitoring/resiliency material.
    - from: NKS-ART-000009
      edge: supports
      to: NKS-ART-000010
      rationale: Security automation guardrails require human oversight architecture.
    - from: NKS-ART-000011
      edge: supports
      to: NKS-ART-000012
      rationale: Agentic DevOps and self-healing systems share operational governance boundaries.
    - from: NKS-ART-000010
      edge: supports
      to: NKS-ART-000012
      rationale: Guardrails are necessary for safe autonomous remediation.
    - from: NKS-COH-000003
      edge: evaluates
      to: NKS-SRC-000003
      rationale: The scorecard evaluates the AI governance source cluster and derived artifacts.
    - from: NKS-ART-000009
      edge: matures
      to: CAP-AI-GOVERNANCE
      rationale: Oversight architecture matures reusable AI governance capability.
    - from: NKS-ART-000010
      edge: matures
      to: CAP-PROOF-SYSTEM
      rationale: Guardrails and proof boundaries strengthen claim control and governance.
```

## Status

Seed graph complete.