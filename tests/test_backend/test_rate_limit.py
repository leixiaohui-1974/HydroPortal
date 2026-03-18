"""Rate limiter tests — token bucket logic and HTTP middleware integration."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app import app
from backend.middleware.rate_limit import RateLimiter


# ---------------------------------------------------------------------------
# Unit tests: RateLimiter
# ---------------------------------------------------------------------------

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


def test_refill_rate_calculation():
    limiter = RateLimiter(max_tokens=120, window_seconds=60)
    assert limiter.refill_rate == 2.0


def test_zero_tokens_edge_case():
    limiter = RateLimiter(max_tokens=1, window_seconds=60)
    assert limiter.check("edge") is True
    assert limiter.check("edge") is False
    assert limiter.check("edge") is False  # still blocked


# ---------------------------------------------------------------------------
# Integration: HTTP middleware returns 429
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_rate_limit_middleware_returns_429(client: AsyncClient):
    """The /health endpoint (no auth needed) should eventually return 429
    if we exceed the rate limit.  We use a tight loop to exhaust the bucket."""
    from backend.middleware.rate_limit import default_limiter

    # Drain the bucket for the test client IP
    test_ip = "testclient"
    original_tokens = default_limiter.max_tokens

    # Temporarily set a very small limit
    default_limiter.max_tokens = 2
    default_limiter._buckets.pop(test_ip, None)

    responses = []
    for _ in range(5):
        resp = await client.get("/health")
        responses.append(resp.status_code)

    # Restore
    default_limiter.max_tokens = original_tokens
    default_limiter._buckets.pop(test_ip, None)

    assert 429 in responses, f"Expected at least one 429 but got: {responses}"
