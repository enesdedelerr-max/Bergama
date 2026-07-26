"""Unit tests for Strategy SDK Feature Platform host resolution (#67)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.feature_platform_settings import FeaturePlatformSettings
from app.core.secrets import SecretSettings
from app.features.catalog import BAR_CLOSE, BAR_OHLCV_FEATURE_IDS, BAR_OPEN
from app.features.errors import FeaturePlatformUnsupportedEventError
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.strategy.models import QualitySummary, StrategyInput
from app.strategy.sdk_runtime.bar_feature_registry import build_bar_feature_schema_registry
from app.strategy.sdk_runtime.bootstrap import build_reference_feature_registry
from app.strategy.sdk_runtime.feature_assembler import FeatureAssembler
from app.strategy.sdk_runtime.feature_resolution import (
    resolve_feature_snapshot_for_strategy_input,
)
from bergama_strategy_sdk.errors import StrategyFeatureSchemaError
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.market_data_fixtures import make_bar, make_trade
from tests.support.strategy_helpers import quality_assessment
from tests.support.strategy_sdk_helpers import sample_feature_values


def _strategy_input_for_event(event: object) -> StrategyInput:
    assessment = quality_assessment(event)  # type: ignore[arg-type]
    return StrategyInput(
        event=event,  # type: ignore[arg-type]
        instrument_id=event.instrument,  # type: ignore[attr-defined]
        run_id="run-1",
        session_id="session-1",
        idempotency_key=build_idempotency_key(event),  # type: ignore[arg-type]
        deduplication_key=build_deduplication_key(event),  # type: ignore[arg-type]
        quality_summary=QualitySummary.from_event_and_assessment(
            event=event,  # type: ignore[arg-type]
            assessment=assessment,
        ),
        received_at=event.ingested_at,  # type: ignore[attr-defined]
    )


def test_app_settings_feature_platform_disabled_by_default() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    assert settings.feature_platform.enabled is False
    assert settings.safe_summary()["feature_platform"]["enabled"] is False


def test_resolve_disabled_uses_assembler_path() -> None:
    bar = make_bar()
    strategy_input = _strategy_input_for_event(bar)
    assembler = FeatureAssembler(
        registry=build_reference_feature_registry(),
        feature_schema_version="1.0.0",
    )
    snapshot = resolve_feature_snapshot_for_strategy_input(
        strategy_input,
        feature_platform=FeaturePlatformSettings(enabled=False),
        assembler=assembler,
        required_features=("EMA20", "EMA50"),
        feature_values=sample_feature_values(),
    )
    assert snapshot.features[0].schema_id == "technical"
    assert {f.feature_id for f in snapshot.features} == {"EMA20", "EMA50"}


def test_resolve_disabled_still_requires_feature_values() -> None:
    bar = make_bar()
    strategy_input = _strategy_input_for_event(bar)
    assembler = FeatureAssembler(
        registry=build_reference_feature_registry(),
        feature_schema_version="1.0.0",
    )
    with pytest.raises(StrategyFeatureSchemaError) as exc_info:
        resolve_feature_snapshot_for_strategy_input(
            strategy_input,
            feature_platform=FeaturePlatformSettings(enabled=False),
            assembler=assembler,
            required_features=("EMA20", "EMA50"),
            feature_values={},
        )
    assert exc_info.value.detail == "adapter_missing_feature_values"


def test_resolve_enabled_materializes_bar_snapshot() -> None:
    bar = make_bar()
    strategy_input = _strategy_input_for_event(bar)
    assembler = FeatureAssembler(
        registry=build_bar_feature_schema_registry(),
        feature_schema_version="1.0.0",
    )
    snapshot = resolve_feature_snapshot_for_strategy_input(
        strategy_input,
        feature_platform=FeaturePlatformSettings(enabled=True),
        assembler=assembler,
        required_features=BAR_OHLCV_FEATURE_IDS,
        feature_values=None,
    )
    by_id = {feature.feature_id: feature for feature in snapshot.features}
    assert by_id[BAR_OPEN].value == Decimal("190.00")
    assert by_id[BAR_CLOSE].value == Decimal("190.20")
    assert snapshot.instrument_key == bar.instrument.instrument_key


def test_resolve_enabled_rejects_non_bar_events() -> None:
    trade = make_trade()
    strategy_input = _strategy_input_for_event(trade)
    assembler = FeatureAssembler(
        registry=build_bar_feature_schema_registry(),
        feature_schema_version="1.0.0",
    )
    with pytest.raises(FeaturePlatformUnsupportedEventError, match="unsupported_event"):
        resolve_feature_snapshot_for_strategy_input(
            strategy_input,
            feature_platform=FeaturePlatformSettings(enabled=True),
            assembler=assembler,
            required_features=BAR_OHLCV_FEATURE_IDS,
        )


def test_resolve_enabled_fingerprint_is_deterministic() -> None:
    bar = make_bar()
    strategy_input = _strategy_input_for_event(bar)
    assembler = FeatureAssembler(
        registry=build_bar_feature_schema_registry(),
        feature_schema_version="1.0.0",
    )
    settings = FeaturePlatformSettings(enabled=True)
    first = resolve_feature_snapshot_for_strategy_input(
        strategy_input,
        feature_platform=settings,
        assembler=assembler,
        required_features=BAR_OHLCV_FEATURE_IDS,
    )
    second = resolve_feature_snapshot_for_strategy_input(
        strategy_input,
        feature_platform=settings,
        assembler=assembler,
        required_features=BAR_OHLCV_FEATURE_IDS,
    )
    assert first.fingerprint() == second.fingerprint()
