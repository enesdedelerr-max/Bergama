import json
import pathlib
import subprocess
import os

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_lock_files_exist():
    for rel in [
        "infra/locks/component-matrix.yaml",
        "infra/locks/helm-versions.yaml",
        "infra/locks/images.lock",
        "infra/locks/python.lock",
        "infra/locks/node.lock",
    ]:
        assert (ROOT / rel).is_file()


def test_images_lock_has_no_mutable_tags_and_digests_are_sha256_or_unresolved():
    data = json.loads((ROOT / "infra/locks/images.lock").read_text())
    forbidden = set(data.get("forbidden_tags", []))
    for name, meta in data["images"].items():
        assert meta["tag"] not in forbidden
        digest = meta.get("digest")
        if digest is not None:
            assert str(digest).startswith("sha256:")
            assert meta.get("digest_status") == "resolved"


def test_verify_locks_script_is_executable_syntax():
    script = ROOT / "infra/locks/scripts/verify-locks.sh"
    subprocess.check_call(["bash", "-n", str(script)])
