"""Provider-specific SEC EDGAR submissions schemas (Issue #304C)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SecFilingFileRef(BaseModel):
    """Historical submissions archive file reference (not fetched in #304C)."""

    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    filing_count: int | None = Field(default=None, alias="filingCount")
    filing_from: str | None = Field(default=None, alias="filingFrom")
    filing_to: str | None = Field(default=None, alias="filingTo")


class SecRecentFilings(BaseModel):
    """Parallel arrays under filings.recent — lengths must align."""

    model_config = ConfigDict(extra="ignore")

    accession_number: list[str] = Field(default_factory=list, alias="accessionNumber")
    filing_date: list[str] = Field(default_factory=list, alias="filingDate")
    report_date: list[str | None] = Field(default_factory=list, alias="reportDate")
    acceptance_date_time: list[str | None] = Field(default_factory=list, alias="acceptanceDateTime")
    act: list[str | None] = Field(default_factory=list)
    form: list[str] = Field(default_factory=list)
    file_number: list[str | None] = Field(default_factory=list, alias="fileNumber")
    film_number: list[str | None] = Field(default_factory=list, alias="filmNumber")
    items: list[str | None] = Field(default_factory=list)
    size: list[int | None] = Field(default_factory=list)
    is_xbrl: list[int | bool | None] = Field(default_factory=list, alias="isXBRL")
    is_inline_xbrl: list[int | bool | None] = Field(default_factory=list, alias="isInlineXBRL")
    primary_document: list[str | None] = Field(default_factory=list, alias="primaryDocument")
    primary_doc_description: list[str | None] = Field(
        default_factory=list, alias="primaryDocDescription"
    )

    @model_validator(mode="after")
    def validate_aligned_lengths(self) -> SecRecentFilings:
        lengths = {
            "accessionNumber": len(self.accession_number),
            "filingDate": len(self.filing_date),
            "form": len(self.form),
        }
        required = lengths["accessionNumber"]
        if lengths["filingDate"] != required or lengths["form"] != required:
            msg = "filings.recent required arrays have mismatched lengths"
            raise ValueError(msg)
        optional_lens = {
            "reportDate": len(self.report_date),
            "acceptanceDateTime": len(self.acceptance_date_time),
            "act": len(self.act),
            "fileNumber": len(self.file_number),
            "filmNumber": len(self.film_number),
            "items": len(self.items),
            "size": len(self.size),
            "isXBRL": len(self.is_xbrl),
            "isInlineXBRL": len(self.is_inline_xbrl),
            "primaryDocument": len(self.primary_document),
            "primaryDocDescription": len(self.primary_doc_description),
        }
        for name, length in optional_lens.items():
            if length not in {0, required}:
                msg = (
                    f"filings.recent.{name} length {length} incompatible with "
                    f"accessionNumber length {required}"
                )
                raise ValueError(msg)
        return self


class SecFilingsBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recent: SecRecentFilings = Field(default_factory=SecRecentFilings)
    files: list[SecFilingFileRef] = Field(default_factory=list)


class SecSubmissionsResponse(BaseModel):
    """GET /submissions/CIK##########.json response."""

    model_config = ConfigDict(extra="ignore")

    cik: str | int
    entity_type: str | None = Field(default=None, alias="entityType")
    sic: str | None = None
    sic_description: str | None = Field(default=None, alias="sicDescription")
    name: str | None = None
    tickers: list[str] = Field(default_factory=list)
    exchanges: list[str] = Field(default_factory=list)
    fiscal_year_end: str | None = Field(default=None, alias="fiscalYearEnd")
    filings: SecFilingsBlock = Field(default_factory=SecFilingsBlock)
