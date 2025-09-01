"""Adds config flow for Real Electricity Price integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
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
    CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT_GRID_TRANSMISSION_DAY,
    CONF_VAT_GRID_TRANSMISSION_NIGHT,
    CONF_VAT_NORD_POOL,
    CONF_VAT_SUPPLIER_MARGIN,
    CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
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
    VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    VAT_GRID_TRANSMISSION_DAY_DEFAULT,
    VAT_GRID_TRANSMISSION_NIGHT_DEFAULT,
    VAT_NORD_POOL_DEFAULT,
    VAT_SUPPLIER_MARGIN_DEFAULT,
    VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
)


class RealElectricityPriceFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Real Electricity Price."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            # Create unique ID based on name, grid, and supplier to allow multiple devices
            name = user_input.get(CONF_NAME, "Real Electricity Price")
            grid = user_input.get(CONF_GRID, GRID_DEFAULT)
            supplier = user_input.get(CONF_SUPPLIER, SUPPLIER_DEFAULT)
            
            await self.async_set_unique_id(
                unique_id=f"real_electricity_price_{name}_{grid}_{supplier}".lower().replace(" ", "_")
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=name,
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
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    vol.Optional(
                        CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                        default=(user_input or {}).get(
                            CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                            GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    vol.Optional(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                        default=(user_input or {}).get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    vol.Optional(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                        default=(user_input or {}).get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                            GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
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
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    vol.Optional(
                        CONF_SUPPLIER_MARGIN,
                        default=(user_input or {}).get(
                            CONF_SUPPLIER_MARGIN,
                            SUPPLIER_MARGIN_DEFAULT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
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
                        selector.NumberSelectorConfig(min=0, max=100, step=0.1, mode="box")
                    ),
                    # Individual VAT controls for each price component
                    vol.Optional(
                        CONF_VAT_NORD_POOL,
                        default=(user_input or {}).get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                        default=(user_input or {}).get(CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY, VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                        default=(user_input or {}).get(CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE, VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_GRID_TRANSMISSION_NIGHT,
                        default=(user_input or {}).get(CONF_VAT_GRID_TRANSMISSION_NIGHT, VAT_GRID_TRANSMISSION_NIGHT_DEFAULT),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_GRID_TRANSMISSION_DAY,
                        default=(user_input or {}).get(CONF_VAT_GRID_TRANSMISSION_DAY, VAT_GRID_TRANSMISSION_DAY_DEFAULT),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                        default=(user_input or {}).get(CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE, VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_SUPPLIER_MARGIN,
                        default=(user_input or {}).get(CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT),
                    ): selector.BooleanSelector(),
                    # Time settings
                    vol.Optional(
                        CONF_NIGHT_PRICE_START_HOUR,
                        default=(user_input or {}).get(
                            CONF_NIGHT_PRICE_START_HOUR, NIGHT_PRICE_START_HOUR_DEFAULT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")
                    ),
                    vol.Optional(
                        CONF_NIGHT_PRICE_END_HOUR,
                        default=(user_input or {}).get(
                            CONF_NIGHT_PRICE_END_HOUR, NIGHT_PRICE_END_HOUR_DEFAULT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")
                    ),
                    # Update interval
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=(user_input or {}).get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=300, max=86400, step=300, mode="box"
                        )  # 5 min to 24 hours
                    ),
                },
            ),
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for Real Electricity Price."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current config values
        current_data = self.config_entry.data
        options_data = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=options_data.get(
                            CONF_NAME, current_data.get(CONF_NAME, "Real Electricity Price")
                        ),
                    ): selector.TextSelector(),
                    # Grid parameters
                    vol.Optional(
                        CONF_GRID,
                        default=options_data.get(
                            CONF_GRID, current_data.get(CONF_GRID, GRID_DEFAULT)
                        ),
                    ): selector.TextSelector(),
                    vol.Optional(
                        CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                        default=options_data.get(
                            CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                            current_data.get(
                                CONF_GRID_ELECTRICITY_EXCISE_DUTY,
                                GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    vol.Optional(
                        CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                        default=options_data.get(
                            CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                            current_data.get(
                                CONF_GRID_RENEWABLE_ENERGY_CHARGE,
                                GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    vol.Optional(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                        default=options_data.get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                            current_data.get(
                                CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
                                GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    vol.Optional(
                        CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                        default=options_data.get(
                            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                            current_data.get(
                                CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
                                GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    # Supplier parameters
                    vol.Optional(
                        CONF_SUPPLIER,
                        default=options_data.get(
                            CONF_SUPPLIER, current_data.get(CONF_SUPPLIER, SUPPLIER_DEFAULT)
                        ),
                    ): selector.TextSelector(),
                    vol.Optional(
                        CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                        default=options_data.get(
                            CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                            current_data.get(
                                CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                                SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    vol.Optional(
                        CONF_SUPPLIER_MARGIN,
                        default=options_data.get(
                            CONF_SUPPLIER_MARGIN,
                            current_data.get(
                                CONF_SUPPLIER_MARGIN,
                                SUPPLIER_MARGIN_DEFAULT,
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=1, step="any", mode="box")
                    ),
                    # Regional and tax settings
                    vol.Optional(
                        CONF_COUNTRY_CODE,
                        default=options_data.get(
                            CONF_COUNTRY_CODE,
                            current_data.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT),
                        ),
                    ): selector.TextSelector(),
                    vol.Optional(
                        CONF_VAT,
                        default=options_data.get(
                            CONF_VAT, current_data.get(CONF_VAT, VAT_DEFAULT)
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=100, step=0.1, mode="box")
                    ),
                    # Individual VAT controls for each price component
                    vol.Optional(
                        CONF_VAT_NORD_POOL,
                        default=options_data.get(
                            CONF_VAT_NORD_POOL, current_data.get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT)
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
                        default=options_data.get(
                            CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY, 
                            current_data.get(CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY, VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT)
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
                        default=options_data.get(
                            CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE, 
                            current_data.get(CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE, VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT)
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_GRID_TRANSMISSION_NIGHT,
                        default=options_data.get(
                            CONF_VAT_GRID_TRANSMISSION_NIGHT, 
                            current_data.get(CONF_VAT_GRID_TRANSMISSION_NIGHT, VAT_GRID_TRANSMISSION_NIGHT_DEFAULT)
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_GRID_TRANSMISSION_DAY,
                        default=options_data.get(
                            CONF_VAT_GRID_TRANSMISSION_DAY, 
                            current_data.get(CONF_VAT_GRID_TRANSMISSION_DAY, VAT_GRID_TRANSMISSION_DAY_DEFAULT)
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
                        default=options_data.get(
                            CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE, 
                            current_data.get(CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE, VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT)
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_VAT_SUPPLIER_MARGIN,
                        default=options_data.get(
                            CONF_VAT_SUPPLIER_MARGIN, 
                            current_data.get(CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT)
                        ),
                    ): selector.BooleanSelector(),
                    # Time settings
                    vol.Optional(
                        CONF_NIGHT_PRICE_START_HOUR,
                        default=options_data.get(
                            CONF_NIGHT_PRICE_START_HOUR,
                            current_data.get(
                                CONF_NIGHT_PRICE_START_HOUR, NIGHT_PRICE_START_HOUR_DEFAULT
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")
                    ),
                    vol.Optional(
                        CONF_NIGHT_PRICE_END_HOUR,
                        default=options_data.get(
                            CONF_NIGHT_PRICE_END_HOUR,
                            current_data.get(
                                CONF_NIGHT_PRICE_END_HOUR, NIGHT_PRICE_END_HOUR_DEFAULT
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")
                    ),
                    # Update interval
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=options_data.get(
                            CONF_SCAN_INTERVAL,
                            current_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=300, max=86400, step=300, mode="box"
                        )  # 5 min to 24 hours
                    ),
                },
            ),
        )
