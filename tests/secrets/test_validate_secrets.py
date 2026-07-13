import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_secret_templates_and_policies_exist():
    assert (ROOT / "infra/secrets/templates/local-secret.yaml").is_file()
    assert (ROOT / "infra/secrets/templates/external-secret.yaml").is_file()
    assert (ROOT / "infra/secrets/policies/naming.md").is_file()
    assert (ROOT / "infra/secrets/policies/rotation.md").is_file()


def test_templates_have_no_default_passwords():
    for path in (ROOT / "infra/secrets/templates").glob("*.yaml"):
        text = path.read_text().lower()
        assert "password: admin" not in text
        assert "password: changeme" not in text
        assert "secretref" in text or "remoteref" in text


def test_validate_secrets_script_syntax():
    subprocess.check_call(["bash", "-n", str(ROOT / "infra/secrets/scripts/validate-secrets.sh")])
