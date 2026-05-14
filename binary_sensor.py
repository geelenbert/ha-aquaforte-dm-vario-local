"""AquaForte binary sensors: 7 fault indicators (diagnostic)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import FAULT_ENDPOINTS, EndpointDef
from .coordinator import AquaForteCoordinator

_FAULT_NAMES = {
    "Fault_Overcurrent":  "Überstrom",
    "Fault_Overvoltage":  "Überspannung",
    "Fault_OverTemp":     "Übertemperatur",
    "Fault_Undervoltage": "Unterspannung",
    "Fault_LockedRotor":  "Rotor blockiert",
    "Fault_NoLoad":       "Kein Last",
    "Fault_UART":         "Verbindungsfehler",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AquaForteCoordinator = entry.runtime_data
    async_add_entities([
        AquaForteFaultSensor(coordinator, ep)
        for ep in FAULT_ENDPOINTS
    ])


class AquaForteFaultSensor(CoordinatorEntity[AquaForteCoordinator], BinarySensorEntity):

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: AquaForteCoordinator, endpoint: EndpointDef) -> None:
        super().__init__(coordinator)
        self._endpoint = endpoint
        self._attr_name = _FAULT_NAMES.get(endpoint.name, endpoint.name)
        self._attr_unique_id = f"{coordinator.device_id}_{endpoint.name}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._endpoint.name)
