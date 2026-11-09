"""
Tests: Rate Limiter
"""
import asyncio
import time
import pytest
from omnilead.core.rate_limiter import RateLimiter, reset_rate_limiter


@pytest.fixture(autouse=True)
def fresh_limiter():
    reset_rate_limiter()
    yield
    reset_rate_limiter()


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests():
    limiter = RateLimiter(concurrency=5, rps=10.0)
    async with limiter.acquire():
        pass  # Should not raise or block for long


@pytest.mark.asyncio
async def test_rate_limiter_concurrency_bound():
    """Verify that concurrent tasks are bounded by the semaphore."""
    limiter = RateLimiter(concurrency=3, rps=100.0)
    active = 0
    max_active = 0

    async def task():
        nonlocal active, max_active
        async with limiter.acquire():
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.05)
            active -= 1

    await asyncio.gather(*[task() for _ in range(10)])
    assert max_active <= 3


@pytest.mark.asyncio
async def test_rate_limiter_enforces_rps():
    """Verify that 3 sequential requests at 2.0 RPS take at least 1 second."""
    limiter = RateLimiter(concurrency=1, rps=2.0)
    start = time.monotonic()
    for _ in range(3):
        async with limiter.acquire():
            pass
    elapsed = time.monotonic() - start
    # 3 requests at 2 RPS = at least 1.0s delay total
    assert elapsed >= 0.9, f"Expected >= 0.9s but got {elapsed:.2f}s"
