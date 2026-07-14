"""CIK and accession-number normalization (Issue #304C)."""

from __future__ import annotations

import re

from app.infrastructure.sec.errors import SecInvalidCikError, SecInvalidRequestError

_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")


def normalize_cik(value: str | int) -> str:
    """Normalize CIK to exactly 10 digits for submissions endpoint paths."""
    text = str(value).strip()
    if text.lower().startswith("cik"):
        text = text[3:].strip()
    if not text.isdigit():
        raise SecInvalidCikError("CIK must be numeric")
    if len(text) > 10:
        raise SecInvalidCikError("CIK must be at most 10 digits")
    if int(text) <= 0:
        raise SecInvalidCikError("CIK must be a positive integer")
    return text.zfill(10)


def cik_without_leading_zeros(cik10: str) -> str:
    """CIK path segment used by archive URLs (no leading zeros)."""
    normalized = normalize_cik(cik10)
    return str(int(normalized))


def validate_accession_number(value: str) -> str:
    """Preserve accession exactly; require official dashed format."""
    text = value.strip()
    if not _ACCESSION_RE.match(text):
        raise SecInvalidRequestError("accession number must match ##########-YY-######")
    return text


def accession_without_dashes(accession: str) -> str:
    validated = validate_accession_number(accession)
    return validated.replace("-", "")
