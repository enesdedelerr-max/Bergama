"""Atomic file-backed Backfill checkpoint store (#309)."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from app.market_data.backfill.checkpoint import BackfillCheckpoint
from app.market_data.backfill.errors import BackfillCheckpointCorruptError, BackfillError


class FileBackfillCheckpointStore:
    """Deterministic JSON checkpoints with temp-file + os.replace."""

    def __init__(self, directory: str | Path) -> None:
        self._root = Path(directory)
        if not self._root.is_absolute():
            raise BackfillError(
                "backfill.invalid_request",
                detail="checkpoint directory must be absolute",
            )
        self._root.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            os.chmod(self._root, 0o700)
        self._closed = False

    async def load(self, backfill_id: str) -> BackfillCheckpoint | None:
        self._ensure_open()
        path = self._path_for(backfill_id)
        if not path.exists():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return BackfillCheckpoint.model_validate(data)
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise BackfillCheckpointCorruptError(
                detail="checkpoint file corrupt or invalid"
            ) from exc

    async def save(self, checkpoint: BackfillCheckpoint) -> None:
        self._ensure_open()
        path = self._path_for(checkpoint.backfill_id)
        payload = checkpoint.model_dump(mode="json")
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=True)
        encoded += "\n"
        try:
            fd, tmp_name = tempfile.mkstemp(
                prefix=f".{checkpoint.backfill_id}.",
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
        except BackfillCheckpointCorruptError:
            raise
        except OSError as exc:
            raise BackfillError(
                "backfill.checkpoint_corrupt",
                detail="checkpoint write failed",
            ) from exc

    async def aclose(self) -> None:
        self._closed = True

    def _path_for(self, backfill_id: str) -> Path:
        safe = backfill_id.strip()
        if not safe or "/" in safe or "\\" in safe or ".." in safe or "\x00" in safe:
            raise BackfillError(
                "backfill.invalid_request",
                detail="unsafe backfill_id for checkpoint path",
            )
        return self._root / f"{safe}.json"

    def _ensure_open(self) -> None:
        if self._closed:
            raise BackfillError("backfill.closed", detail="checkpoint store is closed")
