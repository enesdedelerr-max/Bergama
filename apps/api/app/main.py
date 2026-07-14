"""Process entrypoint — settings are not loaded at import time."""

from __future__ import annotations

import uvicorn

from app.core.config import get_settings


def run() -> None:
    """Console script entrypoint: `uv run app`."""
    settings = get_settings()
    uvicorn.run(
        "app.factory:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
