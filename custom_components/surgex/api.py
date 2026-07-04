"""Async client for SurgeX v1 REST APIs."""

from __future__ import annotations

import json
from typing import Any

from aiohttp import BasicAuth, ClientError, ClientResponseError, ClientSession, ClientTimeout

REQUEST_TIMEOUT = ClientTimeout(total=20)


class SurgeXError(Exception):
    """Base API error."""


class SurgeXAuthError(SurgeXError):
    """Authentication failed."""


class SurgeXApi:
    """Small wrapper around SurgeX local REST endpoints."""

    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._auth = BasicAuth(username, password)

    async def async_who_are_you(self) -> dict[str, Any]:
        """Return device identity information."""
        payload = await self._request("GET", "WhoAreYou")
        if isinstance(payload, dict):
            return payload
        raise SurgeXError("Unexpected WhoAreYou response")

    async def async_current_status(self) -> dict[str, Any]:
        """Return the current device and outlet status."""
        payload = await self._request("GET", "currentStatus")
        if isinstance(payload, dict):
            return payload
        raise SurgeXError("Unexpected currentStatus response")

    async def async_power_on(self, outlet_id: str) -> None:
        """Power on an outlet or outlet group."""
        await self._command(outlet_id, "PowerOn")

    async def async_power_off(self, outlet_id: str) -> None:
        """Power off an outlet or outlet group."""
        await self._command(outlet_id, "PowerOff")

    async def async_reboot(self, outlet_id: str) -> None:
        """Reboot an outlet or outlet group."""
        await self._command(outlet_id, "Reboot")

    async def async_enter_shutdown_state(self) -> None:
        """Enter device shutdown state."""
        await self._request("POST", "EnterShutdownState", json_body=[])

    async def async_clear_shutdown_state(self) -> None:
        """Clear device shutdown state."""
        await self._request("POST", "ClearShutdownState", json_body=[])

    async def async_reset_energy_usage(self, device_id: str = "1") -> None:
        """Reset energy usage counters."""
        await self._request("POST", f"{device_id}/ResetEnergyUsage", json_body=[])

    async def _command(self, outlet_id: str, command: str) -> None:
        """Run a documented outlet command."""
        path = f"{outlet_id.strip('/')}/{command}"
        await self._request("POST", path, json_body=[])

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
    ) -> Any:
        """Make an API request."""
        url = f"{self._base_url}/api/v1/{path.lstrip('/')}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "HomeAssistant-SurgeX/0.1",
        }
        kwargs: dict[str, Any] = {
            "auth": self._auth,
            "headers": headers,
            "timeout": REQUEST_TIMEOUT,
        }
        if json_body is not None:
            kwargs["json"] = json_body

        try:
            async with self._session.request(method, url, **kwargs) as response:
                body = await response.text()
                if response.status in (401, 403):
                    raise SurgeXAuthError(body)
                response.raise_for_status()
        except SurgeXAuthError:
            raise
        except ClientResponseError as err:
            raise SurgeXError(f"HTTP {err.status}: {err.message}") from err
        except ClientError as err:
            raise SurgeXError(str(err)) from err

        if not body:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError as err:
            raise SurgeXError("API returned non-JSON response") from err
