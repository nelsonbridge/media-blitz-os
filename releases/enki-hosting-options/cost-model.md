# Hosting Cost Model

Budget governing Sprint 24 execution: **$0 external services**.

No provider account, paid plan, infrastructure resource, domain, security product, or support plan is purchased by this sprint.

## Modeling rules

1. Published free allowances establish feasibility for low-volume architecture rehearsal only.
2. A free allowance is not a production capacity guarantee.
3. Provider pricing can change; figures must be revalidated before a hosting decision or deployment.
4. Human operations, migration effort, incident coordination, and maintenance are real costs even when provider invoices are $0.
5. Any architecture that can silently exceed $0 requires budget alerts, quotas, or hard-stop controls before use under the current budget policy.

## Planning ranges

| Option | Low-volume monthly planning range | $0 prototype assessment | Major cost drivers |
|---|---:|---|---|
| CF-NATIVE | $0–25 | Strong | Worker CPU/request volume, D1 operations/storage, R2 operations/storage |
| GCP-NATIVE | $0–50 | Conditional on staying within quotas | Cloud Run compute, Firestore operations, storage, backup/PITR, network egress |
| AWS-NATIVE | $1–50 | Not assumed | Lambda compute, DynamoDB usage, S3, networking, logging, security services |
| CF-NEON-R2 | $0–30 | Strong for low-volume rehearsal | Worker usage, Neon compute/storage/transfer, R2 operations/storage |
| GCP-NEON-R2 | $0–50 | Conditional | Cloud Run, Neon compute/storage/transfer, cross-provider traffic, R2 |
| PORTABLE-CONTAINER-POSTGRES-OBJECT | $0–75 | Contract rehearsal only | Selected container, Postgres, object storage, network, adapter operations |

These are architecture-model ranges, not quoted prices.

## Zero-dollar shortlist implications

`CF-NATIVE` has the clearest zero-cost prototype posture because its evaluated runtime, database, and object plane each publish free allowances within one provider ecosystem.

`CF-NEON-R2` also has a credible $0 rehearsal path using Workers, Neon Free, and R2 allowances, but cross-provider connectivity and runtime adaptation must be validated.

`GCP-NEON-R2` can plausibly invoice $0 at very low usage, but it requires explicit billing guardrails and introduces more provider surfaces. It is retained because it minimizes application-runtime changes, not because it is the simplest $0 design.

## Production cost categories not resolved here

- Private networking and interconnects.
- Production backup, PITR, restore testing, and multi-region recovery.
- Managed KMS and per-tenant key operations.
- Production secrets management.
- Centralized logs and long-term telemetry retention.
- WAF, DDoS, identity, and security monitoring beyond free allowances.
- Premium support.
- Independent penetration testing.
- Compliance assessments and contractual requirements.

Sprint 24 completion does not authorize spending in any of these categories.
