"""The Coordinator for Spot-Hinta.fi."""
from __future__ import annotations

from datetime import timedelta
import logging
from random import randint
from typing import NamedTuple

from spothinta_api import Electricity, SpotHinta, SpotHintaConnectionError
from spothinta_api.const import Region

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import DOMAIN, LOGGER

_LOGGER = logging.getLogger(__name__)


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
        )

        self.future_refresh: CALLBACK_TYPE | None = None
        self.region = region
        self.spothinta = SpotHinta(session=async_get_clientsession(hass))

    async def async_request_update(self, *_) -> None:
        """Request update from coordinator."""
        await self.async_request_refresh()

    async def _async_update_data(self) -> SpotHintaData:
        """Fetch data from spot-hinta.fi."""

        now = dt_util.utcnow()

        try:
            energy_prices = await self.spothinta.energy_prices(self.region)
        except SpotHintaConnectionError as err:
            next_update_at = now + timedelta(minutes=3)

            self.future_refresh = async_track_point_in_time(
                self.hass, self.async_request_update, next_update_at
            )

            raise UpdateFailed("Error communicating with Spot-Hinta.fi API") from err

        random_delay = randint(0, 300)
        if has_prices_for_tomorrow(energy_prices):
            # The next time the prices are updated: tomorrow ~11.00 UTC
            next_update_at = now.replace(
                day=now.day + 1, hour=11, minute=0
            ) + timedelta(seconds=random_delay)
            _LOGGER.debug(
                "Got prices for tomorrow, next refresh scheduled for tomorrow: %s",
                str(next_update_at),
            )
        elif now.hour < 11:
            # New prices will be available starting from 11.00 UTC
            next_update_at = now.replace(hour=11, minute=0) + timedelta(
                seconds=random_delay
            )
            _LOGGER.debug("Next check for new prices: %s", str(next_update_at))
        else:
            # 11.00 UTC has passed but still no new prices, try again in a moment
            next_update_at = now + timedelta(minutes=3)
            _LOGGER.debug(
                "New prices not yet available, next check: %s", str(next_update_at)
            )

        self.future_refresh = async_track_point_in_time(
            self.hass, self.async_request_update, next_update_at
        )

        return SpotHintaData(
            energy_today=energy_prices,
        )


def has_prices_for_tomorrow(energy_prices: Electricity) -> bool:
    """Returns true if there are prices for tomorrow in the given energy prices"""
    now = dt_util.utcnow()
    for timestamp in energy_prices.prices.keys():
        if timestamp.day > now.day:
            return True

    return False
