# Risk Summary — Sprint 1

- **High**: Without Kind/ArgoCD runtime evidence, production-like readiness is unproven.
- **Medium**: Backup/restore is smoke-level only.
- **Medium**: Secrets validation detects patterns; it cannot prove external secret stores are correctly populated.
- **Low**: Helm chart currently declares inventory/config; full stateful workload rollout is environment-controlled.
