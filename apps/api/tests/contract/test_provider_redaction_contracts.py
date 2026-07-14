"""Cross-provider secret-redaction contracts (#304E)."""

from __future__ import annotations

from app.core.benzinga_settings import BenzingaSettings
from app.core.finnhub_settings import FinnhubSettings
from app.core.fred_settings import FredSettings
from app.core.polygon_settings import PolygonSettings
from app.infrastructure.benzinga.pagination import sanitize_url as benzinga_sanitize
from app.infrastructure.fred.pagination import sanitize_url as fred_sanitize
from app.infrastructure.polygon.pagination import sanitize_url as polygon_sanitize
from app.infrastructure.polygon.ws_transport import build_auth_frame, redact_control_frame
from pydantic import SecretStr
from tests.support.provider_contracts.assertions import (
    assert_redaction_contract,
    secret_absent_in_mapping,
)

FAKE_KEY = "contract-test-secret-key-abcdef"


def test_settings_safe_summary_never_includes_secret() -> None:
    for settings in (
        PolygonSettings(enabled=True, api_key=SecretStr(FAKE_KEY)),
        FinnhubSettings(enabled=True, api_key=SecretStr(FAKE_KEY)),
        FredSettings(enabled=True, api_key=SecretStr(FAKE_KEY)),
        BenzingaSettings(enabled=True, api_key=SecretStr(FAKE_KEY)),
    ):
        summary = settings.safe_summary()
        secret_absent_in_mapping(summary, (FAKE_KEY,))
        assert summary["api_key_configured"] is True
        assert FAKE_KEY not in repr(settings)


def test_url_sanitizers_strip_credential_query_params() -> None:
    dirty = f"https://api.example/path?page=0&api_key={FAKE_KEY}&token={FAKE_KEY}&apikey={FAKE_KEY}"
    for cleaned in (
        polygon_sanitize(dirty),
        fred_sanitize(dirty),
        benzinga_sanitize(dirty),
    ):
        assert_redaction_contract(cleaned)
        assert FAKE_KEY not in cleaned
        assert "page=0" in cleaned


def test_polygon_ws_auth_frame_is_redacted() -> None:
    frame = build_auth_frame(FAKE_KEY)
    redacted = redact_control_frame(frame)
    assert FAKE_KEY not in redacted
    assert "***REDACTED***" in redacted
    assert_redaction_contract(redacted)
