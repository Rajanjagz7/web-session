# AI API Testing Starter (Claude / Anthropic)

A pytest-based scaffold covering four testing angles against the live
Anthropic Messages API: functional correctness, security/injection
resistance, regression/eval, and load/concurrency.

## Setup

```powershell
pip install -r requirements.txt
copy .env.example .env
# edit .env and paste your ANTHROPIC_API_KEY
```

Get a key at https://console.anthropic.com/settings/keys.

## Running tests

```powershell
# functional + security + regression (default — load tests excluded, they cost more)
pytest

# a single file
pytest tests/test_functional.py

# load/concurrency tests (opt-in, makes ~25 API calls)
pytest -m load

# everything
pytest -m "" 
```

If `ANTHROPIC_API_KEY` isn't set, tests skip with a clear message instead of
failing.

## Layout

- `conftest.py` — shared `client` and `model` fixtures. Model defaults to
  `claude-haiku-4-5-20251001` (cheap/fast) via `ANTHROPIC_MODEL` in `.env`.
- `tests/test_functional.py` — response shape, tool-use schema validation,
  basic content assertions.
- `tests/test_security_injection.py` — prompt injection via user content and
  via simulated tool-result content; checks a system-prompt secret can't be
  exfiltrated.
- `tests/test_load.py` — concurrency + latency budget (p50/p95), rate-limit
  retry behavior. Marked `load`, excluded from default runs.
- `tests/test_regression_eval.py` — data-driven eval loop; each row in
  `datasets/eval_dataset.jsonl` becomes its own parametrized test so CI shows
  exactly which cases regressed.
- `datasets/eval_dataset.jsonl` — the eval set. Add rows as
  `{"id": "...", "prompt": "...", "expect_contains_any": ["..."]}`.

## Extending

- **New eval case**: append a line to `eval_dataset.jsonl`. No code changes
  needed.
- **LLM-as-judge assertions**: for cases too fuzzy for substring matching,
  add a helper that makes a second Claude call to grade the first response
  against a rubric (0/1 or a score), and assert on that.
- **CI**: wire `pytest` (default marker set) into your pipeline on every
  prompt/system-prompt change; keep `-m load` as a manual or nightly job
  since it costs more and is latency-sensitive to network conditions.
