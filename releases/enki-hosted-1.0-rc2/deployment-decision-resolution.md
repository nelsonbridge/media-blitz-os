# Enki Hosted RC2 Deployment Decision Resolution

## Human disposition

- Candidate: `enki-hosted-1.0-rc2`
- Candidate SHA-256: `sha256:c443b2ff6eeb00e6682f6c56dc00cd14bdee53940432e1b9d12e9f473c9346b4`
- Disposition: `APPROVE`
- Authority: `HUMAN`
- Authority identity: `nelsonbridge`
- Evidence source: `https://github.com/nelsonbridge/media-blitz-os/issues/123#issuecomment-5008644257`
- Resolution SHA-256: `sha256:cfb15d11968a6c0d0b63d73f8e5d6b1e38d4332cff73794c3361c887eb0e08e0`

The approved disposition is bound to the exact RC2 candidate hash. No conditions, accepted-risk declarations, or evidence waivers were added to the human decision.

## Architecture lock

The approved candidate authorizes Sprint 37 to lock the candidate-bound split-cloud reference baseline:

- Architecture: `CF-NEON-R2`
- Compute and edge runtime: Cloudflare Workers
- Canonical structured-data system of record: Neon Postgres
- Evidence and object plane: Cloudflare R2
- Optional provider services: none authorized by this lock
- Architecture-lock SHA-256: `sha256:8b79cdbcafd9080a22471fa12e3a176ee1da9963471fa494b90dca62af0d4813`

## Boundaries preserved

This approval and architecture lock do **not** claim that production deployment is ready. They do not create or authorize:

- production credentials;
- paid external services or spending above the standing `$0` boundary;
- production data or production effects;
- optional Cloudflare/provider services;
- completion of blocked or unexecuted hosted TEST campaigns;
- satisfaction of unresolved production-control prerequisites.

RC2 hosted architecture validation remains `BLOCKED`, and RC2 production deployment readiness remains `BLOCKED`, until their separate evidence requirements are satisfied or explicitly governed otherwise.

The architecture lock therefore establishes the implementation baseline for architecture-dependent work while preserving all external-capability, spending, credential, production-control, and production-execution gates as fail-closed.
