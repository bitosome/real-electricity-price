"""Adds config flow for Real Electricity Price integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_COUNTRY_CODE,
    CONF_GRID,
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_NIGHT_PRICE_END_HOUR,
    CONF_NIGHT_PRICE_START_HOUR,
    CONF_SCAN_INTERVAL,
    CONF_SUPPLIER,
    CONF_SUPPLIER_MARGIN,
    CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT,
    COUNTRY_CODE_DEFAULT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    GRID_DEFAULT,
    GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
    GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    NIGHT_PRICE_END_HOUR_DEFAULT,
    NIGHT_PRICE_START_HOUR_DEFAULT,
    SUPPLIER_DEFAULT,
    SUPPLIER_MARGIN_DEFAULT,
    SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    VAT_DEFAULT,
)


class RealElectricityPriceFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Real Electricity Price."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            await self.async_set_unique_id(
                unique_id=f"real_electricity_price_"
                f"{user_input.get(CONF_GRID, GRID_DEFAULT)}_"
                f"{user_input.get(CONF_SUPPLIER, SUPPLIER_DEFAULT)}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "Real Electricity Price"),
                data={
                    **user_input,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=(user_input or {}).get(
                            CONF_NAME, "Real Electricity Price"
                        ),
                    ): selector.TextSelector(),
                    # Grid parameters
                    vol.Optional(
                        CONF_GRID,
                        default=(user_input or {}).get(CONF_GRID, GRID_DEFAULT),
                    ): selector.TextSelector(),
                    vol.Optional(
                        CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                        default=(user_input or {}).get(
                            CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                            GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, step=0.0001)
                    ),
                    vol.Optional(
                        CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                        default=(user_input or {}).get(
                            CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                            GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, step=0.0001)
                    ),
                    vol.Optional(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                        default=(user_input or {}).get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, step=0.0001)
                    ),
                    vol.Optional(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                        default=(user_input or {}).get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, step=0.0001)
                    ),
                    # Supplier parameters
                    vol.Optional(
                        CONF_SUPPLIER,
                        default=(user_input or {}).get(CONF_SUPPLIER, SUPPLIER_DEFAULT),
                    ): selector.TextSelector(),
                    vol.Optional(
                        CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                        default=(user_input or {}).get(
                            CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                            SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, step=0.0001)
                    ),
                    vol.Optional(
                        CONF_SUPPLIER_MARGIN,
                        default=(user_input or {}).get(
                            CONF_SUPPLIER_MARGIN,
                            SUPPLIER_MARGIN_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, step=0.0001)
                    ),
                    # Regional and tax settings
                    vol.Optional(
                        CONF_COUNTRY_CODE,
                        default=(user_input or {}).get(
                            CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT
                        ),
                    ): selector.TextSelector(),
                    vol.Optional(
                        CONF_VAT,
                        default=(user_input or {}).get(CONF_VAT, VAT_DEFAULT),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=100, step=0.1)
                    ),
                    vol.Optional(
                        CONF_NIGHT_PRICE_START_HOUR,
                        default=(user_input or {}).get(
                            CONF_NIGHT_PRICE_START_HOUR, NIGHT_PRICE_START_HOUR_DEFAULT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=23, step=1)
                    ),
                    vol.Optional(
                        CONF_NIGHT_PRICE_END_HOUR,
                        default=(user_input or {}).get(
                            CONF_NIGHT_PRICE_END_HOUR, NIGHT_PRICE_END_HOUR_DEFAULT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=23, step=1)
                    ),
                    # Update interval
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=(user_input or {}).get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=300, max=86400, step=300
                        )  # 5 min to 24 hours
                    ),
                },
            ),
        )
