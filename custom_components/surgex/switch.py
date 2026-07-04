"""Switch entities for SurgeX outlets and outlet groups."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SurgeXCoordinator
from .entity import device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SurgeX outlet switches."""
    coordinator: SurgeXCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SurgeXOutletSwitch] = []
    for outlet_id, outlet in coordinator.data.get("outlets", {}).items():
        entities.append(SurgeXOutletSwitch(coordinator, outlet_id, outlet, False))
    for group_id, group in coordinator.data.get("groups", {}).items():
        entities.append(SurgeXOutletSwitch(coordinator, group_id, group, True))
    async_add_entities(entities)


class SurgeXOutletSwitch(CoordinatorEntity[SurgeXCoordinator], SwitchEntity):
    """A controllable SurgeX outlet or outlet group."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SurgeXCoordinator,
        outlet_id: str,
        initial: dict[str, Any],
        is_group: bool,
    ) -> None:
        super().__init__(coordinator)
        self._outlet_id = outlet_id
        self._is_group = is_group
        identity = coordinator.device_identity
        prefix = str(identity.get("serial") or identity.get("mac") or "surgex").lower()
        kind = "group" if is_group else "outlet"
        self._attr_unique_id = f"{prefix}_{kind}_{outlet_id.strip('/').replace('/', '_')}"
        self._attr_translation_key = "outlet_group" if is_group else "outlet"
        self._attr_name = initial.get("name") or initial.get("physicalName") or outlet_id

    @property
    def is_on(self) -> bool | None:
        """Return true if outlet is on."""
        state = self._item.get("state")
        if state is None:
            state = self._item.get("status")
        if isinstance(state, bool):
            return state
        try:
            return int(state) == 1
        except (TypeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        """Return if outlet is available."""
        connected = self._item.get("Connected")
        return super().available and bool(self._item) and connected is not False

    @property
    def device_info(self):
        """Return device information."""
        return device_info(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        item = self._item
        return {
            "id": self._outlet_id,
            "device_type": item.get("deviceType"),
            "physical_name": item.get("physicalName"),
            "status": item.get("status"),
            "last_state": item.get("lastState"),
            "reboot_time": item.get("rebootTime"),
            "alarm_severity": item.get("AlarmSeverity"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the outlet on."""
        await self.coordinator.api.async_power_on(self._outlet_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the outlet off."""
        await self.coordinator.api.async_power_off(self._outlet_id)
        await self.coordinator.async_request_refresh()

    @property
    def _item(self) -> dict[str, Any]:
        """Return current outlet or group payload."""
        key = "groups" if self._is_group else "outlets"
        return self.coordinator.data.get(key, {}).get(self._outlet_id, {})
