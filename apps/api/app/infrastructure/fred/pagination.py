"""URL sanitization and offset pagination guards for FRED (Issue #304B)."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.infrastructure.fred.errors import FredPaginationLimitError, FredPaginationStateError

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


class OffsetPaginationGuard:
    """Enforce max pages and detect repeated/regressing offsets."""

    def __init__(self, *, max_pages: int) -> None:
        if max_pages < 1:
            msg = "max_pages must be >= 1"
            raise ValueError(msg)
        self._max_pages = max_pages
        self._seen_offsets: set[int] = set()
        self._page = 0
        self._last_offset: int | None = None

    def begin_page(self, offset: int) -> None:
        if offset < 0:
            raise FredPaginationStateError("pagination offset must be non-negative")
        self._page += 1
        if self._page > self._max_pages:
            raise FredPaginationLimitError(f"exceeded maximum pagination pages ({self._max_pages})")
        if offset in self._seen_offsets:
            raise FredPaginationStateError("repeated pagination offset detected")
        if self._last_offset is not None and offset <= self._last_offset:
            raise FredPaginationStateError("pagination offset did not advance")
        self._seen_offsets.add(offset)
        self._last_offset = offset

    @property
    def pages_fetched(self) -> int:
        return self._page
