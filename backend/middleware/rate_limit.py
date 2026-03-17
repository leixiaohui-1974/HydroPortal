"""Simple in-memory token-bucket rate limiter."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from backend.config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class RateLimiter:
    """Token-bucket rate limiter.

    Each *client_id* gets its own bucket with ``max_tokens`` tokens that
    refill at a rate of ``max_tokens / window_seconds`` per second.
    """

    def __init__(
        self,
        max_tokens: int = RATE_LIMIT_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> None:
        self.max_tokens = max_tokens
        self.window_seconds = window_seconds
        self.refill_rate = max_tokens / window_seconds
        self._buckets: dict[str, _Bucket] = {}

    def _get_bucket(self, client_id: str) -> _Bucket:
        if client_id not in self._buckets:
            self._buckets[client_id] = _Bucket(
                tokens=float(self.max_tokens),
                last_refill=time.monotonic(),
            )
        return self._buckets[client_id]

    def check(self, client_id: str) -> bool:
        """Return ``True`` if the request is allowed, ``False`` if rate-limited."""
        bucket = self._get_bucket(client_id)
        now = time.monotonic()
        elapsed = now - bucket.last_refill
        bucket.tokens = min(self.max_tokens, bucket.tokens + elapsed * self.refill_rate)
        bucket.last_refill = now

        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True
        return False

    def reset(self, client_id: str) -> None:
        """Reset a client's bucket to full."""
        self._buckets.pop(client_id, None)


# Module-level default instance
default_limiter = RateLimiter()
