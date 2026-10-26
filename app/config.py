import os

from dotenv import load_dotenv

load_dotenv()

_REQUIRED_ENV_VARS = (
    "PORTAL_BASE_URL",
    "PORTAL_USERNAME",
    "PORTAL_PASSWORD",
)
_missing_vars = [
    name for name in _REQUIRED_ENV_VARS if not os.getenv(name)
]

if _missing_vars:
    raise RuntimeError(
        "Missing required configuration environment variable(s): "
        + ", ".join(_missing_vars)
    )

PORTAL_BASE_URL = os.environ["PORTAL_BASE_URL"]
PORTAL_USERNAME = os.environ["PORTAL_USERNAME"]
PORTAL_PASSWORD = os.environ["PORTAL_PASSWORD"]