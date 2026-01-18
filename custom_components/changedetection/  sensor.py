from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ATTR_WATCHES
from .coordinator import ChangeDetectionCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ChangeDetectionCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SensorEntity] = [
        ChangeDetectionWatchesSensor(coordinator, entry),
        ChangeDetectionSystemInfoSensor(coordinator, entry, "watch_count", "Watches count"),
        ChangeDetectionSystemInfoSensor(coordinator, entry, "tag_count", "Tags count"),
        ChangeDetectionSystemInfoSensor(coordinator, entry, "uptime", "Uptime"),
        ChangeDetectionSystemInfoSensor(coordinator, entry, "version", "Version"),
    ]
    async_add_entities(entities)


class ChangeDetectionWatchesSensor(CoordinatorEntity[ChangeDetectionCoordinator], SensorEntity):
    _attr_name = "ChangeDetection Watches"
    _attr_icon = "mdi:web"

    def __init__(self, coordinator: ChangeDetectionCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_watches"

    @property
    def native_value(self):
        # valore “sintetico”: numero di watch
        return len(self.coordinator.data.watches or {})

    @property
    def extra_state_attributes(self):
        # GET /api/v1/watch ritorna un dict indicizzato per uuid con campi come title, link, paused, last_checked, last_changed, ecc. [page:1]
        return {ATTR_WATCHES: self.coordinator.data.watches}


class ChangeDetectionSystemInfoSensor(CoordinatorEntity[ChangeDetectionCoordinator], SensorEntity):
    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator: ChangeDetectionCoordinator, entry: ConfigEntry, key: str, name: str) -> None:
        super().__init__(coordinator)
        self.key = key
        self._attr_name = f"ChangeDetection {name}"
        self._attr_unique_id = f"{entry.entry_id}_systeminfo_{key}"

    @property
    def native_value(self):
        # systeminfo contiene watch_count, tag_count, uptime, version, ecc. [page:1]
        return (self.coordinator.data.systeminfo or {}).get(self.key)
