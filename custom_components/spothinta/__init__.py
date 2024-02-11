"""The spot-hinta.fi integration."""

from __future__ import annotations

from spothinta_api.const import Region

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_REGION, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import SpotHintaDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up spot-hinta.fi from a config entry."""
    region = entry.data[CONF_REGION]
    if isinstance(region, int):
        region = Region(region)

    coordinator = SpotHintaDataUpdateCoordinator(hass, region)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        await coordinator.spothinta.close()
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload spot-hinta.fi config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: SpotHintaDataUpdateCoordinator = hass.data[DOMAIN].pop(
            entry.entry_id
        )
        if coordinator.future_update:
            coordinator.future_update()

    return unload_ok
