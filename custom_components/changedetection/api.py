"""API client for ChangeDetection.io."""
from __future__ import annotations

import aiohttp
import async_timeout
from typing import Any, Dict, List, Optional


class ChangeDetectorApiError(Exception):
    """Exception raised for ChangeDetection.io API errors."""


class ChangeDetectorClient:
    """Client for interacting with ChangeDetection.io API."""

    def __init__(
        self, base_url: str, api_key: str, session: aiohttp.ClientSession
    ) -> None:
        """Initialize the API client."""
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._session = session

    @property
    def headers(self) -> Dict[str, str]:
        """Return default headers for API requests."""
        return {
            "x-api-key": self._api_key,
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make an API request."""
        url = f"{self._base_url}/api/v1{path}"
        kwargs.setdefault("headers", {}).update(self.headers)
        
        try:
            async with async_timeout.timeout(30):
                async with self._session.request(method, url, **kwargs) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        raise ChangeDetectorApiError(
                            f"API error {resp.status} for {url}: {text}"
                        )
                    
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        return await resp.json()
                    return await resp.text()
        except aiohttp.ClientError as err:
            raise ChangeDetectorApiError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            raise ChangeDetectorApiError(f"Timeout error: {err}") from err

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
