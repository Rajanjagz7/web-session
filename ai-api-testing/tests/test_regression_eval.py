"""Regression / eval pipeline: run a fixed dataset against the API and check
each case still satisfies its expected property. Run this after every prompt
or model change to catch silent quality regressions.

Each row generates its own parametrized test, so CI shows exactly which
cases broke rather than one aggregate pass/fail.
"""

import json
from pathlib import Path

import pytest

DATASET_PATH = Path(__file__).parent.parent / "datasets" / "eval_dataset.jsonl"


def load_dataset():
    rows = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


CASES = load_dataset()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_eval_case(client, model, case):
    resp = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": case["prompt"]}],
    )
    text = resp.content[0].text.lower()

    matched = any(expected in text for expected in case["expect_contains_any"])
    assert matched, (
        f"none of {case['expect_contains_any']} found in response: {text!r}"
    )
