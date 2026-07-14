# Sprint 2 Known Issues

- Production OIDC is not implemented; JWT bootstrap is local/test only.
- Live Kafka broker smoke may be unverified (`make smoke-api-kafka` SKIPPED by default).
- No persistent retry topics or production DLQ adapter.
- No application PostgreSQL/Redis client runtime yet.
- Registry Loader is local-file and read-only.
- Stacked Sprint 2 PRs must merge in order (#208A → #208B → #209 → #210).
- Kafka in-memory test runtime does not emulate full consumer-group rebalance semantics.
- Trading Engine Foundation (#211) is out of scope for this gate.
