# Sprint 2 Risk Summary

| Risk | Mitigation |
|------|------------|
| Live Kafka unverified | Broker-free #208A/#208B tests required; live smoke optional |
| Local JWT bootstrap misuse | Disabled in staging/production via settings invariants |
| Registry misconfiguration | Fail-closed startup when required registries missing/invalid |
| Stacked PR divergence | Gate runs on #209 tip; #211 excluded |
| Evidence secret leakage | Pattern checks on logs and artifacts |
