"""URL sanitization and pagination next_url validation."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.infrastructure.polygon.errors import (
    PolygonInvalidRequestError,
    PolygonPaginationLimitError,
    PolygonPaginationLoopError,
)

_SECRET_QUERY_KEYS = frozenset({"apikey", "api_key", "api-key", "token", "access_token"})


def sanitize_url(url: str) -> str:
    """Strip credential-bearing query parameters for logs/source refs."""
    parsed = urlparse(url)
    cleaned = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in _SECRET_QUERY_KEYS
    ]
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(cleaned),
            "",
        )
    )


def validate_next_url(*, next_url: str, base_url: str) -> str:
    """Allow next_url only when scheme/host match configured base_url."""
    base = urlparse(base_url)
    nxt = urlparse(next_url)
    if nxt.scheme != base.scheme:
        msg = "pagination next_url scheme must match configured base_url"
        raise PolygonInvalidRequestError(msg)
    if nxt.scheme != "https":
        msg = "pagination next_url must use https"
        raise PolygonInvalidRequestError(msg)
    if nxt.netloc.lower() != base.netloc.lower():
        msg = "pagination next_url host must match configured base_url"
        raise PolygonInvalidRequestError(msg)
    if not nxt.path:
        msg = "pagination next_url path is required"
        raise PolygonInvalidRequestError(msg)
    return next_url


class PaginationGuard:
    """Detect loops and enforce maximum page count."""

    def __init__(self, *, max_pages: int) -> None:
        if max_pages < 1:
            msg = "max_pages must be >= 1"
            raise ValueError(msg)
        self._max_pages = max_pages
        self._seen: set[str] = set()
        self._page = 0

    def begin_page(self, url: str) -> None:
        sanitized = sanitize_url(url)
        self._page += 1
        if self._page > self._max_pages:
            msg = f"exceeded maximum pagination pages ({self._max_pages})"
            raise PolygonPaginationLimitError(msg)
        if sanitized in self._seen:
            msg = "pagination next_url loop detected"
            raise PolygonPaginationLoopError(msg)
        self._seen.add(sanitized)

    @property
    def pages_fetched(self) -> int:
        return self._page
