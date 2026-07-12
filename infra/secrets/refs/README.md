# Secret references (Issue #196)

This directory holds **references only**.

- Manifests use `${SECRETREF:...}` placeholders.
- Real credentials are injected at deploy time.
- `.env.example` documents names without values.
- `validate-secrets` fails if default or embedded credentials are detected.
