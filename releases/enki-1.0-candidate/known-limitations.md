# Known Limitations and Production Prerequisites

## Evidence boundary

All qualifying implementation and campaign evidence in the Enki 1.0-rc1 package is TEST evidence unless a source explicitly states otherwise. Repository-local success cannot be promoted into a production-infrastructure claim by inference.

Sprint 16 validates logical namespace, tenant, subject, domain, audience, and execution-context boundaries plus shared and physically separated local adapters. It does **not** certify cloud IAM, managed database isolation, production network controls, production key separation, production secret handling, or externally tested multitenancy.

## Unresolved physical production controls

| Control | Status | Reason |
|---|---|---|
| Cloud IAM | UNRESOLVED | No production cloud IAM environment or qualifying external validation exists under the zero-dollar boundary. |
| Production identity federation | UNRESOLVED | Not provisioned or independently validated. |
| Managed database row-level isolation | UNRESOLVED | No managed production database or qualifying row-level isolation validation exists. |
| Network segmentation | UNRESOLVED | No production network segmentation has been provisioned or independently validated. |
| Per-tenant production key management | UNRESOLVED | No production per-tenant key service has been provisioned or independently validated. |
| Production secrets management | UNRESOLVED | No production secret store or production secret lifecycle has been independently validated. |
| Independent penetration testing | UNRESOLVED | No independent external penetration test has been performed. |

## Additional limitations

- Performance results are governed synthetic TEST measurements, not production capacity guarantees.
- No real production tenant, private production corpus, or production credential is included in the candidate proof.
- No paid external security or infrastructure service was purchased to manufacture evidence.
- No local no-effect adapter proves third-party delivery reliability or provider-specific production behavior.
- The stable consumer contract proves v1.0 semantics and fail-closed compatibility behavior; future versions require separately governed compatibility evidence.
- Downstream product proofs establish scoped consumption and noncanonical output boundaries, not product-market fitness or production launch readiness.
- A human decision is still required before any production-control validation or deployment program begins.
