"""Explicit application-scoped dependency container (Issue #206)."""

from __future__ import annotations

from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from app.core.clock import Clock, JtiGenerator, SystemClock, UuidJtiGenerator
from app.core.config import AppSettings
from app.core.logging import get_logger, structured_extra
from app.services.token_service import TokenService

logger = get_logger(__name__)


@dataclass(slots=True)
class AppContainer:
    """Long-lived runtime dependencies for one FastAPI application instance.

    Application scope only. Request-scoped data (principals, request IDs) must
    never be stored here.
    """

    settings: AppSettings
    clock: Clock
    jti_generator: JtiGenerator
    token_service: TokenService
    _exit_stack: AsyncExitStack = field(default_factory=AsyncExitStack, repr=False, compare=False)
    _closed: bool = field(default=False, init=False, repr=False, compare=False)

    async def aclose(self) -> None:
        """Release owned async resources. Idempotent."""
        if self._closed:
            return
        self._closed = True
        try:
            await self._exit_stack.aclose()
        except Exception:
            logger.error(
                "container cleanup failed",
                exc_info=True,
                extra=structured_extra(
                    event="container.cleanup.failed",
                    source="container",
                ),
            )
            raise


def build_container(
    settings: AppSettings,
    *,
    clock: Clock | None = None,
    jti_generator: JtiGenerator | None = None,
    token_service: TokenService | None = None,
) -> AppContainer:
    """Construct an application container. All long-lived deps are owned here."""
    resolved_clock = clock if clock is not None else SystemClock()
    resolved_jti = jti_generator if jti_generator is not None else UuidJtiGenerator()
    resolved_token = (
        token_service
        if token_service is not None
        else TokenService(
            settings,
            clock=resolved_clock,
            jti_factory=resolved_jti,
        )
    )
    return AppContainer(
        settings=settings,
        clock=resolved_clock,
        jti_generator=resolved_jti,
        token_service=resolved_token,
    )
