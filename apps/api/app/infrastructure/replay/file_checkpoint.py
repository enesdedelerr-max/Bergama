"""Atomic file-backed Replay checkpoint store (#308)."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from app.market_data.replay.checkpoint import ReplayCheckpoint
from app.market_data.replay.errors import ReplayCheckpointCorruptError, ReplayError


class FileCheckpointStore:
    """Deterministic JSON checkpoints with temp-file + os.replace."""

    def __init__(self, directory: str | Path) -> None:
        self._root = Path(directory)
        if not self._root.is_absolute():
            raise ReplayError(
                "replay.invalid_request",
                detail="checkpoint directory must be absolute",
            )
        self._root.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            os.chmod(self._root, 0o700)
        self._closed = False

    async def load(self, replay_id: str) -> ReplayCheckpoint | None:
        self._ensure_open()
        path = self._path_for(replay_id)
        if not path.exists():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return ReplayCheckpoint.model_validate(data)
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise ReplayCheckpointCorruptError(detail="checkpoint file corrupt or invalid") from exc

    async def save(self, checkpoint: ReplayCheckpoint) -> None:
        self._ensure_open()
        path = self._path_for(checkpoint.replay_id)
        payload = checkpoint.model_dump(mode="json")
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=True)
        encoded += "\n"
        try:
            fd, tmp_name = tempfile.mkstemp(
                prefix=f".{checkpoint.replay_id}.",
                suffix=".tmp",
                dir=str(self._root),
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(encoded)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp_name, path)
                with contextlib.suppress(OSError):
                    os.chmod(path, 0o600)
            finally:
                if os.path.exists(tmp_name):
                    with contextlib.suppress(OSError):
                        os.unlink(tmp_name)
        except ReplayCheckpointCorruptError:
            raise
        except OSError as exc:
            raise ReplayError(
                "replay.checkpoint_corrupt",
                detail="checkpoint write failed",
            ) from exc

    async def aclose(self) -> None:
        self._closed = True

    def _path_for(self, replay_id: str) -> Path:
        safe = replay_id.strip()
        if not safe or "/" in safe or "\\" in safe or ".." in safe or "\x00" in safe:
            raise ReplayError(
                "replay.invalid_request",
                detail="unsafe replay_id for checkpoint path",
            )
        return self._root / f"{safe}.json"

    def _ensure_open(self) -> None:
        if self._closed:
            raise ReplayError("replay.closed", detail="checkpoint store is closed")
