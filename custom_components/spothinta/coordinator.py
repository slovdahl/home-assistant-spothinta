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
    current_data: Electricity | None

    def __init__(self, hass: HomeAssistant, region: Region) -> None:
        """Initialize global Spot-Hinta.fi data updater."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{region.name}",
        )

        self.future_update: CALLBACK_TYPE | None = None
        self.region = region
        self.spothinta = SpotHinta(session=async_get_clientsession(hass))
        self.current_data = None

    async def async_request_update(self, *_) -> None:
        """Request update from coordinator."""
        await self.async_request_refresh()

    async def _async_update_data(self) -> SpotHintaData:
        """Fetch data from spot-hinta.fi."""

        now = dt_util.utcnow()

        if self.current_data is not None and has_prices_for_tomorrow(self.current_data):
            # Trigger an update of the sensors at the top of the next hour.
            next_update_at = now.replace(minute=0) + timedelta(hours=1)

            self.future_update = async_track_point_in_time(
                self.hass, self.async_request_update, next_update_at
            )

            return SpotHintaData(energy_today=self.current_data)

        if self.current_data is None or now.hour >= 11:
            # We want to get the prices for tomorrow, but we want to avoid
            # having all instances of the integration polling at the same second.
            if self.current_data is not None and now.minute == 0 and now.second == 0:
                random_delay = randint(0, 120)
                next_update_at = now + timedelta(seconds=random_delay)
                _LOGGER.debug("Getting prices for tomorrow in %s seconds", random_delay)

                self.future_update = async_track_point_in_time(
                    self.hass, self.async_request_update, next_update_at
                )

                return SpotHintaData(energy_today=self.current_data)

            try:
                self.current_data = await self.spothinta.energy_prices(self.region)
            except SpotHintaConnectionError as err:
                _LOGGER.warning("Failed to get energy prices", exc_info=True)

                if self.current_data is not None:
                    next_update_at = (
                        now + timedelta(minutes=5) + timedelta(seconds=random_delay)
                    )
                    _LOGGER.debug("Retrying fetching energy prices %s", next_update_at)

                    self.future_update = async_track_point_in_time(
                        self.hass, self.async_request_update, next_update_at
                    )

                    return SpotHintaData(energy_today=self.current_data)

                raise UpdateFailed(
                    "Error communicating with Spot-Hinta.fi API"
                ) from err

        if has_prices_for_tomorrow(self.current_data):
            _LOGGER.debug("Got prices for tomorrow")
            next_update_at = now.replace(minute=0, second=0) + timedelta(hours=1)
        elif now.hour >= 11:
            next_update_at = now + timedelta(minutes=3)
            _LOGGER.debug(
                "Tomorrow's prices not yet available, next check: %s",
                str(next_update_at),
            )
        else:
            next_update_at = now.replace(minute=0, second=0) + timedelta(hours=1)

        _LOGGER.debug("Next update: %s", str(next_update_at))
        self.future_update = async_track_point_in_time(
            self.hass, self.async_request_update, next_update_at
        )

        return SpotHintaData(
            energy_today=self.current_data,
        )


def has_prices_for_tomorrow(energy_prices: Electricity | None) -> bool:
    """Returns true if there are prices for tomorrow in the given energy prices"""
    if energy_prices is None:
        return False

    now = dt_util.utcnow()
    for timestamp in energy_prices.prices.keys():
        if timestamp.day > now.day:
            return True

    return False
