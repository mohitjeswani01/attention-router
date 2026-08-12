import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class DaemonClientError(Exception):
    """Raised when the AO daemon returns an error or is unreachable."""


class DaemonClient:
    """
    Thin async wrapper around the AO daemon HTTP API.
    All methods are safe to call even if the daemon is down — they raise DaemonClientError
    with a descriptive message instead of crashing the process.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self._base_url = (base_url or settings.ao_daemon_base_url).rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        client = await self._get_client()
        url = f"{self._base_url}{path}"
        try:
            resp = await client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
            logger.error("AO daemon HTTP error %s %s: %s", method, url, exc.response.text)
            raise DaemonClientError(f"Daemon {method} {path} failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("AO daemon connection error %s %s: %s", method, url, exc)
            raise DaemonClientError(f"Cannot reach daemon at {self._base_url}: {exc}") from exc

    # ---- Public API -------------------------------------------------

    async def list_sessions(self) -> List[dict]:
        resp = await self._request("GET", "/api/v1/sessions")
        return resp.json()

    async def get_session(self, session_id: str) -> dict:
        resp = await self._request("GET", f"/api/v1/sessions/{session_id}")
        return resp.json()

    async def list_projects(self) -> List[dict]:
        resp = await self._request("GET", "/api/v1/projects")
        return resp.json()

    async def list_agents(self) -> List[dict]:
        resp = await self._request("GET", "/api/v1/agents")
        return resp.json()

    async def stream_events(self) -> AsyncGenerator[dict, None]:
        """
        Consume the SSE endpoint `/api/v1/events` as an async generator.
        Yields parsed JSON objects for each event line.
        """
        client = await self._get_client()
        url = f"{self._base_url}/api/v1/events"
        headers = {"Accept": "text/event-stream"}
        try:
            async with client.stream("GET", url, headers=headers, timeout=None) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[len("data:") :].strip()
                    if not payload:
                        continue
                    try:
                        yield json.loads(payload)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse SSE payload: %s", payload)
        except httpx.RequestError as exc:
            logger.error("SSE connection error: %s", exc)
            raise DaemonClientError(f"SSE stream failed: {exc}") from exc

    # convenience context manager for use in background tasks
    @asynccontextmanager
    async def lifespan(self):
        try:
            yield self
        finally:
            await self.close()