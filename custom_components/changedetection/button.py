"""Button platform for ChangeDetection.io."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo

from .api import ChangeDetectionApiError
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ChangeDetection.io buttons."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]

    entities: list[ButtonEntity] = []

    # Add recheck button for each watch
    watches = coordinator.data.get("watches", {})
    for uuid, info in watches.items():
        name = (
            info.get("title")
            or info.get("page_title")
            or f"Watch {uuid[:8]}"
        )
        entities.append(
            ChangeDetectionRecheckButton(
                client=client,
                uuid=uuid,
                name=f"{name} Recheck",
                entry_id=entry.entry_id,
            )
        )

    async_add_entities(entities)


class ChangeDetectionRecheckButton(ButtonEntity):
    """Button to recheck a watch."""

    _attr_icon = "mdi:refresh"
    _attr_has_entity_name = True

    def __init__(self, client, uuid: str, name: str, entry_id: str) -> None:
        """Initialize the button."""
        self._client = client
        self._uuid = uuid
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_unique_id = f"recheck_{uuid}"

    @property
    def device_info(self) -> DeviceInfo:  
        """Return device info to link entity with device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self._client.get_watch(self._uuid, recheck=True)
        except ChangeDetectionApiError as err:
            raise HomeAssistantError(f"Failed to recheck watch: {err}") from err
