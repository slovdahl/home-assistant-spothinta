"""The spot-hinta.fi integration."""
from __future__ import annotations

import logging

from spothinta_api.const import Region

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_REGION, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from spothinta.config_flow import SpotHintaFlowHandler

from .const import DOMAIN
from .coordinator import SpotHintaDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


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


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating configuration from version %s.%s", config_entry.version, config_entry.minor_version)

    if config_entry.version > SpotHintaFlowHandler.VERSION:
        # This means the user has downgraded from a future version
        return False

    if config_entry.version == 1:
        entity_registry = er.async_get(hass)
        entities: list[er.RegistryEntry] = er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )

        for entity in entities:
            if entity.entity_id.endswith("_current_hour_price"):
                new_unique_id = entity.unique_id.replace("_current_hour_price", "_current_price")
                new_entity_id = entity.entity_id.replace("_current_hour_price", "_current_price")
                entity_registry.async_update_entity(
                    entity_id=entity.entity_id,
                    new_unique_id=new_unique_id,
                    new_entity_id=new_entity_id,
                    original_name="Current price",
                )
                _LOGGER.debug(
                    "Migrated entity '%s' to '%s' and new unique_id '%s'",
                    entity.entity_id,
                    new_entity_id,
                    new_unique_id,
                )
            elif entity.entity_id.endswith("_next_hour_price"):
                new_unique_id = entity.unique_id.replace("_next_hour_price", "_next_price")
                new_entity_id = entity.entity_id.replace("_next_hour_price", "_next_price")
                entity_registry.async_update_entity(
                    entity_id=entity.entity_id,
                    new_unique_id=new_unique_id,
                    new_entity_id=new_entity_id,
                    original_name="Next price",
                )
                _LOGGER.debug(
                    "Migrated entity '%s' to '%s' and new unique_id '%s'",
                    entity.entity_id,
                    new_entity_id,
                    new_unique_id,
                )

        hass.config_entries.async_update_entry(
            config_entry, minor_version=1, version=2
        )

        return True

    return True
