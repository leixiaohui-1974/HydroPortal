"""Shared test fixtures and configuration for HydroPortal tests."""
from __future__ import annotations

import pytest

from backend.deps import init_app_registry
from backend.middleware.rate_limit import default_limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset the rate limiter before each test to avoid 429 interference."""
    default_limiter._buckets.clear()
    yield
    default_limiter._buckets.clear()


@pytest.fixture(autouse=True, scope="session")
def _init_registry():
    """Ensure the app registry is populated for all tests."""
    init_app_registry()
