"""Config flow for ChangeDetection.io integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ChangeDetectorClient, ChangeDetectorApiError
from .const import DOMAIN, CONF_BASE_URL, CONF_API_KEY


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    client = ChangeDetectorClient(data[CONF_BASE_URL], data[CONF_API_KEY], session)
    
    try:
        systeminfo = await client.systeminfo()
    except ChangeDetectorApiError as err:
        raise ValueError(f"Cannot connect: {err}") from err
    
    return {"title": f"ChangeDetection.io ({systeminfo.get('watch_count', 0)} watches)"}


class ChangeDetectorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ChangeDetection.io."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_BASE_URL])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default="http://localhost:5000"): str,
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
