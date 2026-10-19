import os

import pytest
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


@pytest.fixture(scope="session")
def model():
    return MODEL


@pytest.fixture(scope="session")
def client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set — copy .env.example to .env and add your key")
    from anthropic import Anthropic

    return Anthropic()
