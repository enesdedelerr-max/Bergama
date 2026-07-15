from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gates import gate_sprint3
from scripts.gates import build_sprint3_release
from scripts.gates.sprint3_common import (
    EVIDENCE_VERSION,
    GO_DECISION,
    CommandResult,
    CommandSpec,
    environment_for_spec,
    normalize_status,
    sanitized_gate_environment,
    write_checksums,
    write_json,
)
from scripts.gates.validate_sprint3_evidence import validate_evidence

COMMIT = "408240dcaad8ca81d7351bfa3671a161f1061504"


@pytest.mark.parametrize(
    "body",
    [
        "698 passed, 6 skipped, 5 deselected in 4.40s",
        "1 passed, 3 skipped in 0.02s",
        "29 passed in 0.25s",
        "1 skipped in 0.01s",
        "10 passed, 1 xfailed, 2 deselected in 0.50s",
        "some tests were skipped by pytest markers",
    ],
)
def test_exit_zero_pytest_skip_counts_are_pass(body: str) -> None:
    status, reason = normalize_status(exit_code=0, body=body)
    assert status == "PASS"
    assert reason is None


def test_explicit_smoke_marker_is_skipped() -> None:
    status, reason = normalize_status(
        exit_code=0,
        body=(
            "BERGAMA_SMOKE_STATUS=SKIPPED\n"
            "smoke-api-polygon SKIPPED (set BERGAMA_POLYGON_SMOKE=1)"
        ),
    )
    assert status == "SKIPPED"
    assert reason == "BERGAMA_SMOKE_STATUS=SKIPPED"


def test_json_smoke_marker_is_skipped() -> None:
    status, reason = normalize_status(
        exit_code=0,
        body='{"status": "SKIPPED", "reason": "BERGAMA_KAFKA_SMOKE is not enabled"}',
    )
    assert status == "SKIPPED"
    assert reason == "BERGAMA_KAFKA_SMOKE is not enabled"


@pytest.mark.parametrize(
    "body",
    [
        "FAIL: BERGAMA_KAFKA__ENABLED=true is required",
        "smoke-api-polygon failed after being explicitly enabled",
    ],
)
def test_nonzero_exit_is_fail(body: str) -> None:
    status, reason = normalize_status(exit_code=1, body=body)
    assert status == "FAIL"
    assert reason is None


def test_sanitized_gate_environment_removes_runtime_settings() -> None:
    env = {
        "PATH": "/usr/bin",
        "BERGAMA_ENVIRONMENT": "local",
        "BERGAMA_KAFKA__ENABLED": "true",
        "BERGAMA_KAFKA__BOOTSTRAP_SERVERS": '["127.0.0.1:9092"]',
        "BERGAMA_ICEBERG_WRITER__ENABLED": "true",
        "BERGAMA_ICEBERG_WRITER__SECRET_KEY": "local-secret",
        "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY": "parent-secret",
        "BERGAMA_SPRINT3_RUNTIME_SMOKE": "1",
        "BERGAMA_REPLAY_ENGINE_SMOKE": "1",
    }

    sanitized = sanitized_gate_environment(env)

    assert sanitized == {
        "PATH": "/usr/bin",
        "BERGAMA_REPLAY_ENGINE_SMOKE": "1",
    }


def test_non_runtime_specs_receive_sanitized_environment() -> None:
    env = {
        "PATH": "/usr/bin",
        "BERGAMA_ENVIRONMENT": "local",
        "BERGAMA_KAFKA__ENABLED": "true",
        "BERGAMA_ICEBERG_WRITER__CATALOG_URI": "http://127.0.0.1:8181",
        "BERGAMA_ICEBERG_WRITER__ACCESS_KEY": "local-access",
        "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY": "parent-secret",
    }
    spec = CommandSpec(
        id="test-api-kafka-publish-adapter",
        command=("make", "test-api-kafka-publish-adapter"),
        group="focused-tests",
    )

    child = environment_for_spec(spec, env)

    assert child == {"PATH": "/usr/bin"}


def test_runtime_smoke_spec_receives_runtime_environment_only_for_that_step() -> None:
    env = {
        "PATH": "/usr/bin",
        "BERGAMA_ENVIRONMENT": "local",
        "BERGAMA_KAFKA__ENABLED": "true",
        "BERGAMA_KAFKA__BOOTSTRAP_SERVERS": '["127.0.0.1:9092"]',
        "BERGAMA_ICEBERG_WRITER__ENABLED": "true",
        "BERGAMA_ICEBERG_WRITER__SECRET_KEY": "local-secret",
    }
    spec = CommandSpec(
        id="smoke-sprint3-runtime",
        command=("make", "smoke-sprint3-runtime"),
        group="runtime-smoke",
    )

    child = environment_for_spec(spec, env)

    assert child["PATH"] == "/usr/bin"
    assert child["BERGAMA_ENVIRONMENT"] == "local"
    assert child["BERGAMA_KAFKA__ENABLED"] == "true"
    assert child["BERGAMA_KAFKA__BOOTSTRAP_SERVERS"] == '["127.0.0.1:9092"]'
    assert child["BERGAMA_ICEBERG_WRITER__ENABLED"] == "true"
    assert child["BERGAMA_ICEBERG_WRITER__SECRET_KEY"] == "local-secret"


