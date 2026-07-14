# Enki 0.1.0-rc1 Known Limitations

1. **Internal evidence only.** The candidate proves TEST behavior and cannot satisfy a PRODUCTION gate.
2. **No external platform validation.** Medium, LinkedIn, model providers, analytics systems, and other third-party behavior are not exercised.
3. **No real audience calibration.** Controlled real-human TEST feedback is not equivalent to public audience response.
4. **Filesystem and GitHub scope.** Adapter parity applies only to the declared shared append/get/list and governed recovery surfaces.
5. **No production performance claim.** Current tests validate correctness and bounded runtime behavior, not enterprise-scale throughput or latency.
6. **Human authority remains required.** Release, consent, public identity, privacy, and production-effect decisions cannot be inferred.
7. **Prediction remains downstream.** Enki does not canonize probabilistic model output without a separately governed operation.
8. **Production adapters are future work.** Each external integration requires independent capability review, threat modeling, secrets handling, and authorization.
9. **Release candidate, not release.** `READY_FOR_HUMAN_DECISION` is not an approval or deployment state.
