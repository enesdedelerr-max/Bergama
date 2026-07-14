"""Integration tests for request logging middleware and context headers."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import pytest
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.log_context import get_log_context
from app.core.logging import configure_logging
from app.factory import create_app
from httpx import ASGITransport, AsyncClient
from tests.conftest import make_production_secrets


@pytest.fixture
def json_settings() -> AppSettings:
    return AppSettings(
        app_name="bergama-api-test",
        app_version="0.2.0",
        environment=AppEnvironment.STAGING,
        debug=False,
        docs_enabled=True,
        openapi_enabled=True,
        log_level="INFO",
        api_prefix="/api/v1",
        service_name="bergama-api-test",
        instance_id="test-1",
        secrets=make_production_secrets(),
    )


@pytest.fixture
async def json_client(json_settings: AppSettings) -> AsyncIterator[AsyncClient]:
    application = create_app(json_settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_health_returns_request_and_correlation_headers(
    json_client: AsyncClient,
) -> None:
    response = await json_client.get("/health")
    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    correlation_id = response.headers["X-Correlation-ID"]
    assert request_id
    assert correlation_id == request_id
    assert "X-Causation-ID" not in response.headers


@pytest.mark.asyncio
async def test_existing_incoming_ids_are_echoed(json_client: AsyncClient) -> None:
    response = await json_client.get(
        "/ready",
        headers={
            "X-Request-ID": "req-fixed-1",
            "X-Correlation-ID": "corr-fixed-1",
            "X-Causation-ID": "cause-fixed-1",
        },
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-fixed-1"
    assert response.headers["X-Correlation-ID"] == "corr-fixed-1"
    assert response.headers["X-Causation-ID"] == "cause-fixed-1"


@pytest.mark.asyncio
async def test_rejects_malformed_inbound_ids(json_client: AsyncClient) -> None:
    response = await json_client.get(
        "/health",
        headers={
            "X-Request-ID": "not valid!",
            "X-Correlation-ID": "also bad",
            "X-Causation-ID": "nope!",
        },
    )
    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    assert request_id != "not valid!"
    assert " " not in request_id
    assert response.headers["X-Correlation-ID"] == request_id
    assert "X-Causation-ID" not in response.headers


@pytest.mark.asyncio
async def test_context_does_not_leak_between_requests(json_client: AsyncClient) -> None:
    first = await json_client.get(
        "/health",
        headers={"X-Request-ID": "first-req-id", "X-Correlation-ID": "first-corr"},
    )
    second = await json_client.get("/health")
    assert first.headers["X-Request-ID"] == "first-req-id"
    assert second.headers["X-Request-ID"] != "first-req-id"
    assert get_log_context().request_id is None


@pytest.mark.asyncio
async def test_request_start_and_completion_logs_with_status_and_duration(
    json_settings: AppSettings,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(json_settings)
    application = create_app(json_settings)
    transport = ASGITransport(app=application)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200

    payloads = [
        json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")
    ]
    events = [p.get("event") for p in payloads]
    assert "http.request.started" in events
    assert "http.request.completed" in events
    completed = next(p for p in payloads if p.get("event") == "http.request.completed")
    assert completed["status_code"] == 200
    assert completed["duration_ms"] >= 0
    assert completed["method"] == "GET"
    assert completed["path"] == "/openapi.json"


@pytest.mark.asyncio
async def test_failing_endpoint_produces_failure_log_without_stack_in_body(
    json_settings: AppSettings,
) -> None:
    configure_logging(json_settings)
    application = create_app(json_settings)

    @application.get("/__test__/boom")
    async def boom() -> None:
        raise RuntimeError("intentional test failure")

    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    capture = _Capture()
    root = logging.getLogger()
    root.addHandler(capture)
    try:
        transport = ASGITransport(app=application, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/__test__/boom")
    finally:
        root.removeHandler(capture)

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "internal.error"
    assert "traceback" not in json.dumps(body).lower()
    assert "RuntimeError" not in json.dumps(body)
    assert "intentional test failure" not in json.dumps(body)

    events = [getattr(record, "event", None) for record in records]
    assert "http.request.failed" in events or "http.exception.unhandled" in events
    failure = next(
        record
        for record in records
        if getattr(record, "event", None) in {"http.request.failed", "http.exception.unhandled"}
    )
    assert failure.error_type == "RuntimeError"  # type: ignore[attr-defined]
    assert failure.path == "/__test__/boom"  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_logs_contain_service_environment_version_without_bodies_or_auth(
    json_settings: AppSettings,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(json_settings)
    application = create_app(json_settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get(
            "/openapi.json",
            headers={
                "X-Request-ID": "json-req-1",
                "X-Correlation-ID": "json-corr-1",
                "Authorization": "Bearer super-secret",
            },
        )

    payloads = [
        json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")
    ]
    started = next(p for p in payloads if p.get("event") == "http.request.started")
    completed = next(p for p in payloads if p.get("event") == "http.request.completed")
    assert started["request_id"] == "json-req-1"
    assert started["correlation_id"] == "json-corr-1"
    assert started["service"] == "bergama-api-test"
    assert started["environment"] == "staging"
    assert started["app_version"] == "0.2.0"
    assert completed["status_code"] == 200
    assert "duration_ms" in completed
    blob = json.dumps(payloads)
    assert "super-secret" not in blob
    assert "Bearer" not in blob
    assert "query" not in completed
    assert "body" not in completed
    assert "authorization" not in completed


@pytest.mark.asyncio
async def test_docs_ready_and_openapi_still_work(json_client: AsyncClient) -> None:
    assert (await json_client.get("/ready")).status_code == 200
    assert (await json_client.get("/docs")).status_code == 200
    assert (await json_client.get("/openapi.json")).status_code == 200
