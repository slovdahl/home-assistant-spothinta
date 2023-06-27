"""Constants for the Spot-Hinta.fi integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "spothinta"
LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(hours=1)
THRESHOLD_HOUR: Final = 12

SERVICE_TYPE_DEVICE_NAMES = {
    "energy": "Energy market prices",
}
