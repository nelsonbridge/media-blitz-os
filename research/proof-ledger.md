# Proof Ledger

## Purpose

The Proof Ledger tracks source lineage, proof posture, and public-readiness risk for publication candidates.

## Status Values

- `Proof Needed`
- `Experiential Proof Logged`
- `Document Proof Logged`
- `Repository Proof Logged`
- `Public Verification Needed`
- `Public Verification Complete`
- `Citation Insertion Needed`
- `Ready for Editorial Review`
- `Blocked`

## Proof Categories

- Experiential
- Document-derived
- Repository-derived
- Publicly verified
- Quantitative
- Unverified

## Publication Proof Register

| Publication ID | Title | Source Artifact | Source Record | Proof Category | Proof Status | Public Risk | Notes |
|---|---|---|---|---|---|---|---|
| NKS-PUB-000001 | The Corpus Is Manufactured, Not Found | NKS-ART-000001 | NKS-SRC-000001 | Experiential / Repository-derived | Repository Proof Logged | Low | Architecture and implemented repo artifacts support claim. |
| NKS-PUB-000002 | Media Blitz Is the Publishing Subsystem, Not the System | NKS-ART-000002 | NKS-SRC-000001 | Experiential / Repository-derived | Repository Proof Logged | Low | Internal system architecture claim. |
| NKS-PUB-000003 | GitHub Is the Control Plane for This Knowledge System | NKS-ART-000003 | NKS-SRC-000001 | Repository-derived | Repository Proof Logged | Low | Supported by repo structure and state files. |
| NKS-PUB-000004 | The No Idle State Rule | NKS-ART-000004 | NKS-SRC-000001 | Repository-derived / Experiential | Repository Proof Logged | Low | Governance rule exists in OS Constitution. |
| NKS-PUB-000005 | Clarity Is an Economic Instrument | NKS-ART-000005 | NKS-SRC-000002 | Experiential / Document-derived | Document Proof Logged | Medium | Avoid quantitative claims unless verified. |
| NKS-PUB-000006 | Coherence Beats Compliance | NKS-ART-000006 | NKS-SRC-000002 | Experiential / Document-derived | Document Proof Logged | Medium | Avoid broad process/Agile claims unless verified. |
| NKS-PUB-000007 | How Executives Turn Ambiguity into Capability | NKS-ART-000007 | NKS-SRC-000002 | Experiential / Document-derived | Document Proof Logged | Medium | Needs examples before publication. |
| NKS-PUB-000008 | The Resume Should Not Be the First Signal | NKS-ART-000008 | NKS-SRC-000002 | Strategic / Experiential | Proof Needed | Medium | Recruiter-market claims require caution or sourcing. |
| NKS-PUB-000009 | Agentic AI Requires Human Oversight Architecture | NKS-ART-000009 | NKS-SRC-000003 | Document-derived / Publicly verified | Citation Insertion Needed | Medium | Verification note exists; citations needed before release. |
| NKS-PUB-000010 | Security Automation Needs Guardrails | NKS-ART-000010 | NKS-SRC-000003 | Document-derived / Publicly verified | Citation Insertion Needed | Medium | Verification note exists; citations needed before release. |
| NKS-PUB-000011 | Agentic DevOps Beyond CI/CD | NKS-ART-000011 | NKS-SRC-000003 | Document-derived / Publicly verified | Citation Insertion Needed | Medium | Verification note exists; citations needed before release. |
| NKS-PUB-000012 | Self-Healing Systems Need Governance | NKS-ART-000012 | NKS-SRC-000003 | Document-derived / Publicly verified | Citation Insertion Needed | Medium | Verification note exists; citations needed before release. |

## Rule

No public release until the proof status is at least `Ready for Editorial Review` and the user approves the final artifact.
