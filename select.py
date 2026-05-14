"""AquaForte select entity: AutoMode (Shutdown / Automatic / Feed)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import AUTOMODE_OPTIONS, EP_AUTO_MODE
from .coordinator import AquaForteCoordinator

_OPTION_LABELS = {
    "Shutdown":  "Aus",
    "Automatic": "Automatisch",
    "Feed":      "Fütterung",
}
_LABEL_TO_VALUE = {v: k for k, v in _OPTION_LABELS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AquaForteCoordinator = entry.runtime_data
    async_add_entities([AquaForteModeSelect(coordinator)])


class AquaForteModeSelect(CoordinatorEntity[AquaForteCoordinator], SelectEntity):

    _attr_has_entity_name = True
    _attr_name = "Betriebsmodus"
    _attr_icon = "mdi:cog"
    _attr_options = list(_OPTION_LABELS.values())

    def __init__(self, coordinator: AquaForteCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_{EP_AUTO_MODE.name}"
        self._attr_device_info = coordinator.device_info

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(EP_AUTO_MODE.name)
        return _OPTION_LABELS.get(raw)

    async def async_select_option(self, option: str) -> None:
        value = _LABEL_TO_VALUE.get(option, "Shutdown")
        await self.coordinator.set_value(EP_AUTO_MODE, value)
