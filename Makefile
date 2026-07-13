# Sprint 1 — Infrastructure foundation gate (spec-aligned)

export PATH := $(HOME)/.local/bin:$(PATH)
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT := $(abspath .)

API_DIR := $(ROOT)/apps/api

.PHONY: help helm-lint helm-template full-check verify-locks validate-secrets \
	kind-bootstrap ingress-install argocd-bootstrap \
	postgres-deploy redis-deploy kafka-deploy clickhouse-deploy minio-deploy iceberg-deploy observability-deploy \
	backup restore-smoke platform-validate build-release gate-sprint1 test-sprint1 \
	lint typecheck test-api test-api-auth test-api-container run-api

help:
	@echo "Sprint 1 targets: kind-bootstrap ingress-install argocd-bootstrap postgres-deploy redis-deploy kafka-deploy clickhouse-deploy minio-deploy iceberg-deploy observability-deploy helm-lint helm-template full-check verify-locks validate-secrets backup restore-smoke platform-validate build-release gate-sprint1 test-sprint1"
	@echo "Sprint 2 targets: lint typecheck test-api test-api-auth test-api-container run-api"

kind-bootstrap:
	@bash "$(ROOT)/infra/bootstrap/kind-bootstrap.sh"

ingress-install:
	@bash "$(ROOT)/infra/bootstrap/ingress-install.sh"

argocd-bootstrap:
	@bash "$(ROOT)/infra/bootstrap/argocd-bootstrap.sh"

postgres-deploy:
	@bash "$(ROOT)/infra/bootstrap/platform-deploy.sh" postgresql

redis-deploy:
	@bash "$(ROOT)/infra/bootstrap/platform-deploy.sh" redis

kafka-deploy:
	@bash "$(ROOT)/infra/bootstrap/platform-deploy.sh" kafka

clickhouse-deploy:
	@bash "$(ROOT)/infra/bootstrap/platform-deploy.sh" clickhouse

minio-deploy:
	@bash "$(ROOT)/infra/bootstrap/platform-deploy.sh" minio

iceberg-deploy:
	@bash "$(ROOT)/infra/bootstrap/platform-deploy.sh" iceberg

observability-deploy:
	@bash "$(ROOT)/infra/bootstrap/platform-deploy.sh" observability

helm-lint:
	@bash "$(ROOT)/infra/scripts/helm-lint.sh"

helm-template:
	@bash "$(ROOT)/infra/scripts/helm-template.sh"

full-check:
	@bash "$(ROOT)/infra/scripts/full-check.sh"

verify-locks:
	@ROOT="$(ROOT)" bash "$(ROOT)/infra/locks/scripts/verify-locks.sh"

validate-secrets:
	@ROOT="$(ROOT)" bash "$(ROOT)/infra/secrets/scripts/validate-secrets.sh"

backup:
	@bash "$(ROOT)/scripts/backup.sh"

restore-smoke:
	@bash "$(ROOT)/scripts/restore-smoke.sh"

platform-validate:
	@bash "$(ROOT)/scripts/platform-validate.sh"

build-release:
	@bash "$(ROOT)/scripts/build-release.sh"

gate-sprint1:
	@bash "$(ROOT)/scripts/gates/gate-sprint1.sh"

test-sprint1:
	@python3 -m pytest -q tests/locks tests/secrets tests/backup tests/platform_validation tests/release

# Sprint 2 — FastAPI runtime (apps/api)
lint:
	@cd "$(API_DIR)" && uv run ruff check app tests && uv run ruff format --check app tests

typecheck:
	@cd "$(API_DIR)" && uv run mypy

test-api:
	@cd "$(API_DIR)" && uv run pytest -q

test-api-auth:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_token_service.py \
		tests/unit/test_auth_config.py \
		tests/integration/test_auth_endpoints.py

test-api-container:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_container.py \
		tests/unit/test_providers.py \
		tests/integration/test_container_integration.py

run-api:
	@cd "$(API_DIR)" && uv run app
