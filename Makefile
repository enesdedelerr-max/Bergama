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
	lint typecheck test-api test-api-auth test-api-container test-api-health \
	test-api-kafka-core test-api-kafka-test-runtime test-api-registry smoke-api-kafka run-api \
	smoke-api-runtime validate-api-openapi build-sprint2-release gate-sprint2 test-sprint2-gate \
	test-api-market-contracts test-api-polygon-historical test-api-polygon-realtime \
	test-api-finnhub-fundamentals test-api-fred-macro test-api-sec-filings \
	test-api-benzinga-news test-api-provider-contracts test-api-market-orchestrator \
	test-api-kafka-publish-adapter smoke-api-kafka-publish \
	test-api-iceberg-writer smoke-api-iceberg-writer \
	test-api-replay-engine smoke-api-replay-engine \
	test-api-backfill smoke-api-backfill \
	smoke-api-polygon smoke-api-polygon-realtime smoke-api-finnhub smoke-api-fred \
	smoke-api-sec smoke-api-benzinga

help:
	@echo "Sprint 1 targets: kind-bootstrap ingress-install argocd-bootstrap postgres-deploy redis-deploy kafka-deploy clickhouse-deploy minio-deploy iceberg-deploy observability-deploy helm-lint helm-template full-check verify-locks validate-secrets backup restore-smoke platform-validate build-release gate-sprint1 test-sprint1"
	@echo "Sprint 2 targets: lint typecheck test-api test-api-auth test-api-container test-api-health test-api-kafka-core test-api-kafka-test-runtime test-api-registry smoke-api-kafka smoke-api-runtime validate-api-openapi build-sprint2-release gate-sprint2 test-sprint2-gate run-api"
	@echo "Sprint 3 targets: test-api-market-contracts test-api-polygon-historical test-api-polygon-realtime test-api-finnhub-fundamentals test-api-fred-macro test-api-sec-filings test-api-benzinga-news test-api-provider-contracts test-api-market-orchestrator test-api-kafka-publish-adapter smoke-api-kafka-publish test-api-iceberg-writer smoke-api-iceberg-writer test-api-replay-engine smoke-api-replay-engine test-api-backfill smoke-api-backfill smoke-api-polygon smoke-api-polygon-realtime smoke-api-finnhub smoke-api-fred smoke-api-sec smoke-api-benzinga"

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
	@cd "$(API_DIR)" && uv run pytest -q -m "not kafka_integration and not iceberg_writer_smoke and not replay_engine_smoke and not backfill_smoke"

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

test-api-health:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_health_service.py \
		tests/unit/test_runtime_state.py \
		tests/integration/test_health_runtime.py \
		tests/smoke/test_health.py

test-api-kafka-core:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_event_envelope.py \
		tests/unit/test_event_serialization.py \
		tests/unit/test_topic_registry.py \
		tests/unit/test_consumer_worker.py \
		tests/unit/test_kafka_container.py \
		tests/integration/test_kafka_adapter.py

test-api-kafka-test-runtime:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_in_memory_event_broker.py \
		tests/unit/test_fake_kafka_producer.py \
		tests/unit/test_fake_kafka_consumer.py \
		tests/integration/test_in_memory_event_roundtrip.py \
		tests/integration/test_consumer_worker_runtime.py

test-api-registry:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_registry_models.py \
		tests/unit/test_registry_loaders.py \
		tests/unit/test_registry_validation.py \
		tests/unit/test_registry_canonicalization.py \
		tests/integration/test_registry_service.py

test-api-market-contracts:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_market_data_contracts.py \
		tests/contract/test_canonical_market_event_envelope.py

test-api-polygon-historical:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_polygon_settings_and_mapper.py \
		tests/unit/test_polygon_historical_connector.py

test-api-polygon-realtime:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_polygon_realtime_connector.py

test-api-finnhub-fundamentals:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_finnhub_fundamentals.py

test-api-fred-macro:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_fred_macro.py

test-api-sec-filings:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_sec_filings.py

test-api-benzinga-news:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_benzinga_news.py

test-api-provider-contracts:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/contract/test_provider_identity_contracts.py \
		tests/contract/test_provider_time_contracts.py \
		tests/contract/test_provider_key_contracts.py \
		tests/contract/test_provider_value_contracts.py \
		tests/contract/test_provider_provenance_contracts.py \
		tests/contract/test_provider_redaction_contracts.py \
		tests/contract/test_provider_retry_contracts.py \
		tests/contract/test_provider_pagination_contracts.py \
		tests/contract/test_provider_lifecycle_contracts.py \
		tests/contract/test_provider_event_envelope_contracts.py

test-api-market-orchestrator:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_pipeline_context.py \
		tests/unit/test_dedup.py \
		tests/unit/test_ordering.py \
		tests/unit/test_buffer.py \
		tests/unit/test_routing.py \
		tests/unit/test_publish_port.py \
		tests/unit/test_pipeline.py \
		tests/contract/test_market_data_orchestrator_contract.py

test-api-kafka-publish-adapter:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_kafka_publish_adapter.py \
		tests/integration/test_kafka_publish_adapter_in_memory.py

smoke-api-kafka-publish:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_KAFKA_PUBLISH_SMOKE}" != "1" ]; then \
		echo "smoke-api-kafka-publish SKIPPED (set BERGAMA_KAFKA_PUBLISH_SMOKE=1 and broker settings)"; \
		exit 0; \
	fi; \
	uv run pytest -q -m kafka_integration tests/smoke/test_kafka_publish_adapter_live.py

