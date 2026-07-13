"""OpenAPI generation tests."""

from __future__ import annotations

from httpx import AsyncClient


async def test_openapi_document_is_generated(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()
    assert document["openapi"].startswith("3.")
    assert document["info"]["title"] == "bergama-api-test"
    paths = document["paths"]
    assert "/health" in paths
    assert "/ready" in paths
