"""The Coordinator for Spot-Hinta.fi."""
from __future__ import annotations

from datetime import datetime, timedelta
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

        # The normal happy path, we have the enough for prices for today and
        # tomorrow, no need to trigger any external requests.
        if self.current_data is not None and has_prices_for_tomorrow_until_next_day_refresh(self.current_data):
            # Trigger an update of the sensors at the next quarter of the hour.
            next_update_at = get_next_quarter_of_hour(now)
            self.future_update = async_track_point_in_time(
                self.hass, self.async_request_update, next_update_at
            )

            return SpotHintaData(energy_today=self.current_data)

        # Day-ahead prices are usually published around 13-14:00 CET. Depending
        # on the time of the year, this is either 11-12:00 or 12-13:00 UTC. We
        # start polling for new prices at 11:00 UTC.
        if self.current_data is None or now.hour >= 11 or not has_prices_for_tomorrow_until_next_day_refresh(self.current_data):
            random_delay = randint(0, 120)

            # We want to get the prices for tomorrow, but we want to avoid
            # having all instances of the integration polling at the same second.
            if self.current_data is not None and now.minute == 0 and now.second == 0:
                next_update_at = now + timedelta(seconds=random_delay)
                _LOGGER.debug("Getting prices for tomorrow in %s seconds", random_delay)

                self.future_update = async_track_point_in_time(
                    self.hass, self.async_request_update, next_update_at
                )

                return SpotHintaData(energy_today=self.current_data)

            try:
                self.current_data = await self.spothinta.energy_prices(region=self.region, resolution=timedelta(minutes=15))
            except SpotHintaConnectionError as err:
                _LOGGER.warning("Failed to get energy prices", exc_info=True)

                # The refresh failed, but we already have some data which we can
                # return while scheduling a new refresh in a few minutes.
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

        if has_prices_for_tomorrow_until_next_day_refresh(self.current_data):
            _LOGGER.debug("Got prices until tomorrow's refresh")
            next_update_at = get_next_quarter_of_hour(now)
        elif now.hour >= 11 and not has_prices_for_tomorrow(self.current_data):
            # Try again in a few minutes if there were no prices at all for
            # tomorrow. This can happen if the prices for tomorrow haven't
            # been published yet.
            next_update_at = now + timedelta(minutes=3)
            _LOGGER.debug(
                "Tomorrow's prices not yet available, next check: %s",
                str(next_update_at),
            )
        else:
            # We got some prices but not yet until the next day refresh.
            _LOGGER.info("Not all prices for tomorrow available from the API yet")
            next_update_at = get_next_quarter_of_hour(now)

        _LOGGER.debug("Next update: %s", str(next_update_at))
        self.future_update = async_track_point_in_time(
            self.hass, self.async_request_update, next_update_at
        )

        return SpotHintaData(
            energy_today=self.current_data,
        )


def get_next_quarter_of_hour(now: datetime) -> datetime:
    """Get the next quarter of the hour."""
    next_update_at = now + timedelta(minutes=15)
    next_minute = next_update_at.minute // 15 * 15
    next_update_at = next_update_at.replace(
        minute=next_minute, second=0, microsecond=0, tzinfo=dt_util.UTC
    )
    return next_update_at


def has_prices_for_tomorrow_until_next_day_refresh(energy_prices: Electricity | None) -> bool:
    """Returns true if there are prices for tomorrow until the next day refresh in the given energy prices"""
    if energy_prices is None:
        return False

    now = dt_util.utcnow()
    for timestamp in energy_prices.prices.keys():
        # The prices for tomorrow are usually published around 13-14:00 CET.
        # Depending on the time of the year, this is either 11-12:00 or
        # 12-13:00 UTC. If we have prices until 12:00 UTC tomorrow, we can
        # wait with polling for new prices until the next day refresh, even
        # if we don't have prices for the whole tomorrow yet.
        if timestamp.day > now.day and timestamp.hour >= 12:
            return True

    return False


def has_prices_for_tomorrow(energy_prices: Electricity | None) -> bool:
    """Returns true if there are prices for tomorrow in the given energy prices"""
    if energy_prices is None:
        return False

    now = dt_util.utcnow()
    for timestamp in energy_prices.prices.keys():
        if timestamp.day > now.day:
            return True

    return False
