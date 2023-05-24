"""The Coordinator for Spot-Hinta.fi."""
from __future__ import annotations

from typing import NamedTuple

from spothinta_api import Electricity, SpotHinta, SpotHintaConnectionError
from spothinta_api.const import Region

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, SCAN_INTERVAL


class SpotHintaData(NamedTuple):
    """Class for defining data in dict."""

    energy_today: Electricity


class SpotHintaDataUpdateCoordinator(DataUpdateCoordinator[SpotHintaData]):
    """Class to manage fetching Spot-Hinta.fi data from single endpoint."""

    config_entry: ConfigEntry
    region: Region

    def __init__(self, hass: HomeAssistant, region: Region) -> None:
        """Initialize global Spot-Hinta.fi data updater."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{region.name}",
            update_interval=SCAN_INTERVAL,
        )

        self.region = region
        self.spothinta = SpotHinta(session=async_get_clientsession(hass))

    async def _async_update_data(self) -> SpotHintaData:
        """Fetch data from spot-hinta.fi."""

        try:
            energy_today = await self.spothinta.energy_prices(self.region)
        except SpotHintaConnectionError as err:
            raise UpdateFailed("Error communicating with Spot-Hinta.fi API") from err

        return SpotHintaData(
            energy_today=energy_today,
        )