test-api-iceberg-writer:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_iceberg_writer_settings.py \
		tests/unit/test_iceberg_routing_mapper.py \
		tests/unit/test_iceberg_batch_idempotency.py \
		tests/integration/test_iceberg_writer_offline.py

smoke-api-iceberg-writer:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_ICEBERG_WRITER_SMOKE}" != "1" ]; then \
		echo "smoke-api-iceberg-writer SKIPPED (set BERGAMA_ICEBERG_WRITER_SMOKE=1 with Kafka, REST catalog, MinIO)"; \
		exit 0; \
	fi; \
	uv run pytest -q -m iceberg_writer_smoke tests/smoke/test_iceberg_writer_live.py

test-api-replay-engine:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_replay_settings_and_request.py \
		tests/unit/test_replay_reconstruction_and_ordering.py \
		tests/unit/test_replay_engine_modes.py \
		tests/contract/test_replay_engine_contract.py \
		tests/integration/test_replay_engine_offline.py

smoke-api-replay-engine:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_REPLAY_ENGINE_SMOKE}" != "1" ]; then \
		echo "smoke-api-replay-engine SKIPPED (set BERGAMA_REPLAY_ENGINE_SMOKE=1 for local Iceberg dry-run)"; \
		exit 0; \
	fi; \
	uv run pytest -q -m replay_engine_smoke tests/smoke/test_replay_engine_live.py

test-api-backfill:
	@cd "$(API_DIR)" && uv run pytest -q \
		tests/unit/test_backfill_settings_and_request.py \
		tests/unit/test_backfill_slicing.py \
		tests/unit/test_backfill_checkpoint.py \
		tests/unit/test_backfill_engine_modes.py \
		tests/contract/test_backfill_contract.py \
		tests/integration/test_backfill_offline.py

smoke-api-backfill:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_BACKFILL_SMOKE}" != "1" ]; then \
		echo "smoke-api-backfill SKIPPED (set BERGAMA_BACKFILL_SMOKE=1 and BERGAMA_BACKFILL_SMOKE_PROVIDER)"; \
		exit 0; \
	fi; \
	uv run pytest -q -m backfill_smoke tests/smoke/test_backfill_live.py

smoke-api-polygon:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_POLYGON_SMOKE}" != "1" ]; then \
		echo "smoke-api-polygon SKIPPED (set BERGAMA_POLYGON_SMOKE=1 and BERGAMA_POLYGON__API_KEY)"; \
		exit 0; \
	fi; \
	uv run pytest -q tests/smoke/test_polygon_historical_live.py

smoke-api-polygon-realtime:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_POLYGON_WS_SMOKE}" != "1" ]; then \
		echo "smoke-api-polygon-realtime SKIPPED (set BERGAMA_POLYGON_WS_SMOKE=1 and BERGAMA_POLYGON__API_KEY)"; \
		exit 0; \
	fi; \
	uv run pytest -q tests/smoke/test_polygon_realtime_live.py

smoke-api-finnhub:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_FINNHUB_SMOKE}" != "1" ]; then \
		echo "smoke-api-finnhub SKIPPED (set BERGAMA_FINNHUB_SMOKE=1 and BERGAMA_FINNHUB__API_KEY)"; \
		exit 0; \
	fi; \
	uv run pytest -q tests/smoke/test_finnhub_fundamentals_live.py

smoke-api-fred:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_FRED_SMOKE}" != "1" ]; then \
		echo "smoke-api-fred SKIPPED (set BERGAMA_FRED_SMOKE=1 and BERGAMA_FRED__API_KEY)"; \
		exit 0; \
	fi; \
	uv run pytest -q tests/smoke/test_fred_macro_live.py

smoke-api-sec:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_SEC_SMOKE}" != "1" ]; then \
		echo "smoke-api-sec SKIPPED (set BERGAMA_SEC_SMOKE=1 and SEC User-Agent/contact)"; \
		exit 0; \
	fi; \
	uv run pytest -q tests/smoke/test_sec_filings_live.py

smoke-api-benzinga:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_BENZINGA_SMOKE}" != "1" ]; then \
		echo "smoke-api-benzinga SKIPPED (set BERGAMA_BENZINGA_SMOKE=1 and BERGAMA_BENZINGA__API_KEY)"; \
		exit 0; \
	fi; \
	uv run pytest -q tests/smoke/test_benzinga_news_live.py

smoke-api-kafka:
	@cd "$(API_DIR)" && \
	if [ "$${BERGAMA_KAFKA_SMOKE}" != "1" ]; then \
		echo "smoke-api-kafka SKIPPED (set BERGAMA_KAFKA_SMOKE=1 and broker settings)"; \
		exit 0; \
	fi; \
	uv run pytest -q -m kafka_integration tests/integration/test_kafka_live_smoke.py

smoke-api-runtime:
	@bash "$(ROOT)/scripts/smoke/smoke-api-runtime.sh"

validate-api-openapi:
	@bash "$(ROOT)/scripts/gates/validate-api-openapi.sh"

build-sprint2-release:
	@bash "$(ROOT)/scripts/gates/build-sprint2-release.sh"

gate-sprint2:
	@bash "$(ROOT)/scripts/gates/gate-sprint2.sh"

test-sprint2-gate:
	@cd "$(API_DIR)" && uv run pytest -q "$(ROOT)/tests/gates/test_sprint2_gate.py"

run-api:
	@cd "$(API_DIR)" && uv run app
