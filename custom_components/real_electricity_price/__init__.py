"""
Custom integration to integrate real-electricity-price with Home Assistant.

For more details about this integration, please refer to
https://github.com/bitosome/real-electricity-price
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import RealElectricityPriceApiClient
from .cheap_hours_coordinator import CheapHoursDataUpdateCoordinator
from .const import (
    CONF_CHEAP_HOURS_UPDATE_TRIGGER,
    CONF_COUNTRY_CODE,
    CONF_GRID,
    CONF_NIGHT_PRICE_END_TIME,
    CONF_NIGHT_PRICE_START_TIME,
    CONF_SCAN_INTERVAL,
    CONF_SUPPLIER,
    COUNTRY_CODE_DEFAULT,
    DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    GRID_DEFAULT,
    LOGGER,
    NIGHT_PRICE_END_TIME_DEFAULT,
    NIGHT_PRICE_START_TIME_DEFAULT,
    SUPPLIER_DEFAULT,
)
from .coordinator import RealElectricityPriceDataUpdateCoordinator
from .data import RealElectricityPriceData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import RealElectricityPriceConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,  # For config entities
    Platform.TIME,  # For config entities
]

SERVICE_REFRESH_DATA = "refresh_data"
SERVICE_RECALCULATE_CHEAP_PRICES = "recalculate_cheap_prices"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up this integration using configuration.yaml."""
    LOGGER.info("async_setup called with config: %s", config)

    if DOMAIN not in config:
        LOGGER.info("DOMAIN not in config, returning True")
        return True

    LOGGER.info("DOMAIN found in config, proceeding with setup")

    # Create a config entry from configuration.yaml
    config_data = config[DOMAIN]
    LOGGER.info("Config data: %s", config_data)

    # Check if config entry already exists
    existing_entries = hass.config_entries.async_entries(DOMAIN)
    LOGGER.info("Existing entries: %s", len(existing_entries))

    if existing_entries:
        LOGGER.info("Config entry already exists, skipping configuration.yaml setup")
        return True

    # Create config entry data
    entry_data = {
        CONF_GRID: config_data.get(CONF_GRID, GRID_DEFAULT),
        CONF_SUPPLIER: config_data.get(CONF_SUPPLIER, SUPPLIER_DEFAULT),
        CONF_COUNTRY_CODE: config_data.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT),
        CONF_NIGHT_PRICE_START_TIME: config_data.get(
            CONF_NIGHT_PRICE_START_TIME, NIGHT_PRICE_START_TIME_DEFAULT
        ),
        CONF_NIGHT_PRICE_END_TIME: config_data.get(
            CONF_NIGHT_PRICE_END_TIME, NIGHT_PRICE_END_TIME_DEFAULT
        ),
        CONF_SCAN_INTERVAL: config_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        CONF_CHEAP_HOURS_UPDATE_TRIGGER: config_data.get(
            CONF_CHEAP_HOURS_UPDATE_TRIGGER, DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER
        ),
    }

    LOGGER.info("Creating config entry with data: %s", entry_data)

    # Create the config entry
    try:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data=entry_data,
            )
        )
        LOGGER.info("Config entry creation initiated successfully")
    except Exception as e:
        LOGGER.error("Error creating config entry: %s", e)
        return False

    LOGGER.info("Created config entry from configuration.yaml")
    return True


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: RealElectricityPriceConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    # Migration: Add missing cheap_price_update_trigger parameter to existing configs
    if CONF_CHEAP_HOURS_UPDATE_TRIGGER not in entry.data:
        LOGGER.info(
            "Migrating configuration: adding cheap_price_update_trigger parameter"
        )
        new_data = dict(entry.data)
        new_data[CONF_CHEAP_HOURS_UPDATE_TRIGGER] = DEFAULT_CHEAP_HOURS_UPDATE_TRIGGER

        hass.config_entries.async_update_entry(entry, data=new_data)

    # Merge entry data with options (options override data)
    config = {**entry.data, **entry.options}
    # Ensure time zone from Home Assistant is available to downstream components
    if "time_zone" not in config and hasattr(hass.config, "time_zone"):
        config["time_zone"] = hass.config.time_zone

    coordinator = RealElectricityPriceDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=f"{DOMAIN}_main",
        update_interval=timedelta(
            seconds=config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ),
    )

    # Initialize cheap price coordinator
    cheap_hours_coordinator = CheapHoursDataUpdateCoordinator(
        main_coordinator=coordinator,
        config_entry=entry,
        hass=hass,
        logger=LOGGER,
        name=f"{DOMAIN}_cheap_prices",
        update_method=None,  # No default update interval, uses triggers
    )

    # Link coordinators for automatic cheap hours updates after data sync
    coordinator.set_cheap_price_coordinator(cheap_hours_coordinator)

    entry.runtime_data = RealElectricityPriceData(
        client=RealElectricityPriceApiClient(
            session=async_get_clientsession(hass),
            config=config,
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        cheap_hours_coordinator=cheap_hours_coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up reload listener to update trigger configurations
    async def async_reload_triggers(
        hass: HomeAssistant, updated_entry: RealElectricityPriceConfigEntry
    ) -> None:
        """Update trigger configurations when config changes."""
        cheap_hours_coordinator.update_trigger_config()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Register services
    async def async_refresh_data(call) -> None:
        """Handle refresh data service call."""
        LOGGER.debug("Refresh data service called")
        await coordinator.async_request_refresh()

    async def async_recalculate_cheap_prices(call) -> None:
        """Handle recalculate cheap prices service call."""
        LOGGER.debug("Recalculate cheap prices service called")
        await cheap_hours_coordinator.async_manual_update()

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_DATA,
        async_refresh_data,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECALCULATE_CHEAP_PRICES,
        async_recalculate_cheap_prices,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: RealElectricityPriceConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove services when last entry is unloaded
    if unload_ok and not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DATA)
        hass.services.async_remove(DOMAIN, SERVICE_RECALCULATE_CHEAP_PRICES)

    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: RealElectricityPriceConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
