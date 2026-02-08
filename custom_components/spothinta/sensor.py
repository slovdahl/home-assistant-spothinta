"""Support for Spot-Hinta.fi sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO, EntityCategory, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpotHintaData, SpotHintaDataUpdateCoordinator


@dataclass(frozen=True)
class SpotHintaSensorEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[SpotHintaData], float | datetime | None]
    service_type: str


@dataclass(frozen=True)
class SpotHintaSensorEntityDescription(
    SensorEntityDescription, SpotHintaSensorEntityDescriptionMixin
):
    """Describes Spot-Hinta.fi sensor entity."""


SENSORS: tuple[SpotHintaSensorEntityDescription, ...] = (
    SpotHintaSensorEntityDescription(
        key="current_price",
        name="Current price",
        service_type="energy",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
        value_fn=lambda data: (
            data.energy_today.current_price if data.energy_today else None
        ),
    ),
    SpotHintaSensorEntityDescription(
        key="next_price",
        name="Next price",
        service_type="energy",
        native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
        value_fn=lambda data: data.energy_today.price_at_time(
            data.energy_today.now_in_timezone() + timedelta(minutes=15)
        ),
    ),
    SpotHintaSensorEntityDescription(
        key="average_price_today",
        name="Average - Today",
        service_type="energy",
        native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
        value_fn=lambda data: data.energy_today.average_price_today,
    ),
    SpotHintaSensorEntityDescription(
        key="average_price_tomorrow",
        name="Average - Tomorrow",
        service_type="energy",
        native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
        value_fn=lambda data: data.energy_today.average_price_tomorrow,
    ),
    SpotHintaSensorEntityDescription(
        key="max_price_today",
        name="Highest price - Today",
        service_type="energy",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
        value_fn=lambda data: data.energy_today.highest_price_today,
    ),
    SpotHintaSensorEntityDescription(
        key="max_price_tomorrow",
        name="Highest price - Tomorrow",
        service_type="energy",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
        value_fn=lambda data: data.energy_today.highest_price_tomorrow,
    ),
    SpotHintaSensorEntityDescription(
        key="min_price_today",
        name="Lowest price - Today",
        service_type="energy",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
        value_fn=lambda data: data.energy_today.lowest_price_today,
    ),
    SpotHintaSensorEntityDescription(
        key="min_price_tomorrow",
        name="Lowest price - Tomorrow",
        service_type="energy",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
        value_fn=lambda data: data.energy_today.lowest_price_tomorrow,
    ),
    SpotHintaSensorEntityDescription(
        key="highest_price_time_today",
        name="Time of highest price - Today",
        service_type="energy",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.energy_today.highest_price_time_today,
    ),
    SpotHintaSensorEntityDescription(
        key="highest_price_time_tomorrow",
        name="Time of highest price - Tomorrow",
        service_type="energy",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.energy_today.highest_price_time_tomorrow,
    ),
    SpotHintaSensorEntityDescription(
        key="lowest_price_time_today",
        name="Time of lowest price - Today",
        service_type="energy",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.energy_today.lowest_price_time_today,
    ),
    SpotHintaSensorEntityDescription(
        key="lowest_price_time_tomorrow",
        name="Time of lowest price - Tomorrow",
        service_type="energy",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.energy_today.lowest_price_time_tomorrow,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Spot-Hinta.fi sensors based on a config entry."""
    coordinator: SpotHintaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SpotHintaSensorEntity(coordinator=coordinator, description=description)
        for description in SENSORS
    )


class SpotHintaSensorEntity(
    CoordinatorEntity[SpotHintaDataUpdateCoordinator], SensorEntity
):
    """Defines a Spot-Hinta.fi sensor."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by Spot-Hinta.fi"
    entity_description: SpotHintaSensorEntityDescription

    def __init__(
        self,
        *,
        coordinator: SpotHintaDataUpdateCoordinator,
        description: SpotHintaSensorEntityDescription,
    ) -> None:
        """Initialize Spot-Hinta.fi sensor."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self.entity_id = f"{SENSOR_DOMAIN}.{DOMAIN}_{coordinator.region.name}_{description.service_type}_{description.key}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.service_type}_{description.key}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={
                (
                    DOMAIN,
                    f"{coordinator.config_entry.entry_id}_{description.service_type}",
                )
            },
            configuration_url="https://spot-hinta.fi",
            manufacturer="Spot-Hinta.fi",
            name=f"Energy spot prices for {coordinator.region.name}",
        )

    @property
    def native_value(self) -> float | datetime | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
