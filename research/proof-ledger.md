# Proof Ledger

## Purpose

The Proof Ledger tracks source lineage, proof posture, narrative-arc readiness, and public-readiness risk for publication candidates.

## Proof Status Values

- `Proof Needed`
- `Experiential Proof Logged`
- `Document Proof Logged`
- `Repository Proof Logged`
- `Public Verification Needed`
- `Public Verification Complete`
- `Citation Insertion Needed`
- `Ready for Editorial Review`
- `Blocked`

## Arc Status Values

- `Arc Needed`
- `Partial Arc`
- `Arc Drafted`
- `Arc Review Needed`
- `Arc Approved`

## Proof Categories

- Experiential
- Document-derived
- Repository-derived
- Publicly verified
- Quantitative
- Unverified

## Publication Proof Register

| Publication ID | Title | Source Artifact | Source Record | Proof Category | Proof Status | Arc Status | Public Risk | Notes |
|---|---|---|---|---|---|---|---|---|
| NKS-PUB-000001 | The Corpus Is Manufactured, Not Found | NKS-ART-000001 | NKS-SRC-000001 | Experiential / Repository-derived | Repository Proof Logged | Partial Arc | Low | Architecture and implemented repo artifacts support claim; needs stronger application and invitation. |
| NKS-PUB-000002 | Media Blitz Is the Publishing Subsystem, Not the System | NKS-ART-000002 | NKS-SRC-000001 | Experiential / Repository-derived | Repository Proof Logged | Partial Arc | Low | Internal architecture claim; needs clearer reader application. |
| NKS-PUB-000003 | GitHub Is the Control Plane for This Knowledge System | NKS-ART-000003 | NKS-SRC-000001 | Repository-derived | Repository Proof Logged | Partial Arc | Low | Supported by repo structure and state files; needs stronger invitation. |
| NKS-PUB-000004 | The No Idle State Rule | NKS-ART-000004 | NKS-SRC-000001 | Repository-derived / Experiential | Repository Proof Logged | Partial Arc | Low | Governance rule exists in OS Constitution; needs reader-facing invitation. |
| NKS-PUB-000005 | Clarity Is an Economic Instrument | NKS-ART-000005 | NKS-SRC-000002 | Experiential / Document-derived | Document Proof Logged | Partial Arc | Medium | Avoid quantitative claims unless verified; needs proof examples. |
| NKS-PUB-000006 | Coherence Beats Compliance | NKS-ART-000006 | NKS-SRC-000002 | Experiential / Document-derived | Document Proof Logged | Partial Arc | Medium | Avoid broad process/Agile claims unless verified; needs application expansion. |
| NKS-PUB-000007 | How Executives Turn Ambiguity into Capability | NKS-ART-000007 | NKS-SRC-000002 | Experiential / Document-derived | Document Proof Logged | Partial Arc | Medium | Needs examples before publication. |
| NKS-PUB-000008 | The Resume Should Not Be the First Signal | NKS-ART-000008 | NKS-SRC-000002 | Strategic / Experiential | Proof Needed | Partial Arc | Medium | Recruiter-market claims require caution or sourcing; application needs strengthening. |
| NKS-PUB-000009 | Agentic AI Requires Human Oversight Architecture | NKS-ART-000009 | NKS-SRC-000003 | Document-derived / Publicly verified | Citation Insertion Needed | Partial Arc | Medium | Verification note exists; citations and final invitation needed before release. |
| NKS-PUB-000010 | Security Automation Needs Guardrails | NKS-ART-000010 | NKS-SRC-000003 | Document-derived / Publicly verified | Citation Insertion Needed | Partial Arc | Medium | Verification note exists; citations and final invitation needed before release. |
| NKS-PUB-000011 | Agentic DevOps Beyond CI/CD | NKS-ART-000011 | NKS-SRC-000003 | Document-derived / Publicly verified | Citation Insertion Needed | Partial Arc | Medium | Verification note exists; citations and final invitation needed before release. |
| NKS-PUB-000012 | Self-Healing Systems Need Governance | NKS-ART-000012 | NKS-SRC-000003 | Document-derived / Publicly verified | Citation Insertion Needed | Partial Arc | Medium | Verification note exists; citations and final invitation needed before release. |

## Release Gate

No public release until:

1. Source lineage is recorded.
2. Proof status is at least `Ready for Editorial Review`.
3. Arc status is at least `Arc Review Needed`.
4. Public risk is reviewed.
5. User approval is recorded.

## Operating Principle

Source first. Proof second. Narrative arc third. Publication fourth.