def test_spec_env_is_applied_after_sanitization() -> None:
    env = {
        "PATH": "/usr/bin",
        "BERGAMA_KAFKA__ENABLED": "true",
        "BERGAMA_REPLAY_ENGINE_SMOKE": "0",
    }
    spec = CommandSpec(
        id="smoke-api-replay-engine",
        command=("make", "smoke-api-replay-engine"),
        group="offline-smokes",
        env={"BERGAMA_REPLAY_ENGINE_SMOKE": "1"},
    )

    child = environment_for_spec(spec, env)

    assert child == {
        "PATH": "/usr/bin",
        "BERGAMA_REPLAY_ENGINE_SMOKE": "1",
    }


def test_openapi_child_environment_uses_ephemeral_bootstrap_key() -> None:
    source = {
        "PATH": "/usr/bin",
        "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY": "parent-secret",
    }

    child = build_sprint3_release._openapi_child_environment(source)

    assert source["BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY"] == "parent-secret"
    assert child["PATH"] == "/usr/bin"
    assert child["BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY"] != "parent-secret"
    assert len(child["BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY"]) >= 48


def test_openapi_generation_scopes_bootstrap_key_to_child_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_env: dict[str, str] = {}
    monkeypatch.setenv("BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY", "parent-secret")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal captured_env
        captured_env = dict(kwargs["env"])
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout='{"openapi": "3.1.0", "paths": {}}\n',
            stderr="",
        )

    monkeypatch.setattr(build_sprint3_release.subprocess, "run", fake_run)

    schema = build_sprint3_release._generate_openapi(tmp_path)

    assert schema["openapi"] == "3.1.0"
    assert captured_env["BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY"] != "parent-secret"
    assert len(captured_env["BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY"]) >= 48
    assert os.environ["BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY"] == "parent-secret"


def test_openapi_generation_succeeds_without_parent_bootstrap_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_env: dict[str, str] = {}
    monkeypatch.delenv("BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY", raising=False)

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal captured_env
        captured_env = dict(kwargs["env"])
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout='{"openapi": "3.1.0", "paths": {"/health": {}}}\n',
            stderr="",
        )

    monkeypatch.setattr(build_sprint3_release.subprocess, "run", fake_run)

    schema = build_sprint3_release._generate_openapi(tmp_path)

    assert schema["paths"] == {"/health": {}}
    assert "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY" in captured_env
    assert "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY" not in os.environ


def test_openapi_output_is_independent_of_ephemeral_bootstrap_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_keys: list[str] = []

    def fake_token_urlsafe(length: int) -> str:
        return f"ephemeral-key-{len(observed_keys)}-{'x' * length}"

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        observed_keys.append(kwargs["env"]["BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY"])
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout='{"openapi": "3.1.0", "paths": {"/health": {}}}\n',
            stderr="",
        )

    monkeypatch.setattr(build_sprint3_release.secrets, "token_urlsafe", fake_token_urlsafe)
    monkeypatch.setattr(build_sprint3_release.subprocess, "run", fake_run)

    first = build_sprint3_release._generate_openapi(tmp_path)
    second = build_sprint3_release._generate_openapi(tmp_path)

    assert first == second
    assert len(observed_keys) == 2
    assert observed_keys[0] != observed_keys[1]


