"""Shared entity helpers for SurgeX."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import SurgeXCoordinator


def device_info(coordinator: SurgeXCoordinator) -> DeviceInfo:
    """Return root SurgeX device information."""
    identity = coordinator.device_identity
    identifiers = {(DOMAIN, identity.get("serial") or identity.get("mac") or "device")}
    return DeviceInfo(
        identifiers=identifiers,
        manufacturer=identity.get("manufacturer") or "AMETEK SurgeX",
        name=identity.get("name") or "SurgeX",
        model=identity.get("model"),
        serial_number=identity.get("serial"),
        sw_version=identity.get("firmware"),
        configuration_url=coordinator.config_entry.data.get("base_url"),
    )


def common_attributes(coordinator: SurgeXCoordinator) -> dict[str, Any]:
    """Return common diagnostic attributes."""
    return {
        "active_state": coordinator.data.get("active_state"),
        "input_state": coordinator.data.get("input_state"),
        "alarm_severity": coordinator.data.get("alarm_severity"),
        "shutdown_requests": coordinator.data.get("shutdown_requests"),
        "device_time": coordinator.data.get("time"),
    }
