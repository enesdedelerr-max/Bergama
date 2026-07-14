"""Smoke tests for runtime health endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_live_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "request_id" in body


async def test_health_startup_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health/startup")
    assert response.status_code == 200
    assert response.json()["status"] == "started"


async def test_health_ready_returns_aggregate(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ready", "degraded"}
    assert isinstance(body["checks"], list)


async def test_legacy_health_alias_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


async def test_legacy_ready_alias_returns_readiness(client: AsyncClient) -> None:
    response = await client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ready", "degraded"}
    assert body["environment"] == "test"
