"""Config flow for AquaForte DM-VARIO integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, CONF_HOST, CONF_NAME, DOMAIN, TCP_PORT
from .protocol import AquaForteProtocol, discover_devices

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default="AquaForte Pumpe"): str,
    }
)


async def _test_connection(host: str) -> str:
    """Try to connect and login. Returns device passcode (proves auth works)."""
    proto = AquaForteProtocol(host)
    try:
        await proto.connect()
        passcode = await proto.get_passcode()
        success = await proto.login(passcode)
        if not success:
            raise ValueError("Login rejected")
        return passcode
    finally:
        await proto.disconnect()


class AquaForteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AquaForte DM-VARIO."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show discovery or manual entry options."""
        # Try UDP discovery first to offer device list
        if not self._discovered_devices:
            try:
                devices = await discover_devices()
                self._discovered_devices = [
                    {"host": d.host, "name": d.device_id, "device_id": d.device_id}
                    for d in devices
                ]
            except Exception as exc:
                _LOGGER.debug("UDP discovery failed: %s", exc)

        if self._discovered_devices:
            return await self.async_step_pick_device()

        return await self.async_step_manual()

    async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let user pick from discovered devices."""
        errors: dict[str, str] = {}

        device_options = {
            d["host"]: f"{d['name']} ({d['host']})"
            for d in self._discovered_devices
        }
        device_options["__manual__"] = "Manuelle IP-Eingabe"

        if user_input is not None:
            chosen = user_input["device"]
            if chosen == "__manual__":
                return await self.async_step_manual()
            # Find the selected device
            device = next((d for d in self._discovered_devices if d["host"] == chosen), None)
            if device:
                return await self._async_create_entry(
                    host=device["host"],
                    device_id=device["device_id"],
                    name=device["name"],
                    errors=errors,
                )

        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema(
                {vol.Required("device"): vol.In(device_options)}
            ),
            errors=errors,
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manual IP address entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = user_input.get(CONF_NAME, "AquaForte Pumpe")

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            try:
                await _test_connection(host)
            except TimeoutError:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_auth"
            except Exception as exc:
                _LOGGER.exception("Unexpected error connecting to %s: %s", host, exc)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=name,
                    data={CONF_HOST: host, CONF_DEVICE_ID: host, CONF_NAME: name},
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_create_entry(
        self,
        host: str,
        device_id: str,
        name: str,
        errors: dict[str, str],
    ) -> ConfigFlowResult:
        """Validate connection and create entry."""
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        try:
            await _test_connection(host)
        except TimeoutError:
            errors["base"] = "cannot_connect"
        except ValueError:
            errors["base"] = "invalid_auth"
        except Exception as exc:
            _LOGGER.exception("Unexpected error: %s", exc)
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(
                title=name,
                data={CONF_HOST: host, CONF_DEVICE_ID: device_id, CONF_NAME: name},
            )

        return await self.async_step_manual()
