import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.management import call_command

BACKEND = Path(__file__).resolve().parent.parent


def _load(module: str, **env: str) -> subprocess.CompletedProcess[str]:
    clean = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    clean.pop("DATABASE_URL", None)
    clean.update(env)
    code = (
        f"import importlib; m = importlib.import_module('config.settings.{module}');"
        "print(m.DEBUG, m.ALLOWED_HOSTS)"
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )


HOSTED = {
    "DJANGO_SECRET_KEY": "x" * 50,
    "DJANGO_ALLOWED_HOSTS": "api.example.test",
    "DATABASE_URL": "postgres://u:p@h/db",
}


@pytest.mark.parametrize("module", ["dev", "staging", "production"])
def test_hosted_settings_load_with_debug_off(module: str) -> None:
    result = _load(module, **HOSTED)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False ['api.example.test']"


@pytest.mark.parametrize("module", ["dev", "staging", "production"])
@pytest.mark.parametrize("missing", list(HOSTED))
def test_hosted_settings_fail_at_startup_when_a_key_is_missing(
    module: str, missing: str
) -> None:
    env = {k: v for k, v in HOSTED.items() if k != missing}
    result = _load(module, **env)
    assert result.returncode != 0
    assert missing in result.stderr


@pytest.mark.parametrize("module", ["local", "test"])
def test_local_and_test_settings_default_safely(module: str) -> None:
    result = _load(module)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("module", ["dev", "staging", "production"])
@pytest.mark.parametrize("key", list(HOSTED))
@pytest.mark.parametrize("blank", ["", " ", "  \t"])
def test_hosted_settings_fail_when_a_key_is_blank(
    module: str, key: str, blank: str
) -> None:
    result = _load(module, **{**HOSTED, key: blank})
    assert result.returncode != 0
    assert key in result.stderr


@pytest.mark.parametrize("hosts", [",", " , ,"])
def test_hosted_settings_fail_when_no_host_is_left_after_cleaning(hosts: str) -> None:
    result = _load("dev", **{**HOSTED, "DJANGO_ALLOWED_HOSTS": hosts})
    assert result.returncode != 0
    assert "DJANGO_ALLOWED_HOSTS" in result.stderr


def test_allowed_hosts_are_stripped_and_empties_dropped() -> None:
    result = _load("dev", **{**HOSTED, "DJANGO_ALLOWED_HOSTS": "a, b ,,"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False ['a', 'b']"


def test_local_allowed_hosts_are_stripped() -> None:
    result = _load("local", DJANGO_ALLOWED_HOSTS=" a , b ,,")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True ['a', 'b']"


def test_local_settings_fall_back_when_values_are_empty() -> None:
    result = _load(
        "local",
        DJANGO_SECRET_KEY="",
        DJANGO_ALLOWED_HOSTS="",
        DATABASE_URL="",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True ['localhost', '127.0.0.1']"


@pytest.mark.parametrize("entry", ["wsgi", "asgi"])
@pytest.mark.parametrize("value", [None, ""])
def test_entry_points_refuse_a_missing_settings_module(
    entry: str, value: str | None
) -> None:
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    if value is not None:
        env["DJANGO_SETTINGS_MODULE"] = value
    result = subprocess.run(
        [sys.executable, "-c", f"import config.{entry}"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "DJANGO_SETTINGS_MODULE" in result.stderr


@pytest.mark.parametrize("hosts", [",", " , ", " , ,"])
def test_local_settings_fall_back_when_hosts_split_to_nothing(hosts: str) -> None:
    result = _load("local", DJANGO_ALLOWED_HOSTS=hosts)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True ['localhost', '127.0.0.1']"


@pytest.mark.parametrize("hosts", [",", " , "])
def test_local_server_answers_health_on_localhost_with_a_blank_host_list(
    hosts: str,
) -> None:
    code = (
        "import django; django.setup();"
        "from django.test import Client;"
        "print(Client(HTTP_HOST='localhost').get('/api/v1/health').status_code)"
    )
    clean = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    clean.update(
        DJANGO_SETTINGS_MODULE="config.settings.local", DJANGO_ALLOWED_HOSTS=hosts
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] in {"200", "503"}


def test_static_root_is_git_ignored_inside_the_backend(settings) -> None:
    assert Path(settings.STATIC_ROOT) == BACKEND / "staticfiles"
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(Path(settings.STATIC_ROOT) / "x")],
        cwd=BACKEND,
        check=False,
    )
    assert ignored.returncode == 0


def test_collectstatic_writes_the_swagger_assets(settings, tmp_path: Path) -> None:
    settings.STATIC_ROOT = tmp_path
    call_command("collectstatic", interactive=False, verbosity=0)
    assert list(tmp_path.glob("ninja/swagger-ui*"))
