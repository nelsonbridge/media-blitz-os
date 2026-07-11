# Primary-Source Verification — NKS-PUB-000009 through NKS-PUB-000012

## Scope

Current primary-source verification for the bounded technical and governance claims in:

- NKS-PUB-000009 — Agentic AI Requires Human Oversight Architecture
- NKS-PUB-000010 — Security Automation Needs Guardrails
- NKS-PUB-000011 — Agentic DevOps Beyond CI/CD
- NKS-PUB-000012 — Self-Healing Systems Need Governance

## Sources Reviewed

### NIST AI 600-1 — Generative Artificial Intelligence Profile

Published July 2024 by the National Institute of Standards and Technology.

Relevant verified guidance includes:

- defining organizational responsibilities for monitoring and incident review;
- recording human oversight roles in system inventories;
- establishing incident-response ownership and procedures;
- defining acceptable-use and refusal criteria;
- maintaining continuous monitoring, fallback, recovery, and deactivation criteria;
- enabling appeal, override, escalation, and change management;
- retaining evidence for test, evaluation, validation, and verification.

Canonical source:

https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

DOI:

https://doi.org/10.6028/NIST.AI.600-1

### NIST SP 800-218 — Secure Software Development Framework Version 1.1

NIST describes the SSDF as a core set of secure software-development practices integrated throughout software-development lifecycle implementations. Its stated purpose includes reducing released vulnerabilities, mitigating exploitation impact, and addressing root causes.

Canonical source:

https://csrc.nist.gov/pubs/sp/800/218/final

### SLSA Specification Version 1.2

The current approved SLSA specification defines levels and tracks for incrementally improving software supply-chain security. It includes source and build verification, artifact provenance, attestations, and verified properties.

Canonical source:

https://slsa.dev/spec/v1.2/

### NIST Cybersecurity Framework 2.0

NIST CSF 2.0 is intended to help organizations understand and improve cybersecurity-risk management. Its current framework explicitly includes governance as part of cybersecurity-risk management.

Canonical source:

https://www.nist.gov/cyberframework

### Kubernetes Self-Healing Documentation

Current Kubernetes documentation describes bounded self-healing mechanisms including container restarts, replica replacement, persistent-volume recovery behavior, and removal of failed endpoints. It also explicitly notes limitations: storage recovery may require separate steps, and restarting containers does not repair underlying application defects.

Canonical source:

https://kubernetes.io/docs/concepts/architecture/self-healing/

## Publication Findings

### NKS-PUB-000009

**Result: PASS WITH BOUNDARIES.**

NIST directly supports the need for explicit oversight roles, monitoring, incident response, escalation, fallback, override, recovery, and deactivation criteria. The publication must remain framed as architecture and governance rather than claiming that oversight guarantees safety.

### NKS-PUB-000010

**Result: PASS WITH BOUNDARIES.**

NIST AI risk guidance, CSF 2.0, and SSDF support explicit governance, lifecycle security, incident response, monitoring, and risk controls. The publication may argue that security automation needs permissions, approval boundaries, rollback, escalation, and audit evidence, but may not claim measured risk reduction or universal safety.

### NKS-PUB-000011

**Result: PASS WITH BOUNDARIES.**

SSDF and SLSA support integrating vulnerability management, secure lifecycle practices, provenance, artifact verification, and source/build assurance into delivery systems. The publication may frame DevOps as evidence-informed release-risk governance, but may not claim that agentic systems currently replace engineering judgment or autonomously make safe release decisions.

### NKS-PUB-000012

**Result: PASS WITH BOUNDARIES.**

Kubernetes provides a current concrete example of bounded self-healing and explicitly documents limitations. NIST guidance supports monitoring, incident response, recovery, fallback, deactivation, and accountable oversight. The publication may argue that remediation authority requires governance, but may not claim that every self-healing implementation requires identical controls or that automation guarantees reliability.

## Unsupported Claims Retained

The reviewed sources do not establish:

- product-specific capabilities beyond their current documentation;
- universal safety or reliability guarantees;
- quantified incident, deployment, cost, or performance improvements;
- that human oversight alone is sufficient for risk management;
- that autonomous action should replace accountable human judgment.

## Verification Result

All four proof gates may advance to `ready` provided the public drafts retain these boundaries and include citations to the primary sources above.
