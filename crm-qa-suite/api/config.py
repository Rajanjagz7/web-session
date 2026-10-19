"""Environment-specific configuration. Values come from real environment
variables first, then .env / .env.<CRM_ENV> files. Secrets are never logged."""
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(ROOT / ".env")
if os.environ.get("CRM_ENV"):
    _load_env_file(ROOT / f".env.{os.environ['CRM_ENV']}")


@dataclass(frozen=True)
class Config:
    base_url: str
    project_id: str
    org_id: str
    env_mode: str
    email: str
    password: str

    @property
    def api(self) -> str:
        return f"{self.base_url}/api/crm/v1"

    def __repr__(self) -> str:  # never leak the password
        return f"Config(base_url={self.base_url!r}, project_id={self.project_id!r}, email={self.email!r})"


def load() -> Config:
    missing = [k for k in ("CRM_BASE_URL", "CRM_PROJECT_ID", "CRM_EMAIL", "CRM_PASSWORD") if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)} (see .env.example)")
    return Config(
        base_url=os.environ["CRM_BASE_URL"].rstrip("/"),
        project_id=os.environ["CRM_PROJECT_ID"],
        org_id=os.environ.get("CRM_ORG_ID", "default"),
        env_mode=os.environ.get("CRM_ENV_MODE", "live"),
        email=os.environ["CRM_EMAIL"],
        password=os.environ["CRM_PASSWORD"],
    )
