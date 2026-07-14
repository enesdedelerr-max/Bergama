"""Sprint 2 API runtime smoke — start process, health/auth/registry modes, evidence."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "gates") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "gates"))

from sprint2_common import (  # noqa: E402
    ensure_no_secrets,
    utc_now,
    write_json,
)

BOOTSTRAP_KEY = "sprint2-gate-bootstrap-jwt-signing-key-32b"
WAIT_TIMEOUT_SECONDS = 30.0
POLL_INTERVAL_SECONDS = 0.2


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http(
    method: str,
    url: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 5.0,
) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status), {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), {k.lower(): v for k, v in exc.headers.items()}, exc.read()


def _wait_ready(url: str, proc: subprocess.Popen[str], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            msg = f"API process exited early with code {proc.returncode}"
            raise RuntimeError(msg)
        try:
            code, _, _ = _http("GET", url, timeout=1.0)
            if code == 200:
                return
        except Exception:
            pass
        time.sleep(POLL_INTERVAL_SECONDS)
    msg = f"timed out waiting for {url}"
    raise RuntimeError(msg)


def _terminate(proc: subprocess.Popen[str], *, grace: float = 5.0) -> None:
    if proc.poll() is not None:
        return
    proc.send_signal(signal.SIGTERM)
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.1)
    if proc.poll() is None:
        proc.kill()
        proc.wait(timeout=5)


def _base_env(port: int) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "BERGAMA_ENVIRONMENT": "test",
            "BERGAMA_HOST": "127.0.0.1",
            "BERGAMA_PORT": str(port),
            "BERGAMA_DEBUG": "false",
            "BERGAMA_LOG_LEVEL": "INFO",
            "BERGAMA_BOOTSTRAP_AUTH_ENABLED": "true",
            "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY": BOOTSTRAP_KEY,
            "BERGAMA_KAFKA__ENABLED": "false",
            "BERGAMA_REGISTRY__ENABLED": "false",
            "BERGAMA_DOCS_ENABLED": "true",
            "BERGAMA_OPENAPI_ENABLED": "true",
            # Avoid accidental dotenv secret files influencing smoke.
            "BERGAMA_POSTGRES_REQUIRED": "false",
            "BERGAMA_REDIS_REQUIRED": "false",
        }
    )
    return env


def _start_api(env: dict[str, str], log_path: Path) -> subprocess.Popen[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        ["uv", "run", "app"],
        cwd=ROOT / "apps" / "api",
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    proc._bergama_log_handle = handle  # type: ignore[attr-defined]
    return proc


def _close_log(proc: subprocess.Popen[str]) -> None:
    handle = getattr(proc, "_bergama_log_handle", None)
    if handle is not None:
        handle.close()


def _write_valid_registry(directory: Path) -> None:
    yaml_doc = """registry:
  id: market-data-topics
  type: topic
  version: 1.0.0
  schema_version: 1.0.0
  owner: platform
  created_at: 2026-01-01T00:00:00Z
  dependencies: []
  metadata: {}
payload:
  topics: [events, market-data]
