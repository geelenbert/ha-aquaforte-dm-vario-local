"""AquaForte number entities: Motor_Speed and FeedTime."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import EP_FEED_TIME, EP_MOTOR_SPEED
from .coordinator import AquaForteCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AquaForteCoordinator = entry.runtime_data
    async_add_entities([
        AquaForteNumber(
            coordinator, EP_MOTOR_SPEED,
            name="Pumpengeschwindigkeit",
            icon="mdi:speedometer",
            native_min=0, native_max=100, native_step=1,
            native_unit="%",
            mode=NumberMode.SLIDER,
        ),
        AquaForteNumber(
            coordinator, EP_FEED_TIME,
            name="Fütterungsdauer",
            icon="mdi:timer",
            native_min=1, native_max=60, native_step=1,
            native_unit="s",
            mode=NumberMode.BOX,
        ),
    ])


class AquaForteNumber(CoordinatorEntity[AquaForteCoordinator], NumberEntity):

    _attr_has_entity_name = True

    def __init__(self, coordinator, endpoint, name, icon, native_min, native_max, native_step, native_unit, mode) -> None:
        super().__init__(coordinator)
        self._endpoint = endpoint
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_min_value = native_min
        self._attr_native_max_value = native_max
        self._attr_native_step = native_step
        self._attr_native_unit_of_measurement = native_unit
        self._attr_mode = mode
        self._attr_unique_id = f"{coordinator.device_id}_{endpoint.name}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(self._endpoint.name)
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.set_value(self._endpoint, int(value))