def test_openapi_generation_does_not_echo_bootstrap_key_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_key = "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY=raw-test-secret"

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="",
            stderr=f"bad env {raw_key}",
        )

    monkeypatch.setattr(build_sprint3_release.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc:
        build_sprint3_release._generate_openapi(tmp_path)

    assert "raw-test-secret" not in str(exc.value)
    assert "secret-like material" in str(exc.value)


def test_openapi_generation_does_not_embed_child_stderr_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="",
            stderr="raw-child-output-that-must-not-be-logged",
        )

    monkeypatch.setattr(build_sprint3_release.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc:
        build_sprint3_release._generate_openapi(tmp_path)

    assert "raw-child-output-that-must-not-be-logged" not in str(exc.value)
    assert "OpenAPI generation failed with exit code 1" in str(exc.value)


def _sample_spdx_sbom(*, namespace: object, package_version: str = "1.0.0") -> dict[str, Any]:
    return {
        "SPDXID": "SPDXRef-DOCUMENT",
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "name": "dir:apps/api",
        "documentNamespace": namespace,
        "creationInfo": {
            "created": "2026-07-15T01:02:03Z",
            "creators": ["Tool: syft-1.0.0"],
        },
        "packages": [
            {
                "SPDXID": "SPDXRef-Package-b",
                "name": "beta",
                "versionInfo": package_version,
                "checksums": [{"algorithm": "SHA256", "checksumValue": "b" * 64}],
            },
            {
                "SPDXID": "SPDXRef-Package-a",
                "name": "alpha",
                "versionInfo": "2.0.0",
                "checksums": [{"algorithm": "SHA256", "checksumValue": "a" * 64}],
            },
        ],
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": "SPDXRef-Package-b",
            },
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": "SPDXRef-Package-a",
            },
        ],
    }


def _normalize_sample_sbom(sbom: dict[str, Any], *, commit: str = COMMIT) -> dict[str, Any]:
    return build_sprint3_release._normalize_sbom(
        sbom,
        normalized_created="2026-07-15T00:00:00Z",
        validated_commit=commit,
    )


def test_sbom_document_namespace_is_deterministic_for_same_commit() -> None:
    first = _sample_spdx_sbom(
        namespace="https://anchore.com/syft/dir/apps/api-9378a740-f44a-4043-a4a2-8c091ca3e80d"
    )
    second = _sample_spdx_sbom(
        namespace="https://anchore.com/syft/dir/apps/api-13bc5e23-0b20-40aa-833c-b59e00c6df2c"
    )

    normalized_first = _normalize_sample_sbom(first)
    normalized_second = _normalize_sample_sbom(second)

    assert normalized_first == normalized_second
    assert normalized_first["documentNamespace"] == (
        f"https://github.com/enesdedelerr-max/Bergama/sbom/sprint-3/{COMMIT}"
    )
    assert "9378a740-f44a-4043-a4a2-8c091ca3e80d" not in normalized_first["documentNamespace"]
    assert "13bc5e23-0b20-40aa-833c-b59e00c6df2c" not in normalized_second["documentNamespace"]


def test_sbom_document_namespace_changes_by_commit() -> None:
    other_commit = "508240dcaad8ca81d7351bfa3671a161f1061505"
    first = _normalize_sample_sbom(
        _sample_spdx_sbom(namespace="https://anchore.com/syft/dir/apps/api-a"),
        commit=COMMIT,
    )
    second = _normalize_sample_sbom(
        _sample_spdx_sbom(namespace="https://anchore.com/syft/dir/apps/api-a"),
        commit=other_commit,
    )

    assert first["documentNamespace"] != second["documentNamespace"]
    assert first["documentNamespace"].endswith(f"/{COMMIT}")
    assert second["documentNamespace"].endswith(f"/{other_commit}")


@pytest.mark.parametrize(
    "namespace",
    [
        None,
        "",
        123,
        "not-a-uri",
        "http://anchore.com/syft/dir/apps/api-random",
    ],
)
def test_sbom_document_namespace_must_be_valid_absolute_https_uri(namespace: object) -> None:
    with pytest.raises(RuntimeError):
        _normalize_sample_sbom(_sample_spdx_sbom(namespace=namespace))


def test_sbom_normalization_preserves_packages_relationships_and_core_spdx_fields() -> None:
    source = _sample_spdx_sbom(namespace="https://anchore.com/syft/dir/apps/api-random")

    normalized = _normalize_sample_sbom(source)

    assert normalized["SPDXID"] == source["SPDXID"]
    assert normalized["spdxVersion"] == source["spdxVersion"]
    assert normalized["dataLicense"] == source["dataLicense"]
    assert normalized["name"] == source["name"]
    assert normalized["creationInfo"]["creators"] == source["creationInfo"]["creators"]
    assert normalized["creationInfo"]["created"] == "2026-07-15T00:00:00Z"
    assert sorted(item["name"] for item in normalized["packages"]) == ["alpha", "beta"]
    assert sorted(item["relatedSpdxElement"] for item in normalized["relationships"]) == [
        "SPDXRef-Package-a",
        "SPDXRef-Package-b",
    ]


def test_sbom_canonical_sort_behavior_is_stable() -> None:
    source = _sample_spdx_sbom(namespace="https://anchore.com/syft/dir/apps/api-random")

    normalized = _normalize_sample_sbom(source)

    assert [package["name"] for package in normalized["packages"]] == ["alpha", "beta"]
    assert [relationship["relatedSpdxElement"] for relationship in normalized["relationships"]] == [
        "SPDXRef-Package-a",
        "SPDXRef-Package-b",
    ]


