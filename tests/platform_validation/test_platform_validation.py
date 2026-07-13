import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_platform_validate_script_syntax():
    subprocess.check_call(["bash", "-n", str(ROOT / "scripts/platform-validate.sh")])


def test_platform_validate_fails_without_cluster():
    """Fail-closed: with an unreachable kubeconfig the command must be non-zero."""
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env["KUBECONFIG"] = str(ROOT / "tests/fixtures/unreachable-kubeconfig.yaml")
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts/platform-validate.sh")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode != 0
    report = ROOT / "reports/platform-validation.json"
    assert report.is_file()
    import json

    data = json.loads(report.read_text())
    assert data["status"] == "fail"
