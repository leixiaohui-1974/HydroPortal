"""Shared proxy helper for domain routers.

Each domain router can call ``_proxy_or_mock()`` to attempt forwarding a
request to its upstream service and gracefully fall back to local demo data
when the upstream is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Reusable timeout for upstream calls
_UPSTREAM_TIMEOUT = 10.0


def _extract_error_detail(resp: httpx.Response) -> Any:
    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return resp.json()
        except ValueError:
            pass

    text = resp.text.strip()
    return text or {"detail": f"Upstream service returned HTTP {resp.status_code}"}


async def proxy_or_mock(
    *,
    upstream_url: str,
    method: str,
    path: str,
    mock_data: Any,
    json_body: dict | None = None,
    params: dict | None = None,
    fallback_on_http_error: bool = True,
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
                try:
                    return resp.json()
                except ValueError as exc:
                    logger.warning(
                        "Upstream %s%s returned invalid JSON for successful response",
                        upstream_url,
                        path,
                    )
                    raise HTTPException(
                        status_code=502,
                        detail="Upstream service returned an invalid JSON payload.",
                    ) from exc

            logger.warning(
                "Upstream %s%s returned %d",
                upstream_url,
                path,
                resp.status_code,
            )
            if fallback_on_http_error:
                logger.warning(
                    "Serving mock data for %s %s after upstream HTTP error",
                    method,
                    path,
                )
                return mock_data
            raise HTTPException(
                status_code=resp.status_code,
                detail=_extract_error_detail(resp),
            )
    except HTTPException:
        raise
    except httpx.RequestError:
        logger.info(
            "Upstream %s%s unreachable, serving mock data",
            upstream_url, path,
        )

    return mock_data
