"""Fixtures for spothinta integration tests."""

from collections.abc import Generator
import json
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture
from spothinta_api import Electricity

from custom_components.spothinta.const import DOMAIN
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Mock setting up a config entry."""
    with patch(
        "custom_components.spothinta.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="energy",
        domain=DOMAIN,
        data={},
        unique_id="unique_thingy",
    )


@pytest.fixture
def mock_spothinta() -> Generator[MagicMock, None, None]:
    """Return a mocked SpotHinta client."""
    with patch(
        "custom_components.spothinta.coordinator.SpotHinta", autospec=True
    ) as spothinta_mock:
        client = spothinta_mock.return_value
        client.energy_prices.return_value = Electricity.from_dict(
            json.loads(load_fixture("energy.json", DOMAIN)), ZoneInfo("Europe/Helsinki")
        )
        yield client


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_spothinta: MagicMock
) -> MockConfigEntry:
    """Set up the spothinta integration for testing."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry
