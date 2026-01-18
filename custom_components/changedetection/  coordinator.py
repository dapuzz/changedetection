from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ChangeDetectionClient
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


@dataclass
class ChangeDetectionData:
    watches: dict[str, Any]
    systeminfo: dict[str, Any]


class ChangeDetectionCoordinator(DataUpdateCoordinator[ChangeDetectionData]):
    def __init__(self, hass: HomeAssistant, client: ChangeDetectionClient, scan_interval_s: int) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_s or DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> ChangeDetectionData:
        try:
            watches = await self.client.get_watches()  # GET /api/v1/watch [page:1]
            systeminfo = await self.client.get_systeminfo()  # GET /api/v1/systeminfo [page:1]
            return ChangeDetectionData(watches=watches, systeminfo=systeminfo)
        except Exception as err:
            raise UpdateFailed(str(err)) from err
