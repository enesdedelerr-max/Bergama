"""HTTP / authz tests for Intelligence Run product routes (WS3)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import jwt
import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.core.security import (
    API_READ_SCOPE,
    BOOTSTRAP_ROLES,
    BOOTSTRAP_SUBJECT,
    INTELLIGENCE_RUNS_READ_SCOPE,
    TOKEN_TYPE_ACCESS,
)
from app.deps.intelligence_runs import get_intelligence_run_query_service
from app.factory import create_app
from app.intelligence_pipeline import run_intelligence_pipeline
from app.intelligence_runs.constants import (
    PERSISTENCE_SCHEMA_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.product_errors import (
    corrupt_persisted_snapshot,
    run_not_found,
    storage_unavailable,
    unsupported_snapshot_contract,
)
from app.intelligence_runs.query_service import IntelligenceRunQueryService
from app.intelligence_runs.snapshot import build_authoritative_snapshot
from app.schemas.intelligence_runs import IntelligenceRunRead
from httpx import ASGITransport, AsyncClient
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.unit.test_intelligence_pipeline_core import VALID_ATTESTATION, _valid_request

FIXED_NOW = datetime(2026, 10, 7, 18, 0, tzinfo=UTC)

PRODUCT_ROUTES = (
    "/api/v1/intelligence/runs/latest-dashboard-capable",
    f"/api/v1/intelligence/runs/id/{uuid.uuid4()}",
    f"/api/v1/intelligence/runs/fingerprint/{'a' * 64}",
    f"/api/v1/intelligence/runs/id/{uuid.uuid4()}/dashboard",
    f"/api/v1/intelligence/runs/id/{uuid.uuid4()}/human-review",
    f"/api/v1/intelligence/runs/id/{uuid.uuid4()}/ade",
)


def _settings() -> AppSettings:
    return AppSettings(
        environment=AppEnvironment.LOCAL,
        debug=True,
        docs_enabled=True,
        openapi_enabled=True,
        bootstrap_auth_enabled=True,
        jwt_access_token_ttl_seconds=900,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )


def _mint_token(*, scopes: list[str]) -> str:
    settings = _settings()
    # Use wall-clock claims so validation against SystemClock succeeds.
    now = int(datetime.now(UTC).timestamp())
    return jwt.encode(
        {
            "sub": BOOTSTRAP_SUBJECT,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": now,
            "nbf": now,
            "exp": now + 3600,
            "jti": str(uuid.uuid4()),
            "token_type": TOKEN_TYPE_ACCESS,
            "roles": list(BOOTSTRAP_ROLES),
            "scopes": scopes,
            "environment": settings.environment.value,
        },
        VALID_PROD_JWT_SECRET,
        algorithm="HS256",
    )


def _record(**kwargs: Any) -> IntelligenceRunRecord:
    result = run_intelligence_pipeline(_valid_request(**kwargs))
    snapshot = build_authoritative_snapshot(result)
    return IntelligenceRunRecord(
        run_id=uuid.uuid4(),
        pipeline_fingerprint=snapshot.pipeline_fingerprint,
        as_of=snapshot.as_of,
        outcome=snapshot.outcome,
        failed_stage=snapshot.failed_stage,
        failure_error_type=snapshot.failure_error_type,
        failure_detail=snapshot.failure_detail,
        bindings_json=snapshot.bindings,
        provenance_json=snapshot.provenance,
        stage_presence_json=dict(snapshot.stage_presence),
        dashboard_snapshot_json=snapshot.dashboard_snapshot,
        human_review_snapshot_json=snapshot.human_review_snapshot,
        ade_snapshot_json=snapshot.ade_snapshot,
        snapshot_contract_version=SNAPSHOT_CONTRACT_VERSION,
        persistence_schema_version=PERSISTENCE_SCHEMA_VERSION,
        persisted_at=FIXED_NOW,
    )


def _bind_real_query(
    query: MagicMock,
    record: IntelligenceRunRecord,
) -> IntelligenceRunQueryService:
    service = IntelligenceRunQueryService(session=MagicMock(), clock=FixedClock(FIXED_NOW))
    repo = MagicMock()
    repo.get_by_run_id.return_value = record
    repo.get_by_logical_identity.return_value = record
    repo.get_latest_dashboard_storage_candidate.return_value = record
    service._repository = repo  # noqa: SLF001
    query.get_run_by_id.side_effect = service.get_run_by_id
    query.get_run_by_fingerprint.side_effect = service.get_run_by_fingerprint
    query.get_latest_dashboard_capable.side_effect = service.get_latest_dashboard_capable
    query.get_dashboard.side_effect = service.get_dashboard
    query.get_human_review.side_effect = service.get_human_review
    query.get_ade.side_effect = service.get_ade
    return service


@pytest.fixture
def app_and_query() -> Iterator[tuple[Any, MagicMock]]:
    container = build_container(_settings(), clock=FixedClock(FIXED_NOW))
    application = create_app(settings=container.settings, container=container)
    query = MagicMock(spec=IntelligenceRunQueryService)
    application.dependency_overrides[get_intelligence_run_query_service] = lambda: query
    yield application, query
    application.dependency_overrides.clear()


@pytest.fixture
async def client(app_and_query: tuple[Any, MagicMock]) -> AsyncIterator[AsyncClient]:
    application, _ = app_and_query
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.mark.asyncio
async def test_all_six_routes_require_product_scope(client: AsyncClient) -> None:
    api_only = _mint_token(scopes=[API_READ_SCOPE])
    for path in PRODUCT_ROUTES:
        response = await client.get(path, headers={"Authorization": f"Bearer {api_only}"})
        assert response.status_code == 403, path
        body = response.json()
        assert body["code"] == "authz.insufficient_scope"
        assert "request_id" in body
        assert set(body.keys()) <= {"code", "message", "request_id", "details"}


@pytest.mark.asyncio
async def test_missing_and_invalid_token_401(client: AsyncClient) -> None:
    path = PRODUCT_ROUTES[0]
    missing = await client.get(path)
    assert missing.status_code == 401
    assert missing.json()["code"] == "auth.missing_token"
    invalid = await client.get(path, headers={"Authorization": "Bearer not-a-jwt"})
    assert invalid.status_code == 401
    assert invalid.json()["code"].startswith("auth.")


@pytest.mark.asyncio
async def test_product_scope_success_and_identifier_errors(
    client: AsyncClient,
    app_and_query: tuple[Any, MagicMock],
) -> None:
    _, query = app_and_query
    record = _record()
    _bind_real_query(query, record)
    token = _mint_token(scopes=[INTELLIGENCE_RUNS_READ_SCOPE])
    headers = {"Authorization": f"Bearer {token}"}

    ok = await client.get(f"/api/v1/intelligence/runs/id/{record.run_id}", headers=headers)
    assert ok.status_code == 200
    body = ok.json()
    IntelligenceRunRead.model_validate(body)
    assert body["age_seconds"] >= 0

    bad_id = await client.get("/api/v1/intelligence/runs/id/not-uuid", headers=headers)
    assert bad_id.status_code == 400
    assert bad_id.json()["code"] == "intelligence.runs.invalid_identifier"

    query.get_run_by_id.side_effect = run_not_found()
    missing = await client.get(f"/api/v1/intelligence/runs/id/{uuid.uuid4()}", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["code"] == "intelligence.runs.run_not_found"

    _bind_real_query(query, record)
    bad_fp = await client.get("/api/v1/intelligence/runs/fingerprint/ZZZ", headers=headers)
    assert bad_fp.status_code == 400
    assert bad_fp.json()["code"] == "intelligence.runs.invalid_identifier"

    uppercase_fp = await client.get(
        f"/api/v1/intelligence/runs/fingerprint/{'A' * 64}",
        headers=headers,
    )
    assert uppercase_fp.status_code == 400
    assert uppercase_fp.json()["code"] == "intelligence.runs.invalid_identifier"

    assert record.pipeline_fingerprint is not None
    fp_ok = await client.get(
        f"/api/v1/intelligence/runs/fingerprint/{record.pipeline_fingerprint}",
        headers=headers,
    )
    assert fp_ok.status_code == 200


@pytest.mark.asyncio
async def test_error_mappings_409_500_503(
    client: AsyncClient,
    app_and_query: tuple[Any, MagicMock],
) -> None:
    _, query = app_and_query
    token = _mint_token(scopes=[INTELLIGENCE_RUNS_READ_SCOPE])
    headers = {"Authorization": f"Bearer {token}"}
    path = f"/api/v1/intelligence/runs/id/{uuid.uuid4()}"

    query.get_run_by_id.side_effect = unsupported_snapshot_contract(version="x")
    resp = await client.get(path, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["code"] == "intelligence.runs.unsupported_snapshot_contract"

    query.get_run_by_id.side_effect = corrupt_persisted_snapshot()
    resp = await client.get(path, headers=headers)
    assert resp.status_code == 500
    assert resp.json()["code"] == "intelligence.runs.corrupt_persisted_snapshot"

    query.get_run_by_id.side_effect = storage_unavailable()
    resp = await client.get(path, headers=headers)
    assert resp.status_code == 503
    assert resp.json()["code"] == "intelligence.runs.storage_unavailable"
    assert "sqlalchemy" not in resp.text.lower()
    assert "traceback" not in resp.text.lower()


@pytest.mark.asyncio
async def test_stage_routes_and_ade_payload_exclusion(
    client: AsyncClient,
    app_and_query: tuple[Any, MagicMock],
) -> None:
    _, query = app_and_query
    record = _record(hr_requested=True, ade_requested=True, hr_attestation=VALID_ATTESTATION)
    _bind_real_query(query, record)
    token = _mint_token(scopes=[INTELLIGENCE_RUNS_READ_SCOPE])
    headers = {"Authorization": f"Bearer {token}"}
    run_id = record.run_id

    dash = await client.get(f"/api/v1/intelligence/runs/id/{run_id}/dashboard", headers=headers)
    assert dash.status_code == 200
    hr = await client.get(f"/api/v1/intelligence/runs/id/{run_id}/human-review", headers=headers)
    assert hr.status_code == 200
    ade = await client.get(f"/api/v1/intelligence/runs/id/{run_id}/ade", headers=headers)
    assert ade.status_code == 200
    assert "recorded_attestation_payload" not in ade.text

    dash_only = _record()
    _bind_real_query(query, dash_only)
    absent = await client.get(
        f"/api/v1/intelligence/runs/id/{dash_only.run_id}/human-review",
        headers=headers,
    )
    assert absent.status_code == 404
    assert absent.json()["code"] == "intelligence.runs.stage_not_present"


@pytest.mark.asyncio
async def test_openapi_exposes_exactly_six_product_get_routes() -> None:
    application = create_app(_settings())
    openapi_paths = application.openapi()["paths"]
    product_paths = {path for path in openapi_paths if path.startswith("/api/v1/intelligence/runs")}
    assert len(product_paths) == 6
    for path in product_paths:
        assert set(openapi_paths[path]) == {"get"}
