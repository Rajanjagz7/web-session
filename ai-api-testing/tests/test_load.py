"""Load / performance: concurrency and latency under repeated calls.

Marked 'load' and excluded by default (see pytest.ini) since it burns real
API calls. Run explicitly with: pytest -m load
"""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

CONCURRENCY = 5
PROMPT = "Reply with just the word: ok"


@pytest.mark.load
def test_concurrent_requests_all_succeed_within_budget(client, model):
    def call(_):
        start = time.perf_counter()
        resp = client.messages.create(
            model=model,
            max_tokens=8,
            messages=[{"role": "user", "content": PROMPT}],
        )
        elapsed = time.perf_counter() - start
        return resp, elapsed

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        results = list(pool.map(call, range(CONCURRENCY)))

    latencies = sorted(elapsed for _, elapsed in results)
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]

    print(f"\nlatency p50={p50:.2f}s p95={p95:.2f}s over {CONCURRENCY} concurrent calls")

    for resp, _ in results:
        assert resp.content
    assert p95 < 10.0, f"p95 latency {p95:.2f}s exceeded 10s budget"


@pytest.mark.load
def test_rate_limit_retry_behavior(client, model):
    """Fires a burst beyond typical low-tier RPM to confirm the SDK's
    built-in retry/backoff handles 429s instead of raising."""
    def call(_):
        return client.messages.create(
            model=model,
            max_tokens=8,
            messages=[{"role": "user", "content": PROMPT}],
        )

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(call, range(20)))

    assert all(r.content for r in results)
