"""Sensor platform for ChangeDetection.io."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_CONFIG_ENTRY_ID
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers.device_registry import CONNECTION_CONFIG_ENTRY_ID

from .const import ATTR_WATCHES, DOMAIN
from .coordinator import ChangeDetectionCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: ChangeDetectionCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Device registry per il device principale (config entry)
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"ChangeDetection.io {entry.title}",
        manufacturer="ChangeDetection.io",
        model="Web Monitor Instance",
    )
    device_id = device_entry.id

    # Sensori System Info (sul device principale)
    system_sensors = [
        ChangeDetectionSystemInfoSensor(coordinator, entry, "watch_count", "Watches Count", device_id),
        ChangeDetectionSystemInfoSensor(coordinator, entry, "tag_count", "Tags Count", device_id),
        ChangeDetectionSystemInfoSensor(coordinator, entry, "version", "Version", device_id),
    ]

    # Sensori per OGNI WATCH (device_id = device principale)
    watch_sensors = []
    for uuid, watch_data in coordinator.data.watches.items():
        watch_title = watch_data.get("title", "Unknown") or "Unnamed Watch"
        
        watch_sensors.extend([
            # Title (statico, ma utile per identificazione)
            ChangeDetectionWatchSensor(coordinator, entry, uuid, "title", f"{watch_title}", device_id, "text"),
            # Paused
            ChangeDetectionWatchSensor(coordinator, entry, uuid, "paused", f"{watch_title} Paused", device_id, "boolean"),
            # Notification Muted
            ChangeDetectionWatchSensor(coordinator, entry, uuid, "notification_muted", f"{watch_title} Notifications Muted", device_id, "boolean"),
            # Last Checked (timestamp)
            ChangeDetectionWatchSensor(coordinator, entry, uuid, "last_checked", f"{watch_title} Last Checked", device_id, "timestamp"),
            # Last Changed (timestamp)
            ChangeDetectionWatchSensor(coordinator, entry, uuid, "last_changed", f"{watch_title} Last Changed", device_id, "timestamp"),
        ])

    async_add_entities(system_sensors + watch_sensors)


class ChangeDetectionSystemInfoSensor(CoordinatorEntity[ChangeDetectionCoordinator], SensorEntity):
    """Sensor per System Info."""

    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator: ChangeDetectionCoordinator, entry: ConfigEntry, key: str, name: str, device_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_system_{key}"
        self._attr_name = f"ChangeDetection {name}"
        self._attr_device_id = device_id
        self._attr_has_entity_name = True
        self.key = key

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.systeminfo.get(self.key)


class ChangeDetectionWatchSensor(CoordinatorEntity[ChangeDetectionCoordinator], SensorEntity):
    """Sensor per singola Watch."""

    def __init__(
        self,
        coordinator: ChangeDetectionCoordinator,
        entry: ConfigEntry,
        uuid: str,
        key: str,
        name: str,
        device_id: str,
        native_unit: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._uuid = uuid
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{uuid}_{key}"
        self._attr_name = name
        self._attr_device_id = device_id
        self._attr_has_entity_name = True
        
        if native_unit == "boolean":
            self._attr_device_class = "enum"
            self._attr_options = ["on", "off"]
        elif native_unit == "timestamp":
            self._attr_device_class = "timestamp"

    @property
    def native_value(self) -> str | bool | None:
        watch = self.coordinator.data.watches.get(self._uuid, {})
        value = watch.get(self._key)
        
        if self._key in ["paused", "notification_muted"]:
            return "on" if value else "off"
        elif isinstance(value, (int, float)):
            # Timestamp Unix
            return value
        return str(value) if value else None
