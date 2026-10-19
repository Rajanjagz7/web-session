import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env.nsw-jobs")

BASE_URL = os.environ.get("NSW_BASE_URL", "https://nswdev.rebatem8.com.au")
EMAIL = os.environ["NSW_LOGIN_EMAIL"]
PASSWORD = os.environ["NSW_LOGIN_PASSWORD"]
INSTALLER_COMPANY = os.environ.get("NSW_INSTALLER_COMPANY", "Rajan Testing Company")
