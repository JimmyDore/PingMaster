import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app, docs_settings

BACKEND_DIR = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("environment", ["prod", "production", "PROD", " Production "])
def test_docs_disabled_in_production_environments(environment):
    assert docs_settings(environment) == {"docs_url": None, "redoc_url": None, "openapi_url": None}


@pytest.mark.parametrize("environment", [None, "", "development", "staging", "test"])
def test_docs_enabled_outside_production(environment):
    assert docs_settings(environment) == {}


def test_docs_served_in_test_environment():
    client = TestClient(app)
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_docs_not_served_when_environment_is_prod():
    script = (
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "c = TestClient(app)\n"
        "print(c.get('/docs').status_code, c.get('/redoc').status_code, c.get('/openapi.json').status_code)\n"
    )
    env = dict(os.environ, ENVIRONMENT="prod")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["404", "404", "404"]
