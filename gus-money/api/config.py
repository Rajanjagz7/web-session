"""Environment-specific config. Secrets come only from environment variables / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.getenv("ADMIN_BASE_URL", "https://gusdev.softwareco.com").rstrip("/")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
TIMEOUT = float(os.getenv("API_TIMEOUT", "30"))