"""
    (directory / "topics.yaml").write_text(yaml_doc, encoding="utf-8")
    json_doc = {
        "registry": {
            "id": "secondary-contract",
            "type": "generic",
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "owner": "platform",
            "created_at": "2026-01-01T00:00:00Z",
            "dependencies": [],
            "metadata": {},
        },
        "payload": {"ok": True},
    }
    (directory / "secondary.json").write_text(json.dumps(json_doc), encoding="utf-8")


def _assert_health(base: str, evidence: Path) -> None:
    evidence.mkdir(parents=True, exist_ok=True)
    for path in ("/health/live", "/health/startup", "/health/ready", "/health", "/ready"):
        code, headers, body = _http("GET", base + path)
        if code != 200:
            msg = f"{path} expected 200 got {code}"
            raise RuntimeError(msg)
        text = body.decode("utf-8")
        ensure_no_secrets(text, context=path)
        cc = headers.get("cache-control", "")
        if "no-store" not in cc.lower():
            msg = f"{path} missing Cache-Control: no-store"
            raise RuntimeError(msg)
        if "x-request-id" not in headers:
            msg = f"{path} missing X-Request-ID"
            raise RuntimeError(msg)
        if "x-correlation-id" not in headers:
            msg = f"{path} missing X-Correlation-ID"
            raise RuntimeError(msg)
        payload = json.loads(text)
        for field in ("service", "version", "environment"):
            if field not in payload:
                msg = f"{path} missing operational field {field}"
                raise RuntimeError(msg)
        write_json(evidence / f"{path.strip('/').replace('/', '_')}.json", payload)
        (evidence / f"{path.strip('/').replace('/', '_')}.headers.txt").write_text(
            "\n".join(f"{k}: {v}" for k, v in sorted(headers.items())) + "\n",
            encoding="utf-8",
        )
        if path == "/health/ready":
            names = {c["name"]: c["status"] for c in payload.get("checks", [])}
            if names.get("kafka") != "skipped":
                msg = f"kafka check expected skipped, got {names.get('kafka')}"
                raise RuntimeError(msg)
            if names.get("registry") != "skipped":
                msg = f"registry check expected skipped, got {names.get('registry')}"
                raise RuntimeError(msg)


def _assert_auth(base: str, evidence: Path, log_text: str) -> None:
    evidence.mkdir(parents=True, exist_ok=True)
    code, headers, body = _http(
        "POST",
        base + "/api/v1/auth/token",
        body=b'{"grant_type":"bootstrap"}',
        headers={"Content-Type": "application/json"},
    )
    if code != 200:
        msg = f"token endpoint expected 200 got {code}: {body!r}"
        raise RuntimeError(msg)
    token_payload = json.loads(body.decode("utf-8"))
    if not token_payload.get("access_token"):
        raise RuntimeError("access_token missing")
    if str(token_payload.get("token_type", "")).lower() != "bearer":
        raise RuntimeError("token_type must be bearer")
    if int(token_payload.get("expires_in", 0)) <= 0:
        raise RuntimeError("expires_in must be positive")
    cc = headers.get("cache-control", "")
    if "no-store" not in cc.lower():
        raise RuntimeError("token response must include Cache-Control: no-store")
    # Store sanitized evidence (no raw token).
    sanitized = {
        "token_type": token_payload["token_type"],
        "expires_in": token_payload["expires_in"],
        "access_token_present": True,
    }
    write_json(evidence / "token_response_sanitized.json", sanitized)
    token = token_payload["access_token"]
    code_me, _, body_me = _http(
        "GET",
        base + "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if code_me != 200:
        raise RuntimeError(f"/auth/me expected 200 got {code_me}")
    write_json(evidence / "me.json", json.loads(body_me.decode("utf-8")))
    code_unauth, headers_unauth, _ = _http("GET", base + "/api/v1/auth/me")
    if code_unauth != 401:
        raise RuntimeError(f"unauthenticated /auth/me expected 401 got {code_unauth}")
    www = headers_unauth.get("www-authenticate", "")
    if "bearer" not in www.lower():
        raise RuntimeError("WWW-Authenticate: Bearer required on 401")
    if token in log_text:
        raise RuntimeError("raw access token appeared in process logs")


def _assert_log_events(log_text: str, evidence: Path) -> None:
    required = (
        "application.starting",
        "application.started",
        "http.request.started",
        "http.request.completed",
        "auth.token.issued",
        "application.stopping",
        "application.stopped",
    )
    for event in required:
        if event not in log_text:
            raise RuntimeError(f"missing log event {event}")
    evidence.mkdir(parents=True, exist_ok=True)
    sanitized_lines = []
    for line in log_text.splitlines():
        if "access_token" in line.lower() or "authorization" in line.lower():
            continue
        if BOOTSTRAP_KEY in line:
            raise RuntimeError("bootstrap signing key appeared in logs")
        sanitized_lines.append(line)
    evidence.joinpath("runtime.log").write_text("\n".join(sanitized_lines) + "\n", encoding="utf-8")
    write_json(
        evidence / "log_events.json",
        {"required_events_found": list(required)},
    )


def _assert_staging_json_logs(evidence_root: Path) -> None:
    """Staging-style JSON formatter evidence (bootstrap auth disabled)."""
    port = _free_port()
    env = _base_env(port)
    env["BERGAMA_ENVIRONMENT"] = "staging"
    env["BERGAMA_BOOTSTRAP_AUTH_ENABLED"] = "false"
    env.pop("BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY", None)
    log_path = evidence_root / "logs" / "staging-json.log"
    proc = _start_api(env, log_path)
    base = f"http://127.0.0.1:{port}"
    try:
        _wait_ready(base + "/health/live", proc, WAIT_TIMEOUT_SECONDS)
        _http("GET", base + "/health/live")
        time.sleep(0.2)
    finally:
        _terminate(proc)
        _close_log(proc)
    log_text = log_path.read_text(encoding="utf-8")
    json_line = None
    for line in log_text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("{") and stripped.endswith("}")):
            continue
        payload = json.loads(stripped)
        if "event" in payload:
            json_line = stripped
            break
    if json_line is None:
        raise RuntimeError("staging smoke expected at least one JSON log line with event")
    payload = json.loads(json_line)
    for key in ("timestamp", "level", "event", "service", "environment"):
        if key not in payload:
            raise RuntimeError(f"JSON log missing {key}")
    ensure_no_secrets(json_line, context="staging json log")
    write_json(evidence_root / "logging" / "staging_json_sample.json", payload)


def _run_baseline(evidence_root: Path) -> None:
    port = _free_port()
    env = _base_env(port)
    log_path = evidence_root / "logs" / "baseline-api.log"
    proc = _start_api(env, log_path)
    base = f"http://127.0.0.1:{port}"
    try:
        _wait_ready(base + "/health/live", proc, WAIT_TIMEOUT_SECONDS)
        _assert_health(base, evidence_root / "health")
        _assert_auth(base, evidence_root / "auth", "")
        time.sleep(0.3)
    finally:
        _terminate(proc)
        _close_log(proc)
    log_text = log_path.read_text(encoding="utf-8")
    if BOOTSTRAP_KEY in log_text:
        raise RuntimeError("signing key leaked into logs")
    ensure_no_secrets(log_text, context="baseline log")
    _assert_log_events(log_text, evidence_root / "logging")
    # Raw JWT fragments should not be logged with token field names.
    if "eyJ" in log_text and ("access_token" in log_text.lower() or "bearer eyj" in log_text.lower()):
        raise RuntimeError("token-like material in logs")


def _run_registry_valid(evidence_root: Path) -> None:
    port = _free_port()
    with tempfile.TemporaryDirectory(prefix="bergama-registry-") as tmp:
        reg_dir = Path(tmp)
        _write_valid_registry(reg_dir)
        env = _base_env(port)
        env["BERGAMA_REGISTRY__ENABLED"] = "true"
        env["BERGAMA_REGISTRY__PATHS"] = json.dumps([str(reg_dir)])
        env["BERGAMA_REGISTRY__REQUIRED_REGISTRY_IDS"] = json.dumps(["market-data-topics"])
        env["BERGAMA_REGISTRY__LOAD_ON_STARTUP"] = "true"
        log_path = evidence_root / "logs" / "registry-valid.log"
        proc = _start_api(env, log_path)
        base = f"http://127.0.0.1:{port}"
        try:
            _wait_ready(base + "/health/startup", proc, WAIT_TIMEOUT_SECONDS)
            code, _, body = _http("GET", base + "/health/ready")
            if code != 200:
                raise RuntimeError(f"registry ready expected 200 got {code}")
            payload = json.loads(body.decode("utf-8"))
            text = body.decode("utf-8")
            if str(reg_dir) in text:
                raise RuntimeError("registry path leaked into health")
            names = {c["name"]: c for c in payload.get("checks", [])}
            if names.get("registry", {}).get("status") != "pass":
                raise RuntimeError(f"registry health expected pass got {names.get('registry')}")
            write_json(evidence_root / "registry" / "ready_valid.json", payload)
        finally:
            _terminate(proc)
            _close_log(proc)


def _run_registry_invalid(evidence_root: Path) -> None:
    port = _free_port()
    with tempfile.TemporaryDirectory(prefix="bergama-registry-bad-") as tmp:
        reg_dir = Path(tmp)
        (reg_dir / "bad.yaml").write_text("registry: []\npayload: {}\n", encoding="utf-8")
        env = _base_env(port)
        env["BERGAMA_REGISTRY__ENABLED"] = "true"
        env["BERGAMA_REGISTRY__PATHS"] = json.dumps([str(reg_dir)])
        env["BERGAMA_REGISTRY__LOAD_ON_STARTUP"] = "true"
        log_path = evidence_root / "logs" / "registry-invalid.log"
        proc = _start_api(env, log_path)
        try:
            deadline = time.monotonic() + WAIT_TIMEOUT_SECONDS
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    break
                time.sleep(POLL_INTERVAL_SECONDS)
            if proc.poll() is None:
                _terminate(proc)
                raise RuntimeError("invalid registry startup did not fail")
            if proc.returncode == 0:
                raise RuntimeError("invalid registry startup exited zero")
            write_json(
                evidence_root / "registry" / "invalid_startup.json",
                {"exit_code": proc.returncode, "failed_as_expected": True, "at": utc_now()},
            )
        finally:
            _terminate(proc)
            _close_log(proc)


def main() -> int:
    evidence = ROOT / "artifacts" / "sprint2" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "logs").mkdir(parents=True, exist_ok=True)
    (evidence / "registry").mkdir(parents=True, exist_ok=True)
    print(f"[smoke-api-runtime] start {utc_now()}")
    _run_baseline(evidence)
    print("[smoke-api-runtime] baseline PASS")
    _assert_staging_json_logs(evidence)
    print("[smoke-api-runtime] staging-json PASS")
    _run_registry_valid(evidence)
    print("[smoke-api-runtime] registry-valid PASS")
    _run_registry_invalid(evidence)
    print("[smoke-api-runtime] registry-invalid PASS")
    print(f"[smoke-api-runtime] complete {utc_now()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 — smoke boundary
        print(f"[smoke-api-runtime] FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
