import os
import subprocess
import sys
from pathlib import Path


def test_missing_configuration_fails_clearly_without_exposing_values():
    environment = os.environ.copy()
    environment["PYTHON_DOTENV_DISABLED"] = "true"
    for name in (
        "PORTAL_BASE_URL",
        "PORTAL_USERNAME",
        "PORTAL_PASSWORD",
    ):
        environment.pop(name, None)

    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c", "import app.config"],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Missing required configuration" in result.stderr
    assert "PORTAL_BASE_URL" in result.stderr
    assert "PORTAL_USERNAME" in result.stderr
    assert "PORTAL_PASSWORD" in result.stderr