def test_sbom_non_namespace_drift_still_fails_repeated_comparison() -> None:
    first = _sample_spdx_sbom(
        namespace="https://anchore.com/syft/dir/apps/api-9378a740-f44a-4043-a4a2-8c091ca3e80d",
        package_version="1.0.0",
    )
    second = _sample_spdx_sbom(
        namespace="https://anchore.com/syft/dir/apps/api-13bc5e23-0b20-40aa-833c-b59e00c6df2c",
        package_version="1.0.1",
    )

    normalized_first = _normalize_sample_sbom(first)
    normalized_second = _normalize_sample_sbom(second)

    assert normalized_first != normalized_second
    assert normalized_first["documentNamespace"] == normalized_second["documentNamespace"]


def _release_file_snapshot(root: Path) -> dict[str, bytes]:
    release = root / "releases/sprint-3"
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(release.rglob("*"))
        if path.is_file()
    }


def _patch_release_builder_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    branch: str,
    commit: str = COMMIT,
) -> None:
    monkeypatch.setattr(build_sprint3_release, "git_meta", lambda root: (branch, commit))
    monkeypatch.setattr(
        "scripts.gates.validate_sprint3_evidence.git_meta",
        lambda root: (branch, commit),
    )
    monkeypatch.setattr(
        build_sprint3_release,
        "_generate_openapi",
        lambda root: {"openapi": "3.1.0", "paths": {"/health": {}}},
    )
    monkeypatch.setattr(
        build_sprint3_release,
        "_run_syft",
        lambda root: _sample_spdx_sbom(
            namespace="https://anchore.com/syft/dir/apps/api-random"
        ),
    )

    def fake_check_output(args: list[str], **kwargs: Any) -> str:
        if args == ["syft", "--version"]:
            return "syft 1.18.1\n"
        raise AssertionError(f"unexpected check_output call: {args}")

    monkeypatch.setattr(build_sprint3_release.subprocess, "check_output", fake_check_output)


def test_release_manifest_and_checksums_are_branch_invariant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_valid_evidence(tmp_path)
    _patch_release_builder_dependencies(monkeypatch, branch="fix/sprint3-release")
    build_sprint3_release.build_release(tmp_path)
    feature_snapshot = _release_file_snapshot(tmp_path)

    _patch_release_builder_dependencies(monkeypatch, branch="main")
    build_sprint3_release.build_release(tmp_path)
    main_snapshot = _release_file_snapshot(tmp_path)

    assert main_snapshot == feature_snapshot
    manifest = json.loads(main_snapshot["releases/sprint-3/MANIFEST.json"])
    assert "source_branch" not in manifest
    assert manifest["validated_source_commit"] == COMMIT
    assert manifest["sbom"]["normalized_fields"] == ["creationInfo.created", "documentNamespace"]
    sbom = json.loads(main_snapshot["releases/sprint-3/sbom.spdx.json"])
    assert sbom["documentNamespace"].endswith(f"/{COMMIT}")


def test_release_manifest_and_checksums_are_detached_head_invariant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_valid_evidence(tmp_path)
    _patch_release_builder_dependencies(monkeypatch, branch="fix/sprint3-release")
    build_sprint3_release.build_release(tmp_path)
    branch_snapshot = _release_file_snapshot(tmp_path)

    _patch_release_builder_dependencies(monkeypatch, branch="HEAD")
    build_sprint3_release.build_release(tmp_path)
    detached_snapshot = _release_file_snapshot(tmp_path)

    assert detached_snapshot == branch_snapshot
    assert b"source_branch" not in detached_snapshot["releases/sprint-3/MANIFEST.json"]
    assert b"fix/sprint3-release" not in detached_snapshot["releases/sprint-3/checksums.txt"]
    assert b"HEAD" not in detached_snapshot["releases/sprint-3/checksums.txt"]


def _patch_clean_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate_sprint3, "git_meta", lambda root: ("feature/test", COMMIT))
    monkeypatch.setattr(gate_sprint3, "git_is_dirty", lambda root: False)
    monkeypatch.setattr(gate_sprint3, "_unexpected_dirty_paths", lambda root: [])
    monkeypatch.setattr(
        gate_sprint3,
        "preflight_payload",
        lambda root, git_commit: {
            "evidence_version": EVIDENCE_VERSION,
            "git_commit": git_commit,
            "status": "PASS",
            "checks": {},
            "errors": [],
        },
    )
    monkeypatch.setattr(gate_sprint3, "write_environment", lambda *args, **kwargs: None)
    monkeypatch.setattr(gate_sprint3, "write_git_state", lambda *args, **kwargs: None)


