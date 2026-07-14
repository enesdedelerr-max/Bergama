"""Cross-provider pagination contracts (#304E)."""

from __future__ import annotations

import pytest
from app.infrastructure.benzinga.errors import (
    BenzingaPaginationLimitError,
    BenzingaPaginationLoopError,
)
from app.infrastructure.benzinga.pagination import PagePaginationGuard
from app.infrastructure.fred.errors import FredPaginationLimitError, FredPaginationStateError
from app.infrastructure.fred.pagination import OffsetPaginationGuard
from app.infrastructure.polygon.errors import (
    PolygonInvalidRequestError,
    PolygonPaginationLimitError,
    PolygonPaginationLoopError,
)
from app.infrastructure.polygon.pagination import PaginationGuard, validate_next_url


def test_polygon_next_url_guard_detects_loop_and_limit() -> None:
    guard = PaginationGuard(max_pages=2)
    guard.begin_page("https://api.polygon.io/v2/aggs?cursor=a")
    with pytest.raises(PolygonPaginationLoopError):
        guard.begin_page("https://api.polygon.io/v2/aggs?cursor=a")
    guard2 = PaginationGuard(max_pages=1)
    guard2.begin_page("https://api.polygon.io/v2/aggs?cursor=a")
    with pytest.raises(PolygonPaginationLimitError):
        guard2.begin_page("https://api.polygon.io/v2/aggs?cursor=b")


def test_polygon_rejects_cross_host_next_url() -> None:
    with pytest.raises(PolygonInvalidRequestError, match="host"):
        validate_next_url(next_url="https://evil.example/x", base_url="https://api.polygon.io")


def test_fred_offset_guard_detects_regression_and_limit() -> None:
    guard = OffsetPaginationGuard(max_pages=2)
    guard.begin_page(0)
    with pytest.raises(FredPaginationStateError):
        guard.begin_page(0)
    guard2 = OffsetPaginationGuard(max_pages=1)
    guard2.begin_page(0)
    with pytest.raises(FredPaginationLimitError):
        guard2.begin_page(100)


def test_benzinga_page_guard_detects_regression_and_limit() -> None:
    guard = PagePaginationGuard(max_pages=2)
    guard.begin_page(0)
    with pytest.raises(BenzingaPaginationLoopError):
        guard.begin_page(0)
    guard2 = PagePaginationGuard(max_pages=1)
    guard2.begin_page(0)
    with pytest.raises(BenzingaPaginationLimitError):
        guard2.begin_page(1)


def test_finnhub_and_sec_document_no_multi_page_surface() -> None:
    import app.infrastructure.finnhub as finnhub_pkg
    import app.infrastructure.sec as sec_pkg

    assert "pagination" not in dir(finnhub_pkg)
    assert "Health check intentionally omitted" in (sec_pkg.__doc__ or "")
    doc = (sec_pkg.__doc__ or "").lower()
    assert "never" in doc or "omitted" in doc
