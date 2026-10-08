"""Intelligence Run product read routes (Sprint 14 WS3)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps.authz import require_intelligence_runs_read
from app.deps.intelligence_runs import get_intelligence_run_query_service
from app.intelligence_runs.query_service import IntelligenceRunQueryService
from app.schemas.auth import AuthenticatedPrincipal
from app.schemas.intelligence_runs import (
    IntelligenceRunAdeRead,
    IntelligenceRunDashboardRead,
    IntelligenceRunHumanReviewRead,
    IntelligenceRunRead,
)

router = APIRouter(prefix="/intelligence/runs", tags=["intelligence-runs"])


@router.get(
    "/latest-dashboard-capable",
    response_model=IntelligenceRunRead,
)
def get_latest_dashboard_capable(
    _principal: Annotated[AuthenticatedPrincipal, Depends(require_intelligence_runs_read)],
    query: Annotated[IntelligenceRunQueryService, Depends(get_intelligence_run_query_service)],
) -> IntelligenceRunRead:
    return query.get_latest_dashboard_capable()


@router.get(
    "/fingerprint/{fingerprint}",
    response_model=IntelligenceRunRead,
)
def get_run_by_fingerprint(
    fingerprint: str,
    _principal: Annotated[AuthenticatedPrincipal, Depends(require_intelligence_runs_read)],
    query: Annotated[IntelligenceRunQueryService, Depends(get_intelligence_run_query_service)],
) -> IntelligenceRunRead:
    return query.get_run_by_fingerprint(fingerprint)


@router.get(
    "/id/{run_id}",
    response_model=IntelligenceRunRead,
)
def get_run_by_id(
    run_id: str,
    _principal: Annotated[AuthenticatedPrincipal, Depends(require_intelligence_runs_read)],
    query: Annotated[IntelligenceRunQueryService, Depends(get_intelligence_run_query_service)],
) -> IntelligenceRunRead:
    return query.get_run_by_id(run_id)


@router.get(
    "/id/{run_id}/dashboard",
    response_model=IntelligenceRunDashboardRead,
)
def get_run_dashboard(
    run_id: str,
    _principal: Annotated[AuthenticatedPrincipal, Depends(require_intelligence_runs_read)],
    query: Annotated[IntelligenceRunQueryService, Depends(get_intelligence_run_query_service)],
) -> IntelligenceRunDashboardRead:
    return query.get_dashboard(run_id)


@router.get(
    "/id/{run_id}/human-review",
    response_model=IntelligenceRunHumanReviewRead,
)
def get_run_human_review(
    run_id: str,
    _principal: Annotated[AuthenticatedPrincipal, Depends(require_intelligence_runs_read)],
    query: Annotated[IntelligenceRunQueryService, Depends(get_intelligence_run_query_service)],
) -> IntelligenceRunHumanReviewRead:
    return query.get_human_review(run_id)


@router.get(
    "/id/{run_id}/ade",
    response_model=IntelligenceRunAdeRead,
)
def get_run_ade(
    run_id: str,
    _principal: Annotated[AuthenticatedPrincipal, Depends(require_intelligence_runs_read)],
    query: Annotated[IntelligenceRunQueryService, Depends(get_intelligence_run_query_service)],
) -> IntelligenceRunAdeRead:
    return query.get_ade(run_id)
