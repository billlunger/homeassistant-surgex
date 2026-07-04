"""Sensor entities for SurgeX devices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SurgeXCoordinator
from .entity import common_attributes, device_info


@dataclass(frozen=True, kw_only=True)
class SurgeXSensorDescription(SensorEntityDescription):
    """Description for a SurgeX sensor."""

    source_keys: tuple[str, ...]


SENSOR_DESCRIPTIONS: tuple[SurgeXSensorDescription, ...] = (
    SurgeXSensorDescription(
        key="power",
        name="Power",
        translation_key="power",
        source_keys=("power", "Power"),
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SurgeXSensorDescription(
        key="current",
        name="Current",
        translation_key="current",
        source_keys=("current", "CurrentRmsLine", "CurrentRmsLineAvg"),
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SurgeXSensorDescription(
        key="voltage",
        name="Line-neutral voltage",
        translation_key="voltage",
        source_keys=("voltageLN", "line1Line2", "VoltageRmsLine", "VoltageRmsLineAvg"),
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SurgeXSensorDescription(
        key="neutral_ground_voltage",
        name="Neutral-ground voltage",
        translation_key="neutral_ground_voltage",
        source_keys=("voltageNG", "line2Ground", "VoltageRmsNG", "VoltageRmsNGAvg"),
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SurgeXSensorDescription(
        key="frequency",
        name="Frequency",
        translation_key="frequency",
        source_keys=("frequency", "FrequencyAvg"),
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SurgeXSensorDescription(
        key="energy_usage",
        name="Energy usage",
        translation_key="energy_usage",
        source_keys=("energyUsage", "EnergyUsed", "EnergyUsedDelta"),
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SurgeXSensorDescription(
        key="temperature",
        name="Temperature",
        translation_key="temperature",
        source_keys=("temperature", "TempInternal", "TempInternalAvg"),
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SurgeXSensorDescription(
        key="power_factor",
        name="Power factor",
        translation_key="power_factor",
        source_keys=("pf", "PowerFactor", "PowerFactorInd"),
        icon="mdi:sine-wave",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SurgeXSensorDescription(
        key="crest_factor",
        name="Line-neutral crest factor",
        translation_key="crest_factor",
        source_keys=("crestFactor", "CrestFactorLNAvg"),
        icon="mdi:sine-wave",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SurgeXSensorDescription(
        key="current_crest_factor",
        name="Current crest factor",
        translation_key="current_crest_factor",
        source_keys=("crestFactorNI", "CrestFactorCurrentAvg"),
        icon="mdi:sine-wave",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SurgeX sensors."""
    coordinator: SurgeXCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        SurgeXSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
        if _measurement_value(coordinator.data.get("measurements", {}), description)
        is not None
    ]
    async_add_entities(entities)


class SurgeXSensor(CoordinatorEntity[SurgeXCoordinator], SensorEntity):
    """A SurgeX monitoring sensor."""

    _attr_has_entity_name = True

    entity_description: SurgeXSensorDescription

    def __init__(
        self,
        coordinator: SurgeXCoordinator,
        description: SurgeXSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{_device_unique_prefix(coordinator)}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return _measurement_value(
            self.coordinator.data.get("measurements", {}),
            self.entity_description,
        )

    @property
    def device_info(self):
        """Return device information."""
        return device_info(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = common_attributes(self.coordinator)
        if self.entity_description.key == "energy_usage":
            attrs["energy_usage_time"] = self.coordinator.data.get("measurements", {}).get(
                "energyUsageTime"
            )
        return attrs


def _measurement_value(
    measurements: dict[str, Any],
    description: SurgeXSensorDescription,
) -> Any:
    """Return the first available measurement value for this description."""
    for key in description.source_keys:
        value = measurements.get(key)
        if value is not None:
            return value
    return None


def _device_unique_prefix(coordinator: SurgeXCoordinator) -> str:
    """Return stable unique id prefix."""
    identity = coordinator.device_identity
    return str(identity.get("serial") or identity.get("mac") or "surgex").lower()
