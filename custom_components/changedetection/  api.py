from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientSession


@dataclass
class ChangeDetectionClient:
    base_url: str
    api_key: str
    session: ClientSession

    @property
    def _api_root(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1"

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key}

    async def get_watches(self) -> dict[str, Any]:
        url = f"{self._api_root}/watch"
        async with self.session.get(url, headers=self._headers()) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_systeminfo(self) -> dict[str, Any]:
        url = f"{self._api_root}/systeminfo"
        async with self.session.get(url, headers=self._headers()) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def recheck_watch(self, uuid: str) -> dict[str, Any]:
        # La doc indica che il recheck si attiva passando ?recheck=1 (o true) su GET watch/{uuid}. [page:1]
        url = f"{self._api_root}/watch/{uuid}"
        async with self.session.get(url, params={"recheck": "1"}, headers=self._headers()) as resp:
            resp.raise_for_status()
            return await resp.json()
