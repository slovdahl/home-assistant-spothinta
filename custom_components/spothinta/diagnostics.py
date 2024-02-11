"""Diagnostics support for Spot-Hinta.fi."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_REGION
from homeassistant.core import HomeAssistant

from . import SpotHintaDataUpdateCoordinator
from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: SpotHintaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry": {
            "title": entry.title,
            "region": entry.data[CONF_REGION],
        },
        "energy": {
            "current_hour_price": coordinator.data.energy_today.current_price,
            "next_hour_price": coordinator.data.energy_today.price_at_time(
                coordinator.data.energy_today.now_in_timezone() + timedelta(hours=1)
            ),
            "average_price": coordinator.data.energy_today.average_price_today,
            "max_price": coordinator.data.energy_today.highest_price_today,
            "min_price": coordinator.data.energy_today.lowest_price_today,
            "highest_price_time": coordinator.data.energy_today.highest_price_time_today,
            "lowest_price_time": coordinator.data.energy_today.lowest_price_time_today,
        },
    }
