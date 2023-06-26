"""Config flow for Spot-Hinta.fi integration."""

from __future__ import annotations

from typing import Any

from spothinta_api.const import Region
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_REGION
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import DOMAIN

REGIONS = [region.name for region in Region]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REGION, default=Region.FI.name): SelectSelector(
            SelectSelectorConfig(
                options=REGIONS,
            ),
        ),
    }
)


class SpotHintaFlowHandler(ConfigFlow, domain=DOMAIN):  # type: ignore
    """Config flow for Spot-Hinta.fi integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        region = user_input[CONF_REGION]

        if region not in Region.__members__:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={CONF_REGION: "invalid_region"},
            )

        await self.async_set_unique_id(DOMAIN + region)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Spot-Hinta.fi region {region}",
            data={CONF_REGION: Region[region]},
        )
