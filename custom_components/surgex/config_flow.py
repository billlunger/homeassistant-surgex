"""Config flow for SurgeX."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SurgeXApi, SurgeXAuthError, SurgeXError
from .const import (
    CONF_BASE_URL,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)


class SurgeXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SurgeX."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = _base_url(user_input)
            api = SurgeXApi(
                async_get_clientsession(self.hass),
                base_url,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                status = await api.async_current_status()
            except SurgeXAuthError:
                errors["base"] = "invalid_auth"
            except SurgeXError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                serial = status.get("serial")
                mac = _first_mac(status.get("MAC"))
                unique_id = serial or mac or user_input[CONF_HOST]
                await self.async_set_unique_id(str(unique_id).lower())
                self._abort_if_unique_id_configured()
                title = status.get("model") or DEFAULT_NAME
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_SSL: user_input[CONF_SSL],
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_SSL, default=False): bool,
                    vol.Required(CONF_USERNAME, default="admin"): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )


def _base_url(user_input: dict[str, Any]) -> str:
    """Build a base URL from form input."""
    scheme = "https" if user_input[CONF_SSL] else "http"
    return f"{scheme}://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"


def _first_mac(value: Any) -> str | None:
    """Return a MAC address from either string or list payloads."""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        return str(value[0])
    return None
