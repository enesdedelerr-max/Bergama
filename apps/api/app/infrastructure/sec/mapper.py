"""Map SEC submissions filings.recent rows to FilingEvent (Issue #304C)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from app.infrastructure.sec.errors import SecMappingFailedError
from app.infrastructure.sec.schemas import SecRecentFilings, SecSubmissionsResponse
from app.infrastructure.sec.urls import build_filing_index_url, build_primary_document_url
from app.market_data.enums import AdjustmentState
from app.market_data.events.filing import FilingEvent
from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference

PROVIDER_SCHEMA_VERSION = "v1"
FILING_DATE_POLICY = "sec_filing_date_as_utc_midnight"
ACCEPTANCE_POLICY = "sec_acceptance_datetime_utc"

# Optional coarse classification — unknown forms remain provider strings.
FORM_CLASS_DEFINITIONS: dict[str, str] = {
    "10-K": "annual",
    "10-K/A": "annual",
    "20-F": "annual",
    "20-F/A": "annual",
    "40-F": "annual",
    "10-Q": "quarterly",
    "10-Q/A": "quarterly",
    "8-K": "current_report",
    "8-K/A": "current_report",
    "6-K": "current_report",
    "S-1": "registration",
    "S-1/A": "registration",
    "F-1": "registration",
    "3": "ownership",
    "4": "ownership",
    "5": "ownership",
    "3/A": "ownership",
    "4/A": "ownership",
    "5/A": "ownership",
}


def parse_filing_date(value: str, *, field_name: str) -> date:
    text = value.strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise SecMappingFailedError(f"invalid {field_name}: {text!r}") from exc


def utc_midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def parse_acceptance_datetime(value: str) -> datetime:
    """Parse SEC acceptanceDateTime into UTC-aware datetime."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SecMappingFailedError(f"invalid acceptanceDateTime: {value!r}") from exc
    if parsed.tzinfo is None:
        # SEC values are UTC; treat naive as UTC rather than invent local TZ.
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def detect_amendment(form: str) -> tuple[bool, str]:
    text = form.strip()
    if text.endswith("/A"):
        return True, text[: -len("/A")] or text
    return False, text


def _optional_at(values: list[Any], index: int) -> Any | None:
    if not values:
        return None
    return values[index]


def _bound(value: object | None, *, limit: int = 512) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:limit]


