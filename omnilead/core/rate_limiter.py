"""
Async Token-Bucket Rate Limiter
================================
Prevents bans from scraped sites and respects external API quotas.
Wraps asyncio.Semaphore for concurrency bounding and a simple
time-based token bucket for per-second rate limiting.
"""
from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from omnilead.config import settings


class RateLimiter:
    """
    Composite async rate limiter:
      - Semaphore: bounds simultaneous coroutines.
      - Token bucket: enforces max requests per second.
    """

    def __init__(self, concurrency: int, rps: float) -> None:
        self._semaphore = asyncio.Semaphore(concurrency)
        self._rps = rps
        self._min_interval = 1.0 / rps
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Context manager to acquire both a semaphore slot and a rate token."""
        async with self._semaphore:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_request_time
                sleep_for = self._min_interval - elapsed
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)
                self._last_request_time = time.monotonic()
            yield


# Global singleton shared across all pipeline coroutines
_global_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter(
            concurrency=settings.concurrency_limit,
            rps=settings.rate_limit_rps,
        )
    return _global_limiter


def reset_rate_limiter() -> None:
    """Force a fresh limiter (useful in tests)."""
    global _global_limiter
    _global_limiter = None
