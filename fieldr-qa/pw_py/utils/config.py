"""Environment config, loaded from .env (never hard-code credentials in test files)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BASE_URL = os.environ.get("FLDR_BASE_URL", "https://rajanjagz7.dev.fieldr.app").rstrip("/")
EMAIL = os.environ.get("FLDR_EMAIL", "")
MOBILE = os.environ.get("FLDR_MOBILE", "")
OTP = os.environ.get("FLDR_OTP", "")
AUTH_STATE_PATH = ROOT / ".auth" / "state.json"
