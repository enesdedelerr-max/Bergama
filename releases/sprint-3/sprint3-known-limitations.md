# Sprint 3 Known Limitations

- At-least-once delivery only; exactly-once delivery is not claimed.
- Iceberg writes are append-only.
- Deduplication is process-local and not durable across restarts.
- Quality metrics are process-local.
- Replay ordering differs from original Kafka order.
- Multi-table Iceberg snapshots are not atomic.
- Finnhub and SEC connectors are bounded refresh sources.
- Optional provider live smokes may be SKIPPED when credentials or entitlements are unavailable.
- No external alert delivery.
- No Prometheus exporter.
- Production OIDC remains out of Sprint 3 scope if not already configured.
