"""URL sanitization and page pagination guards for Benzinga (Issue #304D)."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.infrastructure.benzinga.errors import (
    BenzingaPaginationLimitError,
    BenzingaPaginationLoopError,
)

_SECRET_QUERY_KEYS = frozenset({"token", "api_key", "apikey", "api-key", "access_token"})


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


class PagePaginationGuard:
    """Enforce max pages and detect repeated/regressing page offsets."""

    def __init__(self, *, max_pages: int) -> None:
        if max_pages < 1:
            msg = "max_pages must be >= 1"
            raise ValueError(msg)
        self._max_pages = max_pages
        self._seen_pages: set[int] = set()
        self._page_count = 0
        self._last_page: int | None = None

    def begin_page(self, page: int) -> None:
        if page < 0:
            raise BenzingaPaginationLoopError("pagination page must be non-negative")
        self._page_count += 1
        if self._page_count > self._max_pages:
            raise BenzingaPaginationLimitError(
                f"exceeded maximum pagination pages ({self._max_pages})"
            )
        if page in self._seen_pages:
            raise BenzingaPaginationLoopError("repeated pagination page detected")
        if self._last_page is not None and page <= self._last_page:
            raise BenzingaPaginationLoopError("pagination page did not advance")
        self._seen_pages.add(page)
        self._last_page = page

    @property
    def pages_fetched(self) -> int:
        return self._page_count

    @property
    def max_pages(self) -> int:
        return self._max_pages
