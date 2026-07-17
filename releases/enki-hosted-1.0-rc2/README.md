# Enki Hosted 1.0 RC2

> Release-candidate evidence package. This package is not production approval and does not authorize deployment.

Candidate: `enki-hosted-1.0-rc2`

Evidence baseline: `219bf709b3adae247085f4610bae4fe86059a5f9`

Architecture source of truth:

- `architecture/enki/enki-split-cloud-reference-architecture.md`
- `architecture/enki/enki-canonical-nine-layer-architecture.md`

## Separate readiness conclusions

1. **Software readiness:** repository-local TEST validation passes for the provider-neutral Enki core, temporal authority, governed retrieval, model-use boundary, downstream consumer boundaries, multi-consumer operations, recovery, portability, and production-control readiness contracts.
2. **Hosted architecture validation:** blocked. The common hosted-validation foundation exists, but CF-NATIVE is blocked on provider TEST capabilities and CF-NEON-R2 / GCP-NEON-R2 campaigns have not been executed. No finalist is validated or selected.
3. **Zero-cost operating envelope:** partial. Repository-local and CI TEST execution remains within the absolute `$0` external-services boundary. The actual hosted finalist quota, egress, storage, latency, and teardown envelope is unvalidated.
4. **Production deployment readiness:** blocked. Cloud IAM, production identity federation, managed-database row isolation, network segmentation, per-tenant production key management, production secrets management, and independent penetration testing all lack qualifying production evidence.

## Decision state

`PENDING_HUMAN_DECISION`

Supported human dispositions:

- `APPROVE`
- `APPROVE_WITH_CONDITIONS`
- `DEFER`
- `REJECT`

Automation and model output cannot select a disposition. The release candidate remains non-production until explicit human deployment authority is recorded separately.
