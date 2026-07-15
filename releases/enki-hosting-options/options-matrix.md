# Hosting Options Matrix

All cost figures below are Enki planning ranges for low-volume architecture rehearsal. They are not provider quotes, production guarantees, or commitments. The sprint itself spends $0 and provisions nothing.

| Option | Pattern | Runtime | Canonical data | Evidence / object plane | Zero-cost prototype | Planning range / month | Primary advantage | Primary risk |
|---|---|---|---|---|---|---:|---|---|
| CF-NATIVE | Single cloud | Cloudflare Workers | D1 | R2 | Yes | $0–25 | Lowest operational surface and strongest literal $0 prototype fit | Python runtime and relational-data adaptation |
| GCP-NATIVE | Single cloud | Cloud Run | Firestore | Cloud Storage | Yes, within quota | $0–50 | Current Python service fits container runtime | Firestore data-model change; paid backup/PITR paths |
| AWS-NATIVE | Single cloud | Lambda | DynamoDB | S3 candidate | Not assumed under absolute-zero rule | $1–50 | Mature service and IAM portfolio | Rewrite, IAM complexity, adjacent service charges |
| CF-NEON-R2 | Provider split | Workers | Neon Postgres | R2 | Yes | $0–30 | Relational canonical custody separated from edge compute | Runtime adaptation and public-TLS free-tier DB path |
| GCP-NEON-R2 | Control/data split | Cloud Run | Neon Postgres | R2 | Yes, within quota | $0–50 | Lowest-change split-cloud path for current Python runtime | Three-provider trust, latency, egress, and support complexity |
| PORTABLE-CONTAINER-POSTGRES-OBJECT | Portability hybrid | OCI container | Postgres-compatible | S3-compatible | Yes for contract rehearsal | $0–75 | Best provider-exit posture | Adapter maintenance and lowest-common-denominator risk |

## Current official free-tier signals used in the analysis

- Cloudflare Workers publishes a free request allowance; D1 publishes free row-operation and storage allowances; R2 publishes a free storage/operation allowance and no internet egress charge.
- Google Cloud Run publishes a request-based free compute/request allowance. Firestore publishes free storage and daily operation quotas, while backup/PITR/restore features remain outside free usage. Cloud Storage publishes an Always Free allowance in qualifying regions.
- AWS Lambda and DynamoDB publish substantial free allowances, but this package does not assume the complete AWS architecture can be hard-capped at $0 once storage, networking, backup, security, and adjacent services are included.
- Neon publishes a $0 free Postgres plan with scale-to-zero behavior and no credit card requirement; production private networking and higher service guarantees are not inferred from that free plan.
- Supabase and Azure Functions were reviewed as alternatives. Supabase free projects may pause when inactive, and Azure Functions' free compute grant does not make associated storage free.

## Prerequisite mapping

Every option leaves the same seven Sprint 23 production controls **UNRESOLVED** until a concrete deployment is provisioned and separately validated:

1. Cloud IAM.
2. Production identity federation.
3. Managed database row-level isolation.
4. Network segmentation.
5. Per-tenant production key management.
6. Production secrets management.
7. Independent penetration testing.

A provider offering a capability is not evidence that Enki has configured or validated that capability.

## Shortlist rationale

### CF-NATIVE

Retained because it offers the cleanest $0 prototype and smallest provider footprint. It is not the default choice because the current Python/Pydantic service and relational canonical-storage assumptions would require the largest adaptation.

### CF-NEON-R2

Retained because it creates meaningful provider separation while preserving Postgres for canonical knowledge. It is not the default choice because edge-runtime adaptation and free-tier public database connectivity create nontrivial validation work.

### GCP-NEON-R2

Retained because Cloud Run preserves the current Python runtime while Neon preserves Postgres semantics and R2 provides a separate evidence/export plane. It is not the default choice because three-provider operations may cost more in complexity than they return in resilience.

Split cloud is therefore a candidate, not an axiom. The hosting-direction decision must be based on measured validation results, operational capacity, and acceptable failure domains.
