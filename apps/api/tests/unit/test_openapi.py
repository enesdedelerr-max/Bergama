"""Unit tests for OpenAPI metadata."""

from __future__ import annotations

from httpx import AsyncClient


async def test_openapi_document_is_generated(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()
    assert document["openapi"].startswith("3.")
    assert document["info"]["title"] == "bergama-api-test"
    assert "/health" in document["paths"]
    assert "/ready" in document["paths"]


async def test_docs_ui_is_available(client: AsyncClient) -> None:
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
