# Human Deployment Decision Request

Candidate: `enki-hosted-1.0-rc2`

Decision state: **PENDING_HUMAN_DECISION**

This request does not imply that deployment is ready or recommended. The candidate currently reports:

- Software readiness: `PASS_TEST`
- Hosted architecture validation: `BLOCKED`
- Zero-cost operating envelope: `PARTIAL`
- Production deployment readiness: `BLOCKED`

The human decision authority may select exactly one disposition:

1. `APPROVE`
2. `APPROVE_WITH_CONDITIONS`
3. `DEFER`
4. `REJECT`

Any human decision should identify the candidate hash and, when applicable, explicit conditions, accepted risks, evidence waivers, or reasons for deferral/rejection.

Automation, model output, CI success, sprint completion, architecture selection, or TEST approval cannot issue this deployment decision.
