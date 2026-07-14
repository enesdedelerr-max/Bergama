"""SEC archive URL construction with host validation (Issue #304C)."""

from __future__ import annotations

from urllib.parse import urlparse

from app.infrastructure.sec.accession import (
    accession_without_dashes,
    cik_without_leading_zeros,
    validate_accession_number,
)
from app.infrastructure.sec.errors import SecInvalidRequestError

_ALLOWED_ARCHIVE_HOSTS = frozenset({"www.sec.gov", "sec.gov"})


def validate_sec_archives_base(base_url: str) -> str:
    text = base_url.strip().rstrip("/")
    parsed = urlparse(text)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SecInvalidRequestError("archives base URL must be https with host")
    host = parsed.netloc.lower()
    if host not in _ALLOWED_ARCHIVE_HOSTS and not host.endswith(".sec.gov"):
        raise SecInvalidRequestError("archives host must be official sec.gov")
    return text


def build_filing_index_url(
    *,
    archives_base_url: str,
    cik: str,
    accession_number: str,
) -> str:
    """Build filing index URL from official EDGAR path rules.

    Pattern (confirmed by SEC Accessing EDGAR Data):
    ``{archives}/Archives/edgar/data/{cik_no_pad}/{accession_nodash}/{accession}-index.html``
    """
    base = validate_sec_archives_base(archives_base_url)
    accession = validate_accession_number(accession_number)
    cik_path = cik_without_leading_zeros(cik)
    nodash = accession_without_dashes(accession)
    return f"{base}/Archives/edgar/data/{cik_path}/{nodash}/{accession}-index.html"


def build_primary_document_url(
    *,
    archives_base_url: str,
    cik: str,
    accession_number: str,
    primary_document: str,
) -> str | None:
    """Optional primary document URL under the accession directory."""
    doc = primary_document.strip()
    if not doc or "/" in doc or "\\" in doc or ".." in doc:
        return None
    base = validate_sec_archives_base(archives_base_url)
    accession = validate_accession_number(accession_number)
    cik_path = cik_without_leading_zeros(cik)
    nodash = accession_without_dashes(accession)
    return f"{base}/Archives/edgar/data/{cik_path}/{nodash}/{doc}"
