"""Tests for the sensors provided by the spothinta integration."""

from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from spothinta_api import SpotHintaNoDataError

from custom_components.spothinta.const import DOMAIN
from homeassistant.components.homeassistant import SERVICE_UPDATE_ENTITY
from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    CURRENCY_EURO,
    STATE_UNKNOWN,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component


@pytest.mark.freeze_time("2023-01-19 15:00:00")
async def test_energy_usage_today(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test the Spothinta - Energy usage sensors."""
    entry_id = init_integration.entry_id
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    # Current usage energy price sensor
    state = hass.states.get("sensor.spothinta_fi_today_energy_usage_current_hour_price")
    entry = entity_registry.async_get(
        "sensor.spothinta_fi_today_energy_usage_current_hour_price"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_usage_current_hour_price"
    assert state.state == "0.22541"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Usage Current hour"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Average usage energy price sensor
    state = hass.states.get("sensor.spothinta_today_energy_usage_average_price")
    entry = entity_registry.async_get(
        "sensor.spothinta_today_energy_usage_average_price"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_usage_average_price"
    assert state.state == "0.17665"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Usage Average - today"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Highest usage energy price sensor
    state = hass.states.get("sensor.spothinta_today_energy_usage_max_price")
    entry = entity_registry.async_get("sensor.spothinta_today_energy_usage_max_price")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_usage_max_price"
    assert state.state == "0.24677"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Usage Highest price - today"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Highest usage price time sensor
    state = hass.states.get("sensor.spothinta_today_energy_usage_highest_price_time")
    entry = entity_registry.async_get(
        "sensor.spothinta_today_energy_usage_highest_price_time"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_usage_highest_price_time"
    assert state.state == "2023-01-19T16:00:00+00:00"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Usage Time of highest price - today"
    )
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP
    assert ATTR_ICON not in state.attributes

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}_today_energy_usage")}
    assert device_entry.manufacturer == "spothinta"
    assert device_entry.name == "Energy market price - Usage"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert not device_entry.model
    assert not device_entry.sw_version

    # Usage hours priced equal or lower sensor
    state = hass.states.get(
        "sensor.spothinta_today_energy_usage_hours_priced_equal_or_lower"
    )
    entry = entity_registry.async_get(
        "sensor.spothinta_today_energy_usage_hours_priced_equal_or_lower"
    )
    assert entry
    assert state
    assert (
        entry.unique_id == f"{entry_id}_today_energy_usage_hours_priced_equal_or_lower"
    )
    assert state.state == "21"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Usage Hours priced equal or lower than current - today"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes


@pytest.mark.freeze_time("2023-01-19 15:00:00")
async def test_energy_return_today(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test the spothinta - Energy return sensors."""
    entry_id = init_integration.entry_id
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    # Current return energy price sensor
    state = hass.states.get("sensor.spothinta_today_energy_return_current_hour_price")
    entry = entity_registry.async_get(
        "sensor.spothinta_today_energy_return_current_hour_price"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_return_current_hour_price"
    assert state.state == "0.18629"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Current hour"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Average return energy price sensor
    state = hass.states.get("sensor.spothinta_today_energy_return_average_price")
    entry = entity_registry.async_get(
        "sensor.spothinta_today_energy_return_average_price"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_return_average_price"
    assert state.state == "0.14599"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Average - today"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Highest return energy price sensor
    state = hass.states.get("sensor.spothinta_today_energy_return_max_price")
    entry = entity_registry.async_get("sensor.spothinta_today_energy_return_max_price")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_return_max_price"
    assert state.state == "0.20394"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Highest price - today"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Highest return price time sensor
    state = hass.states.get("sensor.spothinta_today_energy_return_highest_price_time")
    entry = entity_registry.async_get(
        "sensor.spothinta_today_energy_return_highest_price_time"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_return_highest_price_time"
    assert state.state == "2023-01-19T16:00:00+00:00"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Time of highest price - today"
    )
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP
    assert ATTR_ICON not in state.attributes

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}_today_energy_return")}
    assert device_entry.manufacturer == "spothinta"
    assert device_entry.name == "Energy market price - Return"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert not device_entry.model
    assert not device_entry.sw_version

    # Return hours priced equal or higher sensor
    state = hass.states.get(
        "sensor.spothinta_today_energy_return_hours_priced_equal_or_higher"
    )
    entry = entity_registry.async_get(
        "sensor.spothinta_today_energy_return_hours_priced_equal_or_higher"
    )
    assert entry
    assert state
    assert (
        entry.unique_id
        == f"{entry_id}_today_energy_return_hours_priced_equal_or_higher"
    )
    assert state.state == "3"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Hours priced equal or higher than current - today"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes


@pytest.mark.freeze_time("2023-05-08 15:00:00")
async def test_no_energy_today(
    hass: HomeAssistant, mock_spothinta: MagicMock, init_integration: MockConfigEntry
) -> None:
    """Test the spothinta - No energy data available."""
    await async_setup_component(hass, "homeassistant", {})

    mock_spothinta.energy_prices.side_effect = SpotHintaNoDataError

    await hass.services.async_call(
        "homeassistant",
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: "sensor.spothinta_fi_today_energy_usage_current_hour_price"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.spothinta_fi_today_energy_usage_current_hour_price")
    assert state
    assert state.state == STATE_UNKNOWN
