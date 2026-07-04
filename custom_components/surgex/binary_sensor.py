"""Binary sensor entities for SurgeX devices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SurgeXCoordinator
from .entity import common_attributes, device_info


@dataclass(frozen=True, kw_only=True)
class SurgeXBinarySensorDescription(BinarySensorEntityDescription):
    """Description for a SurgeX binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[SurgeXBinarySensorDescription, ...] = (
    SurgeXBinarySensorDescription(
        key="connected",
        translation_key="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data.get("connected"),
    ),
    SurgeXBinarySensorDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: _is_running(data),
    ),
    SurgeXBinarySensorDescription(
        key="shutdown",
        translation_key="shutdown",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.get("active_state") == "Shutdown",
    ),
    SurgeXBinarySensorDescription(
        key="alarm",
        translation_key="alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: bool(data.get("alarm_severity") or data.get("alarms")),
    ),
    SurgeXBinarySensorDescription(
        key="surge_protection",
        translation_key="surge_protection",
        device_class=BinarySensorDeviceClass.SAFETY,
        value_fn=lambda data: _surge_good(data),
    ),
    SurgeXBinarySensorDescription(
        key="wiring_fault",
        translation_key="wiring_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.get("wiring_fault"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SurgeX binary sensors."""
    coordinator: SurgeXCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SurgeXBinarySensor(coordinator, description)
            for description in BINARY_SENSOR_DESCRIPTIONS
        ]
    )


class SurgeXBinarySensor(CoordinatorEntity[SurgeXCoordinator], BinarySensorEntity):
    """A SurgeX binary sensor."""

    _attr_has_entity_name = True

    entity_description: SurgeXBinarySensorDescription

    def __init__(
        self,
        coordinator: SurgeXCoordinator,
        description: SurgeXBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        identity = coordinator.device_identity
        prefix = str(identity.get("serial") or identity.get("mac") or "surgex").lower()
        self._attr_unique_id = f"{prefix}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return binary sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def device_info(self):
        """Return device information."""
        return device_info(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return common_attributes(self.coordinator)


def _surge_good(data: dict[str, Any]) -> bool | None:
    """Return true when surge protection reports healthy."""
    if data.get("surge_good") is not None:
        return data.get("surge_good")
    gpio_value = data.get("gpio_surge_good")
    if gpio_value is None:
        return None
    try:
        return int(gpio_value) == 0
    except (TypeError, ValueError):
        return None


def _is_running(data: dict[str, Any]) -> bool | None:
    """Return whether the device is in normal running state."""
    active_state = data.get("active_state")
    if active_state is not None:
        return active_state == "Running"
    return data.get("connected")
