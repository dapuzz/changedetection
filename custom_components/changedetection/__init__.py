"""The ChangeDetection.io integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .api import ChangeDetectorClient, ChangeDetectorApiError
from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
    SERVICE_CREATE_WATCH,
    SERVICE_DELETE_WATCH,
    SERVICE_UPDATE_WATCH,
    SERVICE_RECHECK_WATCH,
    SERVICE_PAUSE_WATCH,
    SERVICE_UNPAUSE_WATCH,
    SERVICE_MUTE_WATCH,
    SERVICE_UNMUTE_WATCH,
    SERVICE_GET_SNAPSHOT,
    SERVICE_GET_DIFF,
    SERVICE_CREATE_TAG,
    SERVICE_DELETE_TAG,
    SERVICE_UPDATE_TAG,
    SERVICE_RECHECK_TAG,
    SERVICE_MUTE_TAG,
    SERVICE_UNMUTE_TAG,
    SERVICE_SEARCH,
    SERVICE_BULK_IMPORT,
    SERVICE_ADD_NOTIFICATIONS,
    SERVICE_REPLACE_NOTIFICATIONS,
    SERVICE_DELETE_NOTIFICATIONS,
    ATTR_UUID,
    ATTR_URL,
    ATTR_TITLE,
    ATTR_TAG,
    ATTR_TAGS,
    ATTR_PAUSED,
    ATTR_NOTIFICATION_MUTED,
    ATTR_METHOD,
    ATTR_FETCH_BACKEND,
    ATTR_HEADERS,
    ATTR_BODY,
    ATTR_PROXY,
    ATTR_TIME_BETWEEN_CHECK,
    ATTR_NOTIFICATION_URLS,
    ATTR_NOTIFICATION_TITLE,
    ATTR_NOTIFICATION_BODY,
    ATTR_NOTIFICATION_FORMAT,
    ATTR_PROCESSOR,
    ATTR_TIMESTAMP,
    ATTR_FROM_TIMESTAMP,
    ATTR_TO_TIMESTAMP,
    ATTR_FORMAT,
    ATTR_WORD_DIFF,
    ATTR_QUERY,
    ATTR_URLS_TEXT,
    ATTR_TAG_UUIDS,
    ATTR_DEDUPE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ChangeDetection.io from a config entry."""
    session = async_get_clientsession(hass)
    client = ChangeDetectorClient(
        entry.data[CONF_BASE_URL],
        entry.data[CONF_API_KEY],
        session,
    )

    async def async_update_data() -> dict[str, Any]:
        """Fetch data from API."""
        try:
            watches = await client.list_watches()
            tags = await client.list_tags()
            systeminfo = await client.systeminfo()
            notifications = await client.get_notifications()
        except ChangeDetectorApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        
        return {
            "watches": watches,
            "tags": tags,
            "systeminfo": systeminfo,
            "notifications": notifications,
        }

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ChangeDetection.io",
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_create_watch(call: ServiceCall) -> None:
        """Handle create watch service."""
        payload: dict[str, Any] = {ATTR_URL: call.data[ATTR_URL]}
        
        if ATTR_TITLE in call.data:
            payload[ATTR_TITLE] = call.data[ATTR_TITLE]
        if ATTR_TAG in call.data:
            payload[ATTR_TAG] = call.data[ATTR_TAG]
        if ATTR_TAGS in call.data:
            payload[ATTR_TAGS] = call.data[ATTR_TAGS]
        if ATTR_METHOD in call.data:
            payload[ATTR_METHOD] = call.data[ATTR_METHOD]
        if ATTR_FETCH_BACKEND in call.data:
            payload[ATTR_FETCH_BACKEND] = call.data[ATTR_FETCH_BACKEND]
        if ATTR_PROCESSOR in call.data:
            payload[ATTR_PROCESSOR] = call.data[ATTR_PROCESSOR]
        
        try:
            await client.create_watch(payload)
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to create watch: {err}") from err

    async def handle_delete_watch(call: ServiceCall) -> None:
        """Handle delete watch service."""
        try:
            await client.delete_watch(call.data[ATTR_UUID])
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to delete watch: {err}") from err

    async def handle_update_watch(call: ServiceCall) -> None:
        """Handle update watch service."""
        uuid = call.data[ATTR_UUID]
        payload = {k: v for k, v in call.data.items() if k != ATTR_UUID}
        
        try:
            await client.update_watch(uuid, payload)
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to update watch: {err}") from err

    async def handle_recheck_watch(call: ServiceCall) -> None:
        """Handle recheck watch service."""
        try:
            await client.get_watch(call.data[ATTR_UUID], recheck=True)
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to recheck watch: {err}") from err

    async def handle_pause_watch(call: ServiceCall) -> None:
        """Handle pause watch service."""
        try:
            await client.get_watch(call.data[ATTR_UUID], paused="paused")
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to pause watch: {err}") from err

    async def handle_unpause_watch(call: ServiceCall) -> None:
        """Handle unpause watch service."""
        try:
            await client.get_watch(call.data[ATTR_UUID], paused="unpaused")
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to unpause watch: {err}") from err

    async def handle_mute_watch(call: ServiceCall) -> None:
        """Handle mute watch service."""
        try:
            await client.get_watch(call.data[ATTR_UUID], muted="muted")
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to mute watch: {err}") from err

    async def handle_unmute_watch(call: ServiceCall) -> None:
        """Handle unmute watch service."""
        try:
            await client.get_watch(call.data[ATTR_UUID], muted="unmuted")
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to unmute watch: {err}") from err

    async def handle_get_snapshot(call: ServiceCall) -> None:
        """Handle get snapshot service."""
        uuid = call.data[ATTR_UUID]
        timestamp = call.data.get(ATTR_TIMESTAMP, "latest")
        
        try:
            snapshot = await client.watch_snapshot(uuid, timestamp)
            hass.bus.async_fire(
                f"{DOMAIN}_snapshot_received",
                {ATTR_UUID: uuid, ATTR_TIMESTAMP: timestamp, "content": snapshot},
            )
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to get snapshot: {err}") from err

    async def handle_get_diff(call: ServiceCall) -> None:
        """Handle get diff service."""
        uuid = call.data[ATTR_UUID]
        from_ts = call.data.get(ATTR_FROM_TIMESTAMP, "previous")
        to_ts = call.data.get(ATTR_TO_TIMESTAMP, "latest")
        format_ = call.data.get(ATTR_FORMAT, "htmlcolor")
        word_diff = "true" if call.data.get(ATTR_WORD_DIFF, False) else "false"
        
        try:
            diff = await client.watch_diff(uuid, from_ts, to_ts, format_, word_diff)
            hass.bus.async_fire(
                f"{DOMAIN}_diff_received",
                {
                    ATTR_UUID: uuid,
                    ATTR_FROM_TIMESTAMP: from_ts,
                    ATTR_TO_TIMESTAMP: to_ts,
                    "content": diff,
                },
            )
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to get diff: {err}") from err

    async def handle_create_tag(call: ServiceCall) -> None:
        """Handle create tag service."""
        payload: dict[str, Any] = {ATTR_TITLE: call.data[ATTR_TITLE]}
        
        if ATTR_NOTIFICATION_URLS in call.data:
            payload[ATTR_NOTIFICATION_URLS] = call.data[ATTR_NOTIFICATION_URLS]
        if ATTR_NOTIFICATION_MUTED in call.data:
            payload[ATTR_NOTIFICATION_MUTED] = call.data[ATTR_NOTIFICATION_MUTED]
        
        try:
            await client.create_tag(payload)
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to create tag: {err}") from err

    async def handle_delete_tag(call: ServiceCall) -> None:
        """Handle delete tag service."""
        try:
            await client.delete_tag(call.data[ATTR_UUID])
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to delete tag: {err}") from err

    async def handle_update_tag(call: ServiceCall) -> None:
        """Handle update tag service."""
        uuid = call.data[ATTR_UUID]
        payload = {k: v for k, v in call.data.items() if k != ATTR_UUID}
        
        try:
            await client.update_tag(uuid, payload)
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to update tag: {err}") from err

    async def handle_recheck_tag(call: ServiceCall) -> None:
        """Handle recheck tag service."""
        try:
            await client.get_tag(call.data[ATTR_UUID], recheck=True)
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to recheck tag: {err}") from err

    async def handle_mute_tag(call: ServiceCall) -> None:
        """Handle mute tag service."""
        try:
            await client.get_tag(call.data[ATTR_UUID], muted="muted")
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to mute tag: {err}") from err

    async def handle_unmute_tag(call: ServiceCall) -> None:
        """Handle unmute tag service."""
        try:
            await client.get_tag(call.data[ATTR_UUID], muted="unmuted")
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to unmute tag: {err}") from err

    async def handle_search(call: ServiceCall) -> None:
        """Handle search service."""
        query = call.data[ATTR_QUERY]
        tag = call.data.get(ATTR_TAG)
        
        try:
            results = await client.search(query, tag)
            hass.bus.async_fire(
                f"{DOMAIN}_search_results",
                {ATTR_QUERY: query, "results": results},
            )
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to search: {err}") from err

    async def handle_bulk_import(call: ServiceCall) -> None:
        """Handle bulk import service."""
        urls_text = call.data[ATTR_URLS_TEXT]
        tag_uuids = call.data.get(ATTR_TAG_UUIDS)
        tag = call.data.get(ATTR_TAG)
        proxy = call.data.get(ATTR_PROXY)
        dedupe = call.data.get(ATTR_DEDUPE, True)
        
        try:
            imported = await client.bulk_import(urls_text, tag_uuids, tag, proxy, dedupe)
            await coordinator.async_request_refresh()
            hass.bus.async_fire(
                f"{DOMAIN}_import_completed",
                {"imported_uuids": imported},
            )
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to bulk import: {err}") from err

    async def handle_add_notifications(call: ServiceCall) -> None:
        """Handle add notifications service."""
        try:
            await client.add_notifications(call.data[ATTR_NOTIFICATION_URLS])
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to add notifications: {err}") from err

    async def handle_replace_notifications(call: ServiceCall) -> None:
        """Handle replace notifications service."""
        try:
            await client.replace_notifications(call.data[ATTR_NOTIFICATION_URLS])
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to replace notifications: {err}") from err

    async def handle_delete_notifications(call: ServiceCall) -> None:
        """Handle delete notifications service."""
        try:
            await client.delete_notifications(call.data[ATTR_NOTIFICATION_URLS])
            await coordinator.async_request_refresh()
        except ChangeDetectorApiError as err:
            raise HomeAssistantError(f"Failed to delete notifications: {err}") from err

    # Service schemas
    CREATE_WATCH_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_URL): cv.url,
            vol.Optional(ATTR_TITLE): cv.string,
            vol.Optional(ATTR_TAG): cv.string,
            vol.Optional(ATTR_TAGS): cv.ensure_list,
            vol.Optional(ATTR_METHOD): vol.In(["GET", "POST", "PUT", "DELETE"]),
            vol.Optional(ATTR_FETCH_BACKEND): vol.In(["html_requests", "html_webdriver"]),
            vol.Optional(ATTR_PROCESSOR): vol.In(["text_json_diff", "restock_diff"]),
        }
    )

    UPDATE_WATCH_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_UUID): cv.string,
            vol.Optional(ATTR_URL): cv.url,
            vol.Optional(ATTR_TITLE): cv.string,
            vol.Optional(ATTR_PAUSED): cv.boolean,
            vol.Optional(ATTR_NOTIFICATION_MUTED): cv.boolean,
        }
    )

    UUID_SCHEMA = vol.Schema({vol.Required(ATTR_UUID): cv.string})

    SNAPSHOT_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_UUID): cv.string,
            vol.Optional(ATTR_TIMESTAMP, default="latest"): cv.string,
        }
    )

    DIFF_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_UUID): cv.string,
            vol.Optional(ATTR_FROM_TIMESTAMP, default="previous"): cv.string,
            vol.Optional(ATTR_TO_TIMESTAMP, default="latest"): cv.string,
            vol.Optional(ATTR_FORMAT, default="htmlcolor"): vol.In(
                ["text", "html", "htmlcolor", "markdown"]
            ),
            vol.Optional(ATTR_WORD_DIFF, default=False): cv.boolean,
        }
    )

    CREATE_TAG_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_TITLE): cv.string,
            vol.Optional(ATTR_NOTIFICATION_URLS): cv.ensure_list,
            vol.Optional(ATTR_NOTIFICATION_MUTED): cv.boolean,
        }
    )

    UPDATE_TAG_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_UUID): cv.string,
            vol.Optional(ATTR_TITLE): cv.string,
            vol.Optional(ATTR_NOTIFICATION_URLS): cv.ensure_list,
            vol.Optional(ATTR_NOTIFICATION_MUTED): cv.boolean,
        }
    )

    SEARCH_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_QUERY): cv.string,
            vol.Optional(ATTR_TAG): cv.string,
        }
    )

    IMPORT_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_URLS_TEXT): cv.string,
            vol.Optional(ATTR_TAG_UUIDS): cv.string,
            vol.Optional(ATTR_TAG): cv.string,
            vol.Optional(ATTR_PROXY): cv.string,
            vol.Optional(ATTR_DEDUPE, default=True): cv.boolean,
        }
    )

    NOTIFICATION_URLS_SCHEMA = vol.Schema(
        {vol.Required(ATTR_NOTIFICATION_URLS): cv.ensure_list}
    )

    # Register all services
    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_WATCH, handle_create_watch, schema=CREATE_WATCH_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_WATCH, handle_delete_watch, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_WATCH, handle_update_watch, schema=UPDATE_WATCH_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RECHECK_WATCH, handle_recheck_watch, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PAUSE_WATCH, handle_pause_watch, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UNPAUSE_WATCH, handle_unpause_watch, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_MUTE_WATCH, handle_mute_watch, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UNMUTE_WATCH, handle_unmute_watch, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_GET_SNAPSHOT, handle_get_snapshot, schema=SNAPSHOT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_GET_DIFF, handle_get_diff, schema=DIFF_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_TAG, handle_create_tag, schema=CREATE_TAG_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_TAG, handle_delete_tag, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_TAG, handle_update_tag, schema=UPDATE_TAG_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RECHECK_TAG, handle_recheck_tag, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_MUTE_TAG, handle_mute_tag, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UNMUTE_TAG, handle_unmute_tag, schema=UUID_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SEARCH, handle_search, schema=SEARCH_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_BULK_IMPORT, handle_bulk_import, schema=IMPORT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_NOTIFICATIONS,
        handle_add_notifications,
        schema=NOTIFICATION_URLS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPLACE_NOTIFICATIONS,
        handle_replace_notifications,
        schema=NOTIFICATION_URLS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_NOTIFICATIONS,
        handle_delete_notifications,
        schema=NOTIFICATION_URLS_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
