"""Synthetic SEC EDGAR fixtures mapped to canonical events."""

from __future__ import annotations

from datetime import datetime

from app.infrastructure.sec.mapper import map_recent_filings
from app.infrastructure.sec.schemas import SecSubmissionsResponse
from app.market_data.events.filing import FilingEvent
from app.market_data.identity import InstrumentId
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.provider_contracts.identities import equity_instrument

PROVIDER_CIK = "320193"
ACCESSION = "0000320193-24-000001"


def sec_submissions_payload(
    *,
    form: str = "10-K",
    accession: str = ACCESSION,
    filing_date: str = "2024-01-15",
    acceptance: str = "2024-01-15T21:00:00.000Z",
) -> dict[str, object]:
    return {
        "cik": PROVIDER_CIK,
        "name": "Synthetic Issuer Fixture",
        "filings": {
            "recent": {
                "accessionNumber": [accession],
                "filingDate": [filing_date],
                "reportDate": ["2023-12-31"],
                "acceptanceDateTime": [acceptance],
                "act": ["34"],
                "form": [form],
                "fileNumber": ["001-00001"],
                "filmNumber": ["24000001"],
                "items": [""],
                "size": [1000],
                "isXBRL": [1],
                "isInlineXBRL": [1],
                "primaryDocument": ["synthetic.htm"],
                "primaryDocDescription": ["Synthetic Form Description"],
            },
            "files": [{"name": "CIK0000320193.json", "filingCount": 1}],
        },
    }


def filing_events(
    *,
    instrument: InstrumentId | None = None,
    ingested_at: datetime | None = None,
    form: str = "10-K",
    accession: str = ACCESSION,
) -> tuple[FilingEvent, ...]:
    response = SecSubmissionsResponse.model_validate(
        sec_submissions_payload(form=form, accession=accession)
    )
    return map_recent_filings(
        response,
        instrument=instrument or equity_instrument(),
        cik10="0000320193",
        ingested_at=ingested_at or OBSERVED_AT,
        archives_base_url="https://www.sec.gov",
        max_filings=10,
    )