def _runner(
    *,
    fail_id: str | None = None,
    skip_id: str | None = None,
) -> Any:
    def run(spec: CommandSpec, cwd: Path, log_path: Path, git_commit: str) -> CommandResult:
        status = "PASS"
        exit_code = 0
        skip_reason = None
        if spec.id == fail_id:
            status = "FAIL"
            exit_code = 1
        if spec.id == skip_id:
            status = "SKIPPED"
            skip_reason = "disabled in fake runner"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"{spec.id} {status}\n", encoding="utf-8")
        return CommandResult(
            id=spec.id,
            command=" ".join(spec.command),
            started_at="2026-07-14T00:00:00Z",
            completed_at="2026-07-14T00:00:01Z",
            duration_seconds=1.0,
            exit_code=exit_code,
            status=status,  # type: ignore[arg-type]
            required=spec.required,
            log_path=str(log_path.relative_to(cwd)),
            skip_reason=skip_reason,
            timeout_seconds=spec.timeout_seconds,
            evidence_version=EVIDENCE_VERSION,
            git_commit=git_commit,
            sanitized_environment_summary={},
        )

    return run


def test_all_required_pass_returns_go(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_clean_preflight(monkeypatch)
    assert gate_sprint3.run_gate(root=tmp_path, runner=_runner(), phase="prepare") == 0
    summary = json.loads((tmp_path / "artifacts/sprint3/gate-summary.json").read_text())
    assert summary["final_decision"] == gate_sprint3.RELEASE_PACKAGE_READY
    assert summary["overall_status"] == "PASS"


def test_required_failure_returns_no_go(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_clean_preflight(monkeypatch)
    assert gate_sprint3.run_gate(root=tmp_path, runner=_runner(fail_id="lint"), phase="prepare") == 1
    summary = json.loads((tmp_path / "artifacts/sprint3/gate-summary.json").read_text())
    assert summary["final_decision"] == "NO-GO FOR SPRINT 4"
    assert summary["first_failed_stage"] == "lint"


def test_required_skipped_returns_no_go(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_clean_preflight(monkeypatch)
    assert (
        gate_sprint3.run_gate(
            root=tmp_path,
            runner=_runner(skip_id="smoke-api-data-quality"),
            phase="prepare",
        )
        == 1
    )
    summary = json.loads((tmp_path / "artifacts/sprint3/gate-summary.json").read_text())
    assert summary["required_skipped_count"] == 1


def test_optional_skipped_is_allowed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_clean_preflight(monkeypatch)
    assert (
        gate_sprint3.run_gate(
            root=tmp_path,
            runner=_runner(skip_id="smoke-api-polygon"),
            phase="prepare",
        )
        == 0
    )
    summary = json.loads((tmp_path / "artifacts/sprint3/gate-summary.json").read_text())
    assert summary["optional_skipped_count"] == 1


def test_enabled_optional_failure_is_no_go(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_clean_preflight(monkeypatch)
    assert (
        gate_sprint3.run_gate(
            root=tmp_path,
            runner=_runner(fail_id="smoke-api-polygon"),
            phase="prepare",
        )
        == 1
    )
    summary = json.loads((tmp_path / "artifacts/sprint3/gate-summary.json").read_text())
    assert summary["optional_failed_count"] == 1
    assert summary["first_failed_stage"] == "smoke-api-polygon"


def test_preflight_failure_is_no_go(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate_sprint3, "git_meta", lambda root: ("feature/test", COMMIT))
    monkeypatch.setattr(gate_sprint3, "write_environment", lambda *args, **kwargs: None)
    monkeypatch.setattr(gate_sprint3, "write_git_state", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        gate_sprint3,
        "preflight_payload",
        lambda root, git_commit: {
            "evidence_version": EVIDENCE_VERSION,
            "git_commit": git_commit,
            "status": "FAIL",
            "checks": {},
            "errors": ["working tree is dirty"],
        },
    )
    assert gate_sprint3.run_gate(root=tmp_path, runner=_runner()) == 1
    summary = json.loads((tmp_path / "artifacts/sprint3/gate-summary.json").read_text())
    assert summary["first_failed_stage"] == "preflight"


def _valid_command_row(command_id: str, *, log_path: str) -> dict[str, Any]:
    return {
        "id": command_id,
        "command": f"make {command_id}",
        "started_at": "2026-07-14T00:00:00Z",
        "completed_at": "2026-07-14T00:00:01Z",
        "duration_seconds": 1.0,
        "exit_code": 0,
        "status": "PASS",
        "required": True,
        "log_path": log_path,
        "skip_reason": None,
        "timeout_seconds": 60,
        "evidence_version": EVIDENCE_VERSION,
        "git_commit": COMMIT,
        "sanitized_environment_summary": {},
    }


def _write_valid_evidence(root: Path) -> None:
    evidence = root / "artifacts/sprint3/evidence"
    logs = root / "artifacts/sprint3/logs"
    logs.mkdir(parents=True)
    for name in (
        "static-checks",
        "focused-tests",
        "regression",
        "offline-smokes",
        "provider-smokes",
        "release",
    ):
        log = logs / f"{name}.log"
        log.write_text("PASS\n", encoding="utf-8")
        write_json(
            evidence / f"{name}.json",
            {
                "evidence_version": EVIDENCE_VERSION,
                "results": [_valid_command_row(name, log_path=str(log.relative_to(root)))],
            },
        )
    write_json(evidence / "environment.json", {"evidence_version": EVIDENCE_VERSION})
    write_json(
        evidence / "git-state.json",
        {"evidence_version": EVIDENCE_VERSION, "generated_at": "2026-07-14T00:00:00Z"},
    )
    write_json(evidence / "preflight.json", {"evidence_version": EVIDENCE_VERSION, "status": "PASS"})
    runtime_log = logs / "runtime.log"
    runtime_log.write_text("PASS\n", encoding="utf-8")
    write_json(
        evidence / "runtime-smoke.json",
        {
            "evidence_version": EVIDENCE_VERSION,
            "git_commit": COMMIT,
            "final_status": "PASS",
            "kafka_ack_verified": True,
            "snapshot_verified": True,
            "row_verified": True,
            "decimal_verified": True,
            "offset_after_durability_verified": True,
            "operation_timestamps": {
                "kafka_publish_acknowledged_at": "2026-07-14T00:00:00Z",
                "iceberg_append_started_at": "2026-07-14T00:00:01Z",
                "iceberg_snapshot_committed_at": "2026-07-14T00:00:02Z",
                "row_verified_at": "2026-07-14T00:00:03Z",
                "kafka_offset_committed_at": "2026-07-14T00:00:04Z",
            },
            "command_results": [
                _valid_command_row("smoke-sprint3-runtime", log_path=str(runtime_log.relative_to(root)))
            ],
        },
    )


def test_validator_rejects_invalid_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    (tmp_path / "artifacts/sprint3/evidence/static-checks.json").write_text("{", encoding="utf-8")
    validation = validate_evidence(tmp_path)
    assert validation.status == "FAIL"
    assert any("invalid JSON" in reason for reason in validation.reasons)


def test_validator_rejects_missing_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    (tmp_path / "artifacts/sprint3/logs/static-checks.log").unlink()
    validation = validate_evidence(tmp_path)
    assert validation.status == "FAIL"
    assert any("missing/empty required file" in reason for reason in validation.reasons)


def test_validator_rejects_log_path_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    payload = json.loads((tmp_path / "artifacts/sprint3/evidence/static-checks.json").read_text())
    payload["results"][0]["log_path"] = "../outside.log"
    write_json(tmp_path / "artifacts/sprint3/evidence/static-checks.json", payload)
    validation = validate_evidence(tmp_path)
    assert validation.status == "FAIL"
    assert any("unsafe log path" in reason for reason in validation.reasons)


def test_validator_rejects_future_timestamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    payload = json.loads((tmp_path / "artifacts/sprint3/evidence/static-checks.json").read_text())
    payload["results"][0]["started_at"] = "2999-01-01T00:00:00Z"
    write_json(tmp_path / "artifacts/sprint3/evidence/static-checks.json", payload)
    validation = validate_evidence(tmp_path)
    assert validation.status == "FAIL"
    assert any("future timestamp" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    ("key", "reason"),
    [
        ("kafka_ack_verified", "missing Kafka acknowledgement"),
        ("snapshot_verified", "missing Iceberg snapshot verification"),
        ("row_verified", "missing row verification"),
        ("decimal_verified", "missing Decimal verification"),
        ("offset_after_durability_verified", "offset-after-durability invariant missing"),
    ],
)
def test_validator_rejects_runtime_missing_required_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    key: str,
    reason: str,
) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    payload = json.loads((tmp_path / "artifacts/sprint3/evidence/runtime-smoke.json").read_text())
    payload[key] = False
    write_json(tmp_path / "artifacts/sprint3/evidence/runtime-smoke.json", payload)
    validation = validate_evidence(tmp_path)
    assert validation.status == "FAIL"
    assert any(reason in item for item in validation.reasons)


def test_validator_rejects_offset_before_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    payload = json.loads((tmp_path / "artifacts/sprint3/evidence/runtime-smoke.json").read_text())
    payload["operation_timestamps"]["kafka_offset_committed_at"] = "2026-07-14T00:00:01Z"
    write_json(tmp_path / "artifacts/sprint3/evidence/runtime-smoke.json", payload)
    validation = validate_evidence(tmp_path)
    assert validation.status == "FAIL"
    assert any("before Iceberg snapshot durability" in reason for reason in validation.reasons)


def test_validator_rejects_secret_leak(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    (tmp_path / "artifacts/sprint3/logs/static-checks.log").write_text(
        "Authorization: Bearer abc123\n",
        encoding="utf-8",
    )
    validation = validate_evidence(tmp_path)
    assert validation.status == "FAIL"
    assert any("secret-like material" in reason for reason in validation.reasons)


def test_validator_rejects_release_checksum_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    release = tmp_path / "releases/sprint-3"
    release.mkdir(parents=True)
    for name in (
        "README.md",
        "RELEASE_NOTES.md",
        "sprint3-runtime-validation.json",
        "sprint3-openapi.json",
        "sprint3-quality-gate.json",
        "sprint3-known-limitations.md",
    ):
        content = "{}\n" if name.endswith(".json") else "ok\n"
        (release / name).write_text(content, encoding="utf-8")
    write_json(release / "sbom.spdx.json", {"SPDXID": "SPDXRef-DOCUMENT", "packages": []})
    write_json(
        release / "MANIFEST.json",
        {
            "release_version": "v0.3.0-sprint3",
            "validated_commit": COMMIT,
            "gate_decision": GO_DECISION,
            "sbom": {"format": "spdx-json"},
            "files": {},
        },
    )
    write_checksums(tmp_path, release)
    (release / "README.md").write_text("drift\n", encoding="utf-8")
    validation = validate_evidence(tmp_path, validate_release=True)
    assert validation.status == "FAIL"
    assert any("checksum" in reason for reason in validation.reasons)


def test_validator_rejects_missing_sbom(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    release = tmp_path / "releases/sprint-3"
    release.mkdir(parents=True)
    write_json(release / "MANIFEST.json", {})
    write_checksums(tmp_path, release)
    validation = validate_evidence(tmp_path, validate_release=True)
    assert validation.status == "FAIL"
    assert any("sbom.spdx.json" in reason for reason in validation.reasons)


def test_final_context_allows_release_only_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_commit = COMMIT
    release_commit = "508240dcaad8ca81d7351bfa3671a161f1061505"
    release = tmp_path / "releases/sprint-3"
    release.mkdir(parents=True)
    write_json(release / "MANIFEST.json", {"validated_source_commit": source_commit})
    monkeypatch.setattr(gate_sprint3, "_git_success", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        gate_sprint3,
        "_changed_paths_between",
        lambda *args, **kwargs: ["releases/sprint-3/MANIFEST.json"],
    )

    validated_source, errors, release_paths = gate_sprint3._final_context(
        tmp_path, head_commit=release_commit
    )

    assert validated_source == source_commit
    assert errors == []
    assert release_paths == ["releases/sprint-3/MANIFEST.json"]


def test_final_context_rejects_product_change_between_source_and_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_commit = COMMIT
    release_commit = "508240dcaad8ca81d7351bfa3671a161f1061505"
    release = tmp_path / "releases/sprint-3"
    release.mkdir(parents=True)
    write_json(release / "MANIFEST.json", {"validated_source_commit": source_commit})
    monkeypatch.setattr(gate_sprint3, "_git_success", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        gate_sprint3,
        "_changed_paths_between",
        lambda *args, **kwargs: [
            "apps/api/pyproject.toml",
            "releases/sprint-3/MANIFEST.json",
        ],
    )

    _, errors, _ = gate_sprint3._final_context(tmp_path, head_commit=release_commit)

    assert any("non-release changes" in error for error in errors)


def test_release_attestation_records_observed_branch_outside_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release = tmp_path / "releases/sprint-3"
    release.mkdir(parents=True)
    write_json(release / "MANIFEST.json", {"validated_source_commit": COMMIT})
    monkeypatch.setattr(
        gate_sprint3.subprocess,
        "check_output",
        lambda *args, **kwargs: "608240dcaad8ca81d7351bfa3671a161f1061506\n",
    )

    gate_sprint3._write_release_attestation(
        tmp_path,
        validated_source_commit=COMMIT,
        release_commit="508240dcaad8ca81d7351bfa3671a161f1061505",
        observed_branch="fix/sprint3-release",
        release_paths=["releases/sprint-3/MANIFEST.json"],
    )

    manifest = json.loads((release / "MANIFEST.json").read_text())
    attestation = json.loads(
        (tmp_path / "artifacts/sprint3/evidence/release-attestation.json").read_text()
    )
    assert "source_branch" not in manifest
    assert "observed_branch" not in manifest
    assert attestation["observed_branch"] == "fix/sprint3-release"
    assert attestation["release_commit"] == "508240dcaad8ca81d7351bfa3671a161f1061505"


def test_prepare_preflight_allows_only_release_dirty_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release = tmp_path / "releases/sprint-3"
    release.mkdir(parents=True)
    (release / "README.md").write_text("generated\n", encoding="utf-8")
    monkeypatch.setattr(gate_sprint3, "_git_status_paths", lambda root: ["releases/sprint-3/README.md"])
    monkeypatch.setattr(
        gate_sprint3,
        "preflight_payload",
        lambda root, git_commit: {
            "evidence_version": EVIDENCE_VERSION,
            "git_commit": git_commit,
            "status": "FAIL",
            "checks": {"working_tree_clean": False},
            "errors": ["working tree is dirty"],
        },
    )

    payload = gate_sprint3._prepare_preflight(tmp_path, git_commit=COMMIT)

    assert payload["status"] == "PASS"
    assert payload["checks"]["release_dirty_paths_allowed"] == ["releases/sprint-3/README.md"]


def test_prepare_preflight_rejects_non_release_dirty_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gate_sprint3, "_git_status_paths", lambda root: ["apps/api/pyproject.toml"])
    monkeypatch.setattr(
        gate_sprint3,
        "preflight_payload",
        lambda root, git_commit: {
            "evidence_version": EVIDENCE_VERSION,
            "git_commit": git_commit,
            "status": "FAIL",
            "checks": {"working_tree_clean": False},
            "errors": ["working tree is dirty"],
        },
    )

    payload = gate_sprint3._prepare_preflight(tmp_path, git_commit=COMMIT)

    assert payload["status"] == "FAIL"


def test_tracked_manifest_rejects_release_commit_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    release = tmp_path / "releases/sprint-3"
    release.mkdir(parents=True)
    for name in (
        "README.md",
        "RELEASE_NOTES.md",
        "sprint3-runtime-validation.json",
        "sprint3-openapi.json",
        "sprint3-quality-gate.json",
        "sprint3-known-limitations.md",
    ):
        (release / name).write_text("{}\n" if name.endswith(".json") else "ok\n", encoding="utf-8")
    write_json(release / "sbom.spdx.json", {"SPDXID": "SPDXRef-DOCUMENT", "packages": []})
    write_json(
        release / "MANIFEST.json",
        {
            "release_version": "v0.3.0-sprint3",
            "validated_source_commit": COMMIT,
            "release_commit": COMMIT,
            "gate_decision": GO_DECISION,
            "approved_release_paths": sorted(gate_sprint3.APPROVED_SPRINT3_RELEASE_PATHS),
            "sbom": {"format": "spdx-json"},
            "files": {},
        },
    )
    write_checksums(tmp_path, release)

    validation = validate_evidence(tmp_path, validate_release=True)

    assert validation.status == "FAIL"
    assert any("must not contain release_commit" in reason for reason in validation.reasons)


def test_tracked_manifest_rejects_source_branch_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.gates.validate_sprint3_evidence.git_meta", lambda root: ("x", COMMIT))
    _write_valid_evidence(tmp_path)
    release = tmp_path / "releases/sprint-3"
    release.mkdir(parents=True)
    for name in (
        "README.md",
        "RELEASE_NOTES.md",
        "sprint3-runtime-validation.json",
        "sprint3-openapi.json",
        "sprint3-quality-gate.json",
        "sprint3-known-limitations.md",
    ):
        (release / name).write_text("{}\n" if name.endswith(".json") else "ok\n", encoding="utf-8")
    write_json(release / "sbom.spdx.json", {"SPDXID": "SPDXRef-DOCUMENT", "packages": []})
    write_json(
        release / "MANIFEST.json",
        {
            "release_version": "v0.3.0-sprint3",
            "validated_source_commit": COMMIT,
            "source_branch": "feature/non-deterministic",
            "gate_decision": GO_DECISION,
            "approved_release_paths": sorted(gate_sprint3.APPROVED_SPRINT3_RELEASE_PATHS),
            "sbom": {"format": "spdx-json"},
            "files": {},
        },
    )
    write_checksums(tmp_path, release)

    validation = validate_evidence(tmp_path, validate_release=True)

    assert validation.status == "FAIL"
    assert any("must not contain source_branch" in reason for reason in validation.reasons)
