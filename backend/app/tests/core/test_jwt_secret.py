import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core import auth
from app.core.auth import MIN_SECRET_KEY_LENGTH, load_secret_key

BACKEND_DIR = Path(__file__).resolve().parents[3]


def test_secret_key_comes_from_environment():
    assert auth.SECRET_KEY == os.environ["JWT_SECRET_KEY"]
    assert auth.SECRET_KEY != "your-secret-key-here"


def test_load_secret_key_returns_env_value(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * MIN_SECRET_KEY_LENGTH)
    assert load_secret_key() == "x" * MIN_SECRET_KEY_LENGTH


def test_load_secret_key_rejects_missing(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        load_secret_key()


def test_load_secret_key_rejects_empty(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        load_secret_key()


def test_load_secret_key_rejects_short(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * (MIN_SECRET_KEY_LENGTH - 1))
    with pytest.raises(RuntimeError, match="at least 32"):
        load_secret_key()


def _import_auth_in_subprocess(env_overrides: dict) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "JWT_SECRET_KEY"}
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import app.core.auth"],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=60,
    )


def test_app_refuses_to_import_without_secret():
    result = _import_auth_in_subprocess({})
    assert result.returncode != 0
    assert "JWT_SECRET_KEY" in result.stderr


def test_app_imports_with_valid_secret():
    result = _import_auth_in_subprocess({"JWT_SECRET_KEY": "s" * 64})
    assert result.returncode == 0, result.stderr