def _flag_text(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "true" if value != 0 else "false"
    text = str(value).strip()
    return text[:16] if text else None


def map_recent_filings(
    response: SecSubmissionsResponse,
    *,
    instrument: InstrumentId,
    cik10: str,
    archives_base_url: str,
    ingested_at: datetime,
    max_filings: int,
) -> tuple[FilingEvent, ...]:
    recent: SecRecentFilings = response.filings.recent
    count = len(recent.accession_number)
    if count == 0:
        return ()

    events: list[FilingEvent] = []
    limit = min(count, max_filings)
    for index in range(limit):
        accession = recent.accession_number[index].strip()
        form = recent.form[index].strip()
        filing_date_raw = recent.filing_date[index].strip()
        if not accession or not form or not filing_date_raw:
            raise SecMappingFailedError("required recent filing fields are empty")

        filing_day = parse_filing_date(filing_date_raw, field_name="filingDate")
        effective_at = utc_midnight(filing_day)

        acceptance_raw = _optional_at(recent.acceptance_date_time, index)
        if acceptance_raw:
            known_at = parse_acceptance_datetime(str(acceptance_raw))
            occurred_at = known_at
        else:
            known_at = effective_at
            occurred_at = effective_at

        if occurred_at > known_at:
            raise SecMappingFailedError(f"occurred_at > known_at for accession={accession}")

        quality = DataQualityFlags(is_late=True) if known_at > ingested_at else DataQualityFlags()

        is_amendment, base_form = detect_amendment(form)
        form_class = FORM_CLASS_DEFINITIONS.get(form)

        try:
            index_url = build_filing_index_url(
                archives_base_url=archives_base_url,
                cik=cik10,
                accession_number=accession,
            )
        except Exception as exc:
            raise SecMappingFailedError("failed to build filing index URL") from exc

        primary_doc = _bound(_optional_at(recent.primary_document, index), limit=256)
        primary_url = None
        if primary_doc:
            primary_url = build_primary_document_url(
                archives_base_url=archives_base_url,
                cik=cik10,
                accession_number=accession,
                primary_document=primary_doc,
            )

        metadata: dict[str, str] = {
            "sec_cik": cik10,
            "sec_filing_date": filing_date_raw[:32],
            "filing_date_policy": FILING_DATE_POLICY,
            "acceptance_policy": ACCEPTANCE_POLICY,
            "is_amendment": "true" if is_amendment else "false",
            "base_form": base_form[:32],
            "filing_index_url": index_url[:512],
        }
        if form_class:
            metadata["form_class"] = form_class
        report_date = _bound(_optional_at(recent.report_date, index), limit=32)
        if report_date:
            metadata["sec_report_date"] = report_date
        if acceptance_raw:
            metadata["sec_acceptance_datetime"] = str(acceptance_raw).strip()[:64]
        act = _bound(_optional_at(recent.act, index), limit=16)
        if act:
            metadata["sec_act"] = act
        file_number = _bound(_optional_at(recent.file_number, index), limit=64)
        if file_number:
            metadata["sec_file_number"] = file_number
        film_number = _bound(_optional_at(recent.film_number, index), limit=64)
        if film_number:
            metadata["sec_film_number"] = film_number
        items = _bound(_optional_at(recent.items, index), limit=256)
        if items:
            metadata["sec_items"] = items
        size = _optional_at(recent.size, index)
        if size is not None:
            metadata["sec_size"] = str(size)[:32]
        xbrl = _flag_text(_optional_at(recent.is_xbrl, index))
        if xbrl:
            metadata["sec_is_xbrl"] = xbrl
        inline = _flag_text(_optional_at(recent.is_inline_xbrl, index))
        if inline:
            metadata["sec_is_inline_xbrl"] = inline
        if primary_doc:
            metadata["sec_primary_document"] = primary_doc
        if primary_url:
            metadata["sec_primary_document_url"] = primary_url[:512]
        primary_desc = _bound(_optional_at(recent.primary_doc_description, index), limit=256)
        if primary_desc:
            metadata["sec_primary_doc_description"] = primary_desc
        if response.name:
            metadata["sec_entity_name"] = response.name.strip()[:256]

        title = primary_desc or f"{form} {accession}"

        # Composite provider identity for #301 keys: CIK + accession + form + filing date.
        source_event_id = f"{cik10}:{accession}:{form}:{filing_date_raw}"[:256]

        events.append(
            FilingEvent(
                schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
                instrument=instrument,
                source=SourceReference(
                    provider="sec_edgar",
                    source_instrument_id=cik10,
                    source_event_id=source_event_id,
                    extras={
                        "endpoint": "submissions",
                        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
                        "sec_cik": cik10,
                        "sec_accession_number": accession[:64],
                        "filing_index_url": index_url[:512],
                    },
                ),
                quality=quality,
                adjustment_state=AdjustmentState.UNADJUSTED,
                occurred_at=occurred_at,
                effective_at=effective_at,
                known_at=known_at,
                ingested_at=ingested_at,
                currency=None,
                venue=None,
                form_type=form[:32],
                accession_number=accession[:64],
                title=title[:512],
                document_ref=index_url[:512],
                metadata=metadata,
            )
        )

    return tuple(events)


def archive_file_refs(response: SecSubmissionsResponse) -> tuple[dict[str, str], ...]:
    """Bounded metadata for filings.files — never fetched in #304C."""
    refs: list[dict[str, str]] = []
    for file_ref in response.filings.files:
        entry: dict[str, str] = {}
        if file_ref.name:
            entry["name"] = file_ref.name.strip()[:256]
        if file_ref.filing_count is not None:
            entry["filing_count"] = str(file_ref.filing_count)
        if file_ref.filing_from:
            entry["filing_from"] = file_ref.filing_from.strip()[:32]
        if file_ref.filing_to:
            entry["filing_to"] = file_ref.filing_to.strip()[:32]
        if entry:
            refs.append(entry)
    return tuple(refs)
