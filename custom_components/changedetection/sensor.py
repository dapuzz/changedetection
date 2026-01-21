"""Sensor platform for ChangeDetection.io."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo 


from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ChangeDetection.io sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]

    entities: list[SensorEntity] = []

    # Add watch sensors
    watches = coordinator.data.get("watches", {})
    for uuid, info in watches.items():
        entities.append(
            ChangeDetectionWatchSensor(
                coordinator=coordinator,
                client=client,
                uuid=uuid,
                info=info,
                entry_id=entry.entry_id,
            )
        )

    # Add system info sensors
    entities.extend(
        [
            ChangeDetectionSystemInfoSensor(
                coordinator=coordinator,
                sensor_type="watch_count",
                name="Watch Count",
                icon="mdi:counter",
                entry_id=entry.entry_id,
            ),
            ChangeDetectionSystemInfoSensor(
                coordinator=coordinator,
                sensor_type="tag_count",
                name="Tag Count",
                icon="mdi:tag-multiple",
                entry_id=entry.entry_id,
            ),
            ChangeDetectionSystemInfoSensor(
                coordinator=coordinator,
                sensor_type="version",
                name="Version",
                icon="mdi:information",
                entry_id=entry.entry_id,
            ),
        ]
    )

    async_add_entities(entities)


class ChangeDetectionWatchSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing a ChangeDetection.io watch."""

    _attr_icon = "mdi:web"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True


    def __init__(
        self, coordinator, client, uuid: str, info: dict[str, Any], entry_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._client = client
        self._uuid = uuid
        self._entry_id = entry_id
        self._attr_unique_id = f"watch_{uuid}"
        self._attr_name = (
            info.get("title")
            or info.get("page_title")
            or f"Watch {uuid[:8]}"
        )

    @property
    def device_info(self) -> DeviceInfo: 
        """Return device info to link entity with device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor."""
        data = self.coordinator.data.get("watches", {}).get(self._uuid, {})
        ts = data.get("last_changed")
        if ts:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get("watches", {}).get(self._uuid, {})
        
        # Converti last_checked in formato ISO8601
        last_checked = None
        if data.get("last_checked"):
            last_checked = datetime.fromtimestamp(
                data["last_checked"], tz=timezone.utc
            ).isoformat()        
            
        return {
            "uuid": self._uuid,
            "url": data.get("url"),
            "link": data.get("link"),
            "page_title": data.get("page_title"),
            "paused": data.get("paused", False),
            "notification_muted": data.get("notification_muted", False),
            "method": data.get("method"),
            "fetch_backend": data.get("fetch_backend"),
            "last_checked": last_checked,
            "last_error": data.get("last_error"),
            "tags": data.get("tags", []),
        }


class ChangeDetectionSystemInfoSensor(CoordinatorEntity, SensorEntity):
    """Sensor for ChangeDetection.io system information."""
    
    _attr_has_entity_name = True

    def __init__(
        self, coordinator, sensor_type: str, name: str, icon: str, entry_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._entry_id = entry_id
        self._attr_unique_id = f"systeminfo_{sensor_type}"
        self._attr_name = f"ChangeDetection.io {name}"
        self._attr_icon = icon
        
        # State class solo per sensori numerici
        if sensor_type in ("watch_count", "tag_count"):
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo: 
        """Return device info to link entity with device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )

    @property
    def native_value(self) -> int | str | None:
        """Return the state of the sensor."""
        systeminfo = self.coordinator.data.get("systeminfo", {})
        return systeminfo.get(self._sensor_type)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes for version sensor."""
        if self._sensor_type == "version":
            systeminfo = self.coordinator.data.get("systeminfo", {})
            return {
                "watch_count": systeminfo.get("watch_count"),
                "tag_count": systeminfo.get("tag_count"),
            }
        return None
