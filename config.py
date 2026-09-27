"""
config.py
----------
Central configuration for the Regional Insight Collector application.

All values that vary between environments (secrets, API keys, feature
flags) are read from environment variables / a local .env file. Nothing
sensitive is ever hardcoded here.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file if one exists. In production the
# real environment variables (set by the OS / hosting platform) take
# precedence automatically because load_dotenv() will not overwrite
# variables that are already set.
load_dotenv()


class Config:
    """Application-wide configuration."""

    # --- Flask core -------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
    PORT = int(os.environ.get("FLASK_PORT", "5000"))

    # --- Paths --------------------------------------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    DATABASE_PATH = os.path.join(DATABASE_DIR, "visitors.db")

    DATA_DIR = os.path.join(BASE_DIR, "data")
    CSV_PATH = os.path.join(DATA_DIR, "visitors.csv")

    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    LOG_FILE = os.path.join(LOGS_DIR, "application.log")

    IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")

    # --- Geolocation ----------------------------------------------------
    # ip-api.com's free JSON endpoint is used by default because it
    # requires no API key for light, non-commercial use. If you have a
    # key for a provider such as ipinfo.io or ipgeolocation.io, set
    # GEOLOCATION_API_KEY and GEOLOCATION_PROVIDER accordingly and adapt
    # geolocation.py.
    GEOLOCATION_PROVIDER = os.environ.get("GEOLOCATION_PROVIDER", "ip-api")
    GEOLOCATION_API_KEY = os.environ.get("GEOLOCATION_API_KEY", "")
    GEOLOCATION_API_URL = os.environ.get(
        "GEOLOCATION_API_URL", "http://ip-api.com/json/"
    )
    GEOLOCATION_TIMEOUT_SECONDS = float(
        os.environ.get("GEOLOCATION_TIMEOUT_SECONDS", "4")
    )

    # --- Reverse proxy trust -----------------------------------------
    # Only trust X-Forwarded-For / X-Real-IP headers when the app is
    # actually deployed behind a known, trusted reverse proxy (nginx,
    # a load balancer, etc). Leave this False for local development so
    # that arbitrary client-supplied headers can never be used to spoof
    # an IP address.
    TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "False").lower() in (
        "1",
        "true",
        "yes",
    )
    # Number of trusted proxies sitting in front of the app. Passed to
    # werkzeug's ProxyFix so only that many hops of X-Forwarded-For are
    # honoured.
    TRUSTED_PROXY_COUNT = int(os.environ.get("TRUSTED_PROXY_COUNT", "1"))

    # --- Input validation ------------------------------------------------
    MAX_NAME_LENGTH = 60
    MIN_NAME_LENGTH = 1

    # --- Development / Testing -------------------------------------------
    # Set to True to use mock geolocation data for localhost testing.
    # This allows testing the full flow without a public IP address.
    # NEVER use in production.
    DEV_MODE_MOCK_GEOLOCATION = os.environ.get(
        "DEV_MODE_MOCK_GEOLOCATION", "False"
    ).lower() in ("1", "true", "yes")

    # --- Admin Panel ---------------------------------------------------
    # Simple password protection for the /admin endpoint.
    # Change this to a strong password in production.
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin-password-123")


def ensure_directories():
    """Create all runtime directories the app needs if they don't exist."""
    for path in (
        Config.DATABASE_DIR,
        Config.DATA_DIR,
        Config.LOGS_DIR,
        Config.IMAGES_DIR,
    ):
        os.makedirs(path, exist_ok=True)
