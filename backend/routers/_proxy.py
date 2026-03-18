"""Shared proxy helper for domain routers.

Each domain router can call ``_proxy_or_mock()`` to attempt forwarding a
request to its upstream service and gracefully fall back to local demo data
when the upstream is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Reusable timeout for upstream calls
_UPSTREAM_TIMEOUT = 10.0


async def proxy_or_mock(
    *,
    upstream_url: str,
    method: str,
    path: str,
    mock_data: Any,
    json_body: dict | None = None,
    params: dict | None = None,
) -> Any:
    """Forward a request to the upstream service; fall back to *mock_data*.

    Parameters
    ----------
    upstream_url:
        Base URL of the upstream service (e.g. ``http://localhost:8001``).
    method:
        HTTP method (``GET`` or ``POST``).
    path:
        Path to append to *upstream_url* (e.g. ``/api/stations``).
    mock_data:
        Data to return when the upstream is unreachable.
    json_body:
        Optional JSON body for POST requests.
    params:
        Optional query parameters.

    Returns
    -------
    The upstream response data (parsed JSON) on success, or *mock_data* on
    failure.
    """
    try:
        async with httpx.AsyncClient(timeout=_UPSTREAM_TIMEOUT) as client:
            if method.upper() == "POST":
                resp = await client.post(
                    f"{upstream_url}{path}",
                    json=json_body or {},
                    params=params,
                )
            else:
                resp = await client.get(
                    f"{upstream_url}{path}",
                    params=params,
                )

            if resp.status_code < 400:
                logger.debug("Proxy %s %s -> %d", method, path, resp.status_code)
                return resp.json()

            logger.warning(
                "Upstream %s%s returned %d, falling back to mock",
                upstream_url, path, resp.status_code,
            )
    except Exception:
        logger.info(
            "Upstream %s%s unreachable, serving mock data",
            upstream_url, path,
        )

    return mock_data
