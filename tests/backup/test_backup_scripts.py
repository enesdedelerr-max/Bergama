import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_backup_layout_exists():
    for name in ["postgres", "redis", "clickhouse", "minio"]:
        assert (ROOT / "backup" / name).is_dir()
    assert (ROOT / "backup/README.md").is_file()


def test_backup_scripts_syntax():
    subprocess.check_call(["bash", "-n", str(ROOT / "scripts/backup.sh")])
    subprocess.check_call(["bash", "-n", str(ROOT / "scripts/restore-smoke.sh")])
