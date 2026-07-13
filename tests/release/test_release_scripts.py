import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_build_release_script_syntax():
    subprocess.check_call(["bash", "-n", str(ROOT / "scripts/build-release.sh")])


def test_gate_script_syntax():
    subprocess.check_call(["bash", "-n", str(ROOT / "scripts/gates/gate-sprint1.sh")])
