"""Process entrypoint."""

from __future__ import annotations

import uvicorn

from app.core.config import get_settings
from app.factory import create_app

app = create_app()


def run() -> None:
    """Console script entrypoint: `uv run app`."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        factory=False,
    )


if __name__ == "__main__":
    run()
