"""Data coordinator for SurgeX devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SurgeXApi, SurgeXAuthError, SurgeXError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SurgeXCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch SurgeX device state."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: SurgeXApi,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=config_entry,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest state from the API."""
        try:
            payload = await self.api.async_current_status()
        except SurgeXAuthError as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except SurgeXError as err:
            raise UpdateFailed(str(err)) from err
        return _parse_current_status(payload)

    @property
    def device_identity(self) -> dict[str, Any]:
        """Return the root device identity."""
        return self.data.get("identity", {}) if self.data else {}


def _parse_current_status(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize currentStatus payload for entities."""
    devices_raw = [item for item in payload.get("devices", []) if isinstance(item, dict)]
    root_device = devices_raw[0] if devices_raw else {}

    device_id = _clean_id(root_device.get("id") or "/1")
    identity = {
        "id": device_id,
        "name": (
            root_device.get("name")
            or payload.get("deviceName")
            or payload.get("model")
            or "SurgeX"
        ),
        "model": payload.get("model") or root_device.get("deviceType"),
        "serial": payload.get("serial"),
        "firmware": payload.get("firmware"),
        "manufacturer": "AMETEK SurgeX",
        "mac": _first_mac(payload.get("MAC")),
        "device_type": root_device.get("deviceType"),
    }

    outlets = _collect_children(devices_raw, "outlets")
    groups = _collect_children(devices_raw, "groups")
    measurements = _normalize_measurements(root_device.get("deviceMeasurements", {}))

    return {
        "raw": payload,
        "identity": identity,
        "active_state": payload.get("activeState"),
        "time": payload.get("time"),
        "temperature_units": payload.get("temperatureUnits"),
        "shutdown_requests": payload.get("shutdownRequests"),
        "input_state": root_device.get("inputState"),
        "connected": root_device.get("Connected"),
        "alarm_severity": root_device.get("AlarmSeverity"),
        "alarms": root_device.get("Alarms", []),
        "surge_good": measurements.get("surgeGood"),
        "gpio_surge_good": measurements.get("gpioSurgeGood"),
        "wiring_fault": root_device.get("wiringFault"),
        "measurements": measurements,
        "outlets": outlets,
        "groups": groups,
    }


def _collect_children(
    devices: list[dict[str, Any]],
    key: str,
) -> dict[str, dict[str, Any]]:
    """Collect outlet or group children from all physical devices."""
    children: dict[str, dict[str, Any]] = {}
    for device in devices:
        parent_id = _clean_id(device.get("id") or "/1")
        for child in device.get(key, []):
            if not isinstance(child, dict):
                continue
            child_id = _clean_id(child.get("id"))
            if not child_id:
                continue
            normalized = dict(child)
            normalized["_id"] = child_id
            normalized["_parent_id"] = parent_id
            children[child_id] = normalized
    return children


def _normalize_measurements(measurements: Any) -> dict[str, Any]:
    """Return a measurement dictionary."""
    return measurements if isinstance(measurements, dict) else {}


def _clean_id(value: Any) -> str:
    """Normalize documented ids such as /1/1 for unique ids and commands."""
    if value is None:
        return ""
    return str(value).strip()


def _first_mac(value: Any) -> str | None:
    """Return a MAC address from either string or list payloads."""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        return str(value[0])
    return None
