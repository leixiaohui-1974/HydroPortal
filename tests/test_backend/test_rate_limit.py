"""Rate limiter tests."""

import pytest

from backend.middleware.rate_limit import RateLimiter


def test_allows_within_limit():
    limiter = RateLimiter(max_tokens=5, window_seconds=60)
    for _ in range(5):
        assert limiter.check("client-a") is True


def test_blocks_over_limit():
    limiter = RateLimiter(max_tokens=3, window_seconds=60)
    for _ in range(3):
        limiter.check("client-b")
    assert limiter.check("client-b") is False


def test_separate_clients():
    limiter = RateLimiter(max_tokens=2, window_seconds=60)
    assert limiter.check("c1") is True
    assert limiter.check("c1") is True
    assert limiter.check("c1") is False
    # c2 should still have tokens
    assert limiter.check("c2") is True


def test_reset():
    limiter = RateLimiter(max_tokens=1, window_seconds=60)
    assert limiter.check("x") is True
    assert limiter.check("x") is False
    limiter.reset("x")
    assert limiter.check("x") is True
