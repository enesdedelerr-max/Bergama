"""Runtime state compatibility and ownership helpers (#406)."""

from __future__ import annotations

from bergama_strategy_sdk.errors import StrategyStateError
from bergama_strategy_sdk.execution import StrategyExecutionOutput
from bergama_strategy_sdk.state import NextStrategyState, PreviousStrategyState

SUPPORTED_STATE_SCHEMA_VERSION = "1.0.0"


def validate_previous_state(
    previous_state: PreviousStrategyState | None,
    *,
    strategy_id: str,
    strategy_instance_id: str,
    supported_state_schema_version: str = SUPPORTED_STATE_SCHEMA_VERSION,
) -> None:
    if previous_state is None:
        return
    if previous_state.state_schema_version != supported_state_schema_version:
        raise StrategyStateError(detail="state_schema_version_mismatch")
    if previous_state.strategy_id is not None and previous_state.strategy_id != strategy_id:
        raise StrategyStateError(detail="state_strategy_id_mismatch")
    if (
        previous_state.strategy_instance_id is not None
        and previous_state.strategy_instance_id != strategy_instance_id
    ):
        raise StrategyStateError(detail="state_strategy_instance_id_mismatch")


def validate_next_state(
    output: StrategyExecutionOutput,
    *,
    previous_state: PreviousStrategyState | None,
    strategy_id: str,
    strategy_instance_id: str,
    supported_state_schema_version: str = SUPPORTED_STATE_SCHEMA_VERSION,
) -> NextStrategyState | None:
    next_state = output.next_state
    if next_state is None:
        return None
    if not isinstance(next_state, NextStrategyState):
        raise StrategyStateError(detail="next_state_type_invalid")
    if next_state.state_schema_version != supported_state_schema_version:
        raise StrategyStateError(detail="next_state_schema_version_mismatch")
    if (
        previous_state is not None
        and next_state.state_schema_version != previous_state.state_schema_version
    ):
        raise StrategyStateError(detail="state_schema_auto_migration_forbidden")
    if next_state.strategy_id is not None and next_state.strategy_id != strategy_id:
        raise StrategyStateError(detail="next_state_strategy_id_mismatch")
    if (
        next_state.strategy_instance_id is not None
        and next_state.strategy_instance_id != strategy_instance_id
    ):
        raise StrategyStateError(detail="next_state_strategy_instance_id_mismatch")
    return next_state
