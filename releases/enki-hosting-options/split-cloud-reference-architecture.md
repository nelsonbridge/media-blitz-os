# Split-Cloud Reference Architecture

Reference finalist: `GCP-NEON-R2`.

```text
Consumer suites
    |
    v
Google Cloud Run
Enki API / application / policy control plane
    |
    | TLS + scoped credentials
    v
Neon Postgres
Canonical knowledge data plane
    |
    | governed export / evidence flow
    v
Cloudflare R2
Evidence, portability, and recovery artifact plane
```

## Control plane

Cloud Run hosts the current Python/Pydantic-shaped Enki application boundary. It performs contract resolution, boundary authorization, policy evaluation, governed transaction orchestration, receipts, and consumer API handling. It does not become independent canonical authority merely because it runs separately from the data plane.

## Canonical data plane

Neon Postgres is the relational canonical-data candidate. The separation preserves SQL/Postgres semantics while preventing the runtime provider from also being the only canonical-data provider. Production row-level isolation, private connectivity, tenant-key strategy, and database recovery still require concrete validation.

## Evidence and portability plane

R2 is the independent object/evidence candidate for immutable evidence packages, governed exports, recovery bundles, and provider-exit artifacts. Evidence stored there does not become canonical truth by virtue of location.

## Trust boundaries

1. Consumer to Cloud Run identity and authorization.
2. Cloud Run workload identity to Neon database credential.
3. Cloud Run workload identity to R2 scoped credential.
4. Neon canonical data custody boundary.
5. R2 evidence and export custody boundary.
6. Human administrative access boundary across all provider accounts.

## Failure domains

- Cloud Run outage: API/control plane unavailable while canonical data and evidence providers may remain intact.
- Neon outage: canonical state operations pause; runtime must fail closed rather than substitute stale evidence as authority.
- R2 outage: evidence/export persistence pauses; canonical mutations requiring terminal evidence must fail or enter recoverable state according to governed transaction rules.
- Cross-provider network partition: operations must classify interruption, retry, rollback, or recovery deterministically.
- Credential compromise at one provider must not automatically confer administrative authority at the others.

## Data flow constraints

Canonical mutations flow through Cloud Run governance to Neon. Terminal evidence and governed exports flow to R2 only after exact authority and content hashes are resolved. Reads returned to downstream suites remain filtered by privacy, purpose, audience, and boundary contracts. Cross-cloud replication must never widen disclosure or turn evidence copies into alternate canonical writers.

## Provider-split alternative

`CF-NEON-R2` moves the runtime/control plane to Cloudflare Workers while retaining Neon canonical data and R2 evidence. This reduces provider count to two and may improve edge cost characteristics, but requires more adaptation from the existing Python service shape.

## Split-cloud selection criteria

Prefer split cloud when independent canonical custody, evidence-plane portability, or provider-failure separation materially outweighs added latency, egress, credential distribution, incident coordination, and operational burden. Reject it when measured cross-cloud overhead or support complexity exceeds the resilience gained.
