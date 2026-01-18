from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import service

from .api import ChangeDetectionClient
from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    SERVICE_RECHECK_WATCH,
    SERVICE_RECHECK_WATCH_FIELD_UUID,
)
from .coordinator import ChangeDetectionCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = aiohttp_client.async_get_clientsession(hass)

    client = ChangeDetectionClient(
        base_url=entry.data[CONF_BASE_URL],
        api_key=entry.data[CONF_API_KEY],
        session=session,
    )

    coordinator = ChangeDetectionCoordinator(
        hass=hass,
        client=client,
        scan_interval_s=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    async def _handle_recheck_watch(call: service.ServiceCall) -> None:
        uuid = call.data[SERVICE_RECHECK_WATCH_FIELD_UUID]
        await client.recheck_watch(uuid)  # GET /api/v1/watch/{uuid}?recheck=1 [page:1]
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECHECK_WATCH,
        _handle_recheck_watch,
        schema=vol.Schema(
            {
                vol.Required(SERVICE_RECHECK_WATCH_FIELD_UUID): str,
            }
        ),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
