"""Policy Version resolver and binder registry."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager

from app.premarket.errors import ScoreUnsupportedPolicyError
from app.premarket.scoring.models import ScoreConfig
from app.premarket.scoring.policy import POLICY_VERSION_V1, WEIGHT_PROFILE_DEFAULT_V1
from app.premarket.scoring.policy_v1.binder import PolicyVersionV1Binder
from app.premarket.scoring.ports import BoundPolicyContext, PolicyVersionBinder

_DEFAULT_BINDERS: dict[str, PolicyVersionBinder] = {
    POLICY_VERSION_V1: PolicyVersionV1Binder(),
}
_BINDERS: dict[str, PolicyVersionBinder] = dict(_DEFAULT_BINDERS)


def resolve_policy(config: ScoreConfig) -> BoundPolicyContext:
    """Bind evaluation to exactly one registered Policy Version implementation."""
    binder = _BINDERS.get(config.policy_version_id)
    if binder is None:
        raise ScoreUnsupportedPolicyError(
            detail=f"unsupported_policy_version:{config.policy_version_id}"
        )
    if config.weight_profile_id != binder.weight_profile_id:
        raise ScoreUnsupportedPolicyError(
            detail=(
                "unsupported_weight_profile:"
                f"{config.weight_profile_id}:expected:{binder.weight_profile_id}"
            )
        )
    if config.weight_profile_id != WEIGHT_PROFILE_DEFAULT_V1:
        raise ScoreUnsupportedPolicyError(
            detail=f"unsupported_weight_profile:{config.weight_profile_id}"
        )

    params = binder.resolve_params()
    if config.ordering_policy_id != params.ordering_policy_id:
        raise ScoreUnsupportedPolicyError(
            detail=f"unsupported_ordering_policy:{config.ordering_policy_id}"
        )
    if config.score_quantize_policy_id != params.score_quantize_policy_id:
        raise ScoreUnsupportedPolicyError(
            detail=f"unsupported_quantize_policy:{config.score_quantize_policy_id}"
        )

    return BoundPolicyContext(
        params=params,
        weight_profile=binder.weight_profile(),
        feature_extractors=tuple(binder.feature_extractors()),
        identity_builder=binder.identity_builder(),
        ordering_policy_id=params.ordering_policy_id,
    )


@contextmanager
def override_binder_registry(
    binders: Mapping[str, PolicyVersionBinder],
) -> Iterator[None]:
    """Temporarily replace the Policy Version binder registry (tests only).

    Exception-safe for single-threaded use: ``finally`` always restores the
    previous registry snapshot. The process-global ``_BINDERS`` map is **not**
    concurrency-safe; parallel test workers or multi-threaded callers must not
    share overrides. That limitation is accepted for the current in-process
    Premarket Scoring foundation and is not a redesign of DI architecture.
    """
    global _BINDERS
    previous = _BINDERS
    _BINDERS = dict(binders)
    try:
        yield
    finally:
        _BINDERS = previous


def reset_binder_registry() -> None:
    """Restore the production Policy Version binder registry."""
    global _BINDERS
    _BINDERS = dict(_DEFAULT_BINDERS)


def registered_policy_version_ids() -> tuple[str, ...]:
    """Return currently registered Policy Version IDs (deterministic order)."""
    return tuple(sorted(_BINDERS))
