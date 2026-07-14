"""SEC EDGAR infrastructure (Issue #304C) — company submissions filings only.

Health check intentionally omitted: submissions responses are filing-data payloads
and there is no documented cheap, honest non-data probe that avoids authenticated
User-Agent discipline and quota pressure. Configuration validation remains
settings-side (`SecSettings`) and must not be labeled provider health.

`filings.files` archive references are preserved as metadata only; archive
backfill/download is out of scope for #304C.
"""

from __future__ import annotations

from app.infrastructure.sec.accession import (
    accession_without_dashes,
    normalize_cik,
    validate_accession_number,
)
from app.infrastructure.sec.errors import (
    SecConnectionFailedError,
    SecError,
    SecForbiddenError,
    SecInvalidCikError,
    SecInvalidRequestError,
    SecInvalidResponseError,
    SecMappingFailedError,
    SecNotConfiguredError,
    SecNotFoundError,
    SecProviderError,
    SecRateLimitedError,
    SecTimeoutError,
)
from app.infrastructure.sec.http import SecHttpClient
from app.infrastructure.sec.mapper import FORM_CLASS_DEFINITIONS
from app.infrastructure.sec.submissions import (
    SecSubmissionsConnector,
    SubmissionsRequest,
    SubmissionsResult,
)

__all__ = [
    "FORM_CLASS_DEFINITIONS",
    "SecConnectionFailedError",
    "SecError",
    "SecForbiddenError",
    "SecHttpClient",
    "SecInvalidCikError",
    "SecInvalidRequestError",
    "SecInvalidResponseError",
    "SecMappingFailedError",
    "SecNotConfiguredError",
    "SecNotFoundError",
    "SecProviderError",
    "SecRateLimitedError",
    "SecSubmissionsConnector",
    "SecTimeoutError",
    "SubmissionsRequest",
    "SubmissionsResult",
    "accession_without_dashes",
    "normalize_cik",
    "validate_accession_number",
]
