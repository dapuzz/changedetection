"""API client for ChangeDetection.io."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout


class ChangeDetectionApiError(Exception):
    """Exception raised for ChangeDetection.io API errors."""

class ChangeDetectionConnectionError(Exception):
    """Exception raised for ChangeDetection.io Connections errors."""


# Status codes treated as transient/server-side failures for backoff purposes.
_BACKOFF_STATUS_CODES = {408, 429, 500, 502, 503, 504}

_INITIAL_BACKOFF = timedelta(hours=1)
_MAX_BACKOFF = timedelta(hours=24)


class ChangeDetectionClient:
    """Client for interacting with ChangeDetection.io API."""

    def __init__(
        self, base_url: str, api_key: str, session: aiohttp.ClientSession
    ) -> None:
        """Initialize the API client."""
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._session = session

        # Connection error backoff tracking.
        self._error_count: int = 0
        self._last_error_time: Optional[datetime] = None

    @property
    def headers(self) -> Dict[str, str]:
        """Return default headers for API requests."""
        return {
            "x-api-key": self._api_key,
            "Accept": "application/json",
        }

    # ==================== BACKOFF HANDLING ====================

    def _current_backoff(self) -> timedelta:
        """Return the backoff duration for the current error count."""
        if self._error_count <= 0:
            return timedelta(0)
        # 1st error -> 1h, 2nd -> 2h, 3rd -> 4h, ... capped at 24h.
        multiplier = 2 ** (self._error_count - 1)
        backoff = _INITIAL_BACKOFF * multiplier
        return min(backoff, _MAX_BACKOFF)

    def is_connection_available(self) -> bool:
        """Return True if a request should be attempted now.

        Returns False if we are still within the backoff window following
        previous connection errors.
        """
        if self._error_count <= 0 or self._last_error_time is None:
            return True

        backoff = self._current_backoff()
        next_allowed = self._last_error_time + backoff
        return datetime.utcnow() >= next_allowed

    def record_connection_error(self) -> None:
        """Record a connection/server error, advancing the backoff state."""
        self._error_count += 1
        self._last_error_time = datetime.utcnow()

    def reset_connection_error(self) -> None:
        """Reset backoff state after a successful request."""
        self._error_count = 0
        self._last_error_time = None

    def _seconds_until_available(self) -> float:
        """Seconds remaining until the backoff window elapses."""
        if self._last_error_time is None:
            return 0.0
        next_allowed = self._last_error_time + self._current_backoff()
        remaining = (next_allowed - datetime.utcnow()).total_seconds()
        return max(remaining, 0.0)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make an API request."""
        if not self.is_connection_available():
            raise ChangeDetectionConnectionError(
                "Skipping request: still within backoff window "
                f"({self._seconds_until_available():.0f}s remaining after "
                f"{self._error_count} consecutive error(s))"
            )

        url = f"{self._base_url}/api/v1{path}"
        kwargs.setdefault("headers", {}).update(self.headers)

        try:
            async with async_timeout.timeout(30):
                async with self._session.request(method, url, **kwargs) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        if resp.status in _BACKOFF_STATUS_CODES:
                            self.record_connection_error()
                        raise ChangeDetectionApiError(
                            f"API error {resp.status} for {url}: {text}"
                        )

                    self.reset_connection_error()

                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        return await resp.json()
                    return await resp.text()
        except aiohttp.ClientError as err:
            self.record_connection_error()
            raise ChangeDetectionApiError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            self.record_connection_error()
            raise ChangeDetectionApiError(f"Timeout error: {err}") from err

    # ==================== WATCHES ====================

    async def list_watches(
        self, tag: Optional[str] = None, recheck_all: bool = False
    ) -> Dict[str, Any]:
        """List all watches."""
        params: Dict[str, Any] = {}
        if tag:
            params["tag"] = tag
        if recheck_all:
            params["recheck_all"] = "1"
        return await self._request("GET", "/watch", params=params)

    async def create_watch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new watch."""
        return await self._request("POST", "/watch", json=payload)

    async def get_watch(
        self,
        uuid: str,
        recheck: bool = False,
        paused: Optional[str] = None,
        muted: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get watch details."""
        params: Dict[str, Any] = {}
        if recheck:
            params["recheck"] = "true"
        if paused in ("paused", "unpaused"):
            params["paused"] = paused
        if muted in ("muted", "unmuted"):
            params["muted"] = muted
        return await self._request("GET", f"/watch/{uuid}", params=params)

    async def update_watch(self, uuid: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing watch."""
        return await self._request("PUT", f"/watch/{uuid}", json=payload)

    async def delete_watch(self, uuid: str) -> None:
        """Delete a watch."""
        await self._request("DELETE", f"/watch/{uuid}")

    async def watch_history(self, uuid: str) -> Dict[str, str]:
        """Get watch history (list of snapshots)."""
        return await self._request("GET", f"/watch/{uuid}/history")

    async def watch_snapshot(
        self, uuid: str, timestamp: str = "latest", html: bool = False
    ) -> str:
        """Get a specific snapshot of a watch."""
        params: Dict[str, Any] = {}
        if html:
            params["html"] = "1"
        return await self._request(
            "GET", f"/watch/{uuid}/history/{timestamp}", params=params
        )

    async def watch_diff(
        self,
        uuid: str,
        from_ts: str | int,
        to_ts: str | int,
        format_: str = "text",
        word_diff: str = "false",
        no_markup: str = "false",
        type_: str = "diffLines",
        changes_only: str = "true",
        ignore_whitespace: str = "false",
        removed: str = "true",
        added: str = "true",
        replaced: str = "true",
    ) -> str:
        """Get difference between two snapshots."""
        params = {
            "format": format_,
            "word_diff": word_diff,
            "no_markup": no_markup,
            "type": type_,
            "changesOnly": changes_only,
            "ignoreWhitespace": ignore_whitespace,
            "removed": removed,
            "added": added,
            "replaced": replaced,
        }
        return await self._request(
            "GET", f"/watch/{uuid}/difference/{from_ts}/{to_ts}", params=params
        )

    async def watch_favicon(self, uuid: str) -> bytes:
        """Get watch favicon."""
        return await self._request("GET", f"/watch/{uuid}/favicon")

    # ==================== TAGS ====================

    async def list_tags(self) -> Dict[str, Any]:
        """List all tags."""
        return await self._request("GET", "/tags")

    async def create_tag(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tag."""
        return await self._request("POST", "/tag", json=payload)

    async def get_tag(
        self, uuid: str, muted: Optional[str] = None, recheck: bool = False
    ) -> Dict[str, Any]:
        """Get tag details."""
        params: Dict[str, Any] = {}
        if muted in ("muted", "unmuted"):
            params["muted"] = muted
        if recheck:
            params["recheck"] = "true"
        return await self._request("GET", f"/tag/{uuid}", params=params)

    async def update_tag(self, uuid: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tag."""
        return await self._request("PUT", f"/tag/{uuid}", json=payload)

    async def delete_tag(self, uuid: str) -> None:
        """Delete a tag."""
        await self._request("DELETE", f"/tag/{uuid}")

    # ==================== NOTIFICATIONS ====================

    async def get_notifications(self) -> List[str]:
        """Get notification URLs."""
        return await self._request("GET", "/notifications")

    async def add_notifications(self, urls: List[str]) -> Any:
        """Add notification URLs."""
        return await self._request(
            "POST", "/notifications", json={"notification_urls": urls}
        )

    async def replace_notifications(self, urls: List[str]) -> Any:
        """Replace all notification URLs."""
        return await self._request(
            "PUT", "/notifications", json={"notification_urls": urls}
        )

    async def delete_notifications(self, urls: List[str]) -> Any:
        """Delete notification URLs."""
        return await self._request(
            "DELETE", "/notifications", json={"notification_urls": urls}
        )

    # ==================== SEARCH ====================

    async def search(
        self, q: str, tag: Optional[str] = None, partial: bool = False
    ) -> Dict[str, Any]:
        """Search watches."""
        params: Dict[str, Any] = {"q": q}
        if tag:
            params["tag"] = tag
        if partial:
            params["partial"] = "1"
        return await self._request("GET", "/search", params=params)

    # ==================== IMPORT ====================

    async def bulk_import(
        self,
        body: str,
        tag_uuids: Optional[str] = None,
        tag: Optional[str] = None,
        proxy: Optional[str] = None,
        dedupe: bool = True,
    ) -> List[str]:
        """Bulk import URLs."""
        params: Dict[str, Any] = {}
        if tag_uuids:
            params["tag_uuids"] = tag_uuids
        if tag:
            params["tag"] = tag
        if proxy:
            params["proxy"] = proxy
        params["dedupe"] = "true" if dedupe else "false"

        return await self._request(
            "POST",
            "/import",
            params=params,
            data=body,
            headers={"Content-Type": "text/plain"},
        )

    # ==================== SYSTEM INFO ====================

    async def systeminfo(self) -> Dict[str, Any]:
        """Get system information."""
        return await self._request("GET", "/systeminfo")
