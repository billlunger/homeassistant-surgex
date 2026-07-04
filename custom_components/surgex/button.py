"""Button entities for SurgeX commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SurgeXCoordinator
from .entity import device_info


@dataclass(frozen=True, kw_only=True)
class SurgeXButtonDescription(ButtonEntityDescription):
    """Description for a SurgeX command button."""

    press_fn: Callable[[SurgeXCoordinator], Awaitable[None]]


DEVICE_BUTTONS: tuple[SurgeXButtonDescription, ...] = (
    SurgeXButtonDescription(
        key="enter_shutdown_state",
        translation_key="enter_shutdown_state",
        press_fn=lambda coordinator: coordinator.api.async_enter_shutdown_state(),
    ),
    SurgeXButtonDescription(
        key="clear_shutdown_state",
        translation_key="clear_shutdown_state",
        press_fn=lambda coordinator: coordinator.api.async_clear_shutdown_state(),
    ),
    SurgeXButtonDescription(
        key="reset_energy_usage",
        translation_key="reset_energy_usage",
        press_fn=lambda coordinator: coordinator.api.async_reset_energy_usage(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SurgeX command buttons."""
    coordinator: SurgeXCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = [
        SurgeXCommandButton(coordinator, description) for description in DEVICE_BUTTONS
    ]
    for outlet_id, outlet in coordinator.data.get("outlets", {}).items():
        entities.append(SurgeXRebootButton(coordinator, outlet_id, outlet.get("name")))
    async_add_entities(entities)


class SurgeXCommandButton(CoordinatorEntity[SurgeXCoordinator], ButtonEntity):
    """A device-level SurgeX command button."""

    _attr_has_entity_name = True

    entity_description: SurgeXButtonDescription

    def __init__(
        self,
        coordinator: SurgeXCoordinator,
        description: SurgeXButtonDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        identity = coordinator.device_identity
        prefix = str(identity.get("serial") or identity.get("mac") or "surgex").lower()
        self._attr_unique_id = f"{prefix}_{description.key}"

    @property
    def device_info(self):
        """Return device information."""
        return device_info(self.coordinator)

    async def async_press(self) -> None:
        """Press the command button."""
        await self.entity_description.press_fn(self.coordinator)
        await self.coordinator.async_request_refresh()


class SurgeXRebootButton(CoordinatorEntity[SurgeXCoordinator], ButtonEntity):
    """An outlet reboot button."""

    _attr_has_entity_name = True
    _attr_translation_key = "reboot_outlet"

    def __init__(
        self,
        coordinator: SurgeXCoordinator,
        outlet_id: str,
        outlet_name: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._outlet_id = outlet_id
        identity = coordinator.device_identity
        prefix = str(identity.get("serial") or identity.get("mac") or "surgex").lower()
        self._attr_unique_id = (
            f"{prefix}_reboot_{outlet_id.strip('/').replace('/', '_')}"
        )
        self._attr_name = f"Reboot {outlet_name or outlet_id}"

    @property
    def device_info(self):
        """Return device information."""
        return device_info(self.coordinator)

    async def async_press(self) -> None:
        """Reboot the outlet."""
        await self.coordinator.api.async_reboot(self._outlet_id)
        await self.coordinator.async_request_refresh()
