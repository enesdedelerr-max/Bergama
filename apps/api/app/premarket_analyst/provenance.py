"""Provenance specification ``premarket-analyst.provenance.v1``."""

from __future__ import annotations

from app.premarket_analyst.errors import PremarketAnalystUnsupportedPolicyError
from app.premarket_analyst.models import AnalystProvenance
from app.premarket_analyst.policy import (
    ANALYST_DEFINITION_VERSION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.premarket_analyst.validate_input import ValidatedAnalystRequest
from app.strategy.keys import strategy_sha256


def build_config_fingerprint(request: ValidatedAnalystRequest) -> str:
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise PremarketAnalystUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{request.config.digest_method_id}"
        )
    return strategy_sha256(
        {
            "config": request.config.model_dump(mode="python"),
            "analyst_definition_version": ANALYST_DEFINITION_VERSION_V1,
            "policy_version_id": POLICY_VERSION_V1,
            "identity_specification_id": IDENTITY_SPECIFICATION_V1,
            "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
            "digest_method_id": DIGEST_METHOD_V1,
            "ordering_policy_id": ORDERING_POLICY_V1,
        }
    )


def build_input_fingerprint(request: ValidatedAnalystRequest) -> str:
    return strategy_sha256(
        {
            "as_of": request.as_of,
            "membership_complete": request.membership_complete,
            "watchlist": request.watchlist.model_dump(mode="python"),
            "gaps": None if request.gaps is None else request.gaps.model_dump(mode="python"),
            "catalysts": (
                None if request.catalysts is None else request.catalysts.model_dump(mode="python")
            ),
            "scores": None if request.scores is None else request.scores.model_dump(mode="python"),
            "briefing_id": None if request.briefing is None else request.briefing.briefing_id,
            "dashboard_output_id": (
                None if request.dashboard is None else request.dashboard.dashboard_output_id
            ),
            "upstream_pipeline_failure_identity": request.upstream_pipeline_failure_identity,
            "unsupported_instrument_keys": list(request.unsupported_instrument_keys),
        }
    )


def build_analyst_provenance(request: ValidatedAnalystRequest) -> AnalystProvenance:
    upstream: list[str] = [request.watchlist.provenance.input_fingerprint]
    sources: list[str] = list(request.watchlist.provenance.source_identifiers)
    if request.gaps is not None:
        upstream.append(request.gaps.provenance.input_fingerprint)
        sources.extend(request.gaps.provenance.source_identifiers)
    if request.catalysts is not None:
        upstream.append(request.catalysts.provenance.input_fingerprint)
        sources.extend(request.catalysts.provenance.source_identifiers)
    if request.scores is not None:
        upstream.append(request.scores.provenance.input_fingerprint)
        sources.extend(request.scores.provenance.source_identifiers)
    if request.briefing is not None:
        upstream.append(request.briefing.provenance.input_fingerprint)
        sources.append(request.briefing.briefing_id)
    if request.dashboard is not None:
        upstream.append(request.dashboard.provenance.input_fingerprint)
        sources.append(request.dashboard.dashboard_output_id)

    return AnalystProvenance(
        analyst_definition_version=ANALYST_DEFINITION_VERSION_V1,
        policy_version_id=POLICY_VERSION_V1,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
        digest_method_id=DIGEST_METHOD_V1,
        ordering_policy_id=ORDERING_POLICY_V1,
        as_of=request.as_of,
        config_fingerprint=build_config_fingerprint(request),
        input_fingerprint=build_input_fingerprint(request),
        upstream_fingerprints=tuple(upstream),
        upstream_pipeline_failure_identity=request.upstream_pipeline_failure_identity,
        source_identifiers=tuple(dict.fromkeys(sources)),
    )
