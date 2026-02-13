"""Load test: 50 concurrent SSE connections to demo stream endpoint.

D7 quality gate: Measures p50, p95, p99 latency for time-to-first-byte
and total connection duration under concurrent load.
"""

from __future__ import annotations

import asyncio
import statistics
import time

import httpx
import pytest

BASE_URL = "http://localhost:8000"
SCENARIO_ID = "fracoes-tea-tdah"
CONCURRENT = 50
TIMEOUT = 30.0


def _check_server_available() -> bool:
    """Check if the API server is reachable."""
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


async def _connect_sse(client: httpx.AsyncClient, idx: int) -> dict:
    """Open one SSE connection and measure timings."""
    t0 = time.monotonic()
    ttfb = 0.0
    events = 0
    error: str | None = None

    try:
        async with client.stream(
            "POST",
            f"{BASE_URL}/demo/scenarios/{SCENARIO_ID}/stream",
            timeout=TIMEOUT,
        ) as resp:
            ttfb = time.monotonic() - t0
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    events += 1
    except httpx.ReadTimeout:
        error = "timeout"
    except httpx.ConnectError as e:
        error = f"connect_error: {e}"
    except Exception as e:
        error = f"error: {type(e).__name__}: {e}"

    total = time.monotonic() - t0
    return {
        "idx": idx,
        "ttfb": ttfb,
        "total": total,
        "events": events,
        "error": error,
    }


@pytest.mark.skipif(
    not _check_server_available(),
    reason="API server not running on localhost:8000",
)
@pytest.mark.timeout(120)
async def test_sse_load_50_concurrent() -> None:
    """50 concurrent SSE connections should complete within acceptable latency."""
    async with httpx.AsyncClient() as client:
        tasks = [_connect_sse(client, i) for i in range(CONCURRENT)]
        results = await asyncio.gather(*tasks)

    errors = [r for r in results if r["error"]]
    successes = [r for r in results if not r["error"]]

    # Metrics
    ttfbs = [r["ttfb"] for r in successes]
    totals = [r["total"] for r in successes]

    print(f"\n{'='*60}")
    print(f"SSE Load Test: {CONCURRENT} concurrent connections")
    print(f"{'='*60}")
    print(f"Successes: {len(successes)}/{CONCURRENT}")
    print(f"Errors:    {len(errors)}")
    if errors:
        for e in errors[:5]:
            print(f"  - Connection {e['idx']}: {e['error']}")

    if ttfbs:
        print("\nTime-to-First-Byte (TTFB):")
        print(f"  p50:  {statistics.median(ttfbs):.3f}s")
        print(f"  p95:  {sorted(ttfbs)[int(len(ttfbs) * 0.95)]:.3f}s")
        print(f"  p99:  {sorted(ttfbs)[int(len(ttfbs) * 0.99)]:.3f}s")
        print(f"  max:  {max(ttfbs):.3f}s")

    if totals:
        print("\nTotal Connection Duration:")
        print(f"  p50:  {statistics.median(totals):.3f}s")
        print(f"  p95:  {sorted(totals)[int(len(totals) * 0.95)]:.3f}s")
        print(f"  p99:  {sorted(totals)[int(len(totals) * 0.99)]:.3f}s")
        print(f"  max:  {max(totals):.3f}s")

    total_events = sum(r["events"] for r in successes)
    print(f"\nTotal SSE events received: {total_events}")
    print(f"Avg events per connection: {total_events / max(len(successes), 1):.1f}")
    print(f"{'='*60}")

    # Assertions
    assert len(successes) >= CONCURRENT * 0.9, (
        f"Too many failures: {len(errors)}/{CONCURRENT}"
    )
    if ttfbs:
        p95_ttfb = sorted(ttfbs)[int(len(ttfbs) * 0.95)]
        assert p95_ttfb < 5.0, f"p95 TTFB too high: {p95_ttfb:.3f}s"
