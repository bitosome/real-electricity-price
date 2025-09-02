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
from .const import (
    CONF_SCAN_INTERVAL, 
    DEFAULT_SCAN_INTERVAL, 
    DOMAIN, 
    LOGGER,
    CONF_CHEAP_PRICE_UPDATE_TRIGGER,
    DEFAULT_CHEAP_PRICE_UPDATE_TRIGGER,
)
from .coordinator import RealElectricityPriceDataUpdateCoordinator
from .cheap_price_coordinator import CheapPriceDataUpdateCoordinator
from .data import RealElectricityPriceData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import RealElectricityPriceConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
]

SERVICE_REFRESH_DATA = "refresh_data"
SERVICE_RECALCULATE_CHEAP_PRICES = "recalculate_cheap_prices"


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: RealElectricityPriceConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    # Migration: Add missing cheap_price_update_trigger parameter to existing configs
    if CONF_CHEAP_PRICE_UPDATE_TRIGGER not in entry.data:
        LOGGER.info("Migrating configuration: adding cheap_price_update_trigger parameter")
        new_data = dict(entry.data)
        new_data[CONF_CHEAP_PRICE_UPDATE_TRIGGER] = DEFAULT_CHEAP_PRICE_UPDATE_TRIGGER
        
        hass.config_entries.async_update_entry(
            entry, 
            data=new_data
        )
    
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
    cheap_price_coordinator = CheapPriceDataUpdateCoordinator(
        main_coordinator=coordinator,
        config_entry=entry,
        hass=hass,
        logger=LOGGER,
        name=f"{DOMAIN}_cheap_prices",
        update_method=None,  # No default update interval, uses triggers
    )
    
    entry.runtime_data = RealElectricityPriceData(
        client=RealElectricityPriceApiClient(
            session=async_get_clientsession(hass),
            config=config,
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        cheap_price_coordinator=cheap_price_coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up reload listener to update trigger configurations
    async def async_reload_triggers(hass: HomeAssistant, updated_entry: RealElectricityPriceConfigEntry) -> None:
        """Update trigger configurations when config changes."""
        cheap_price_coordinator.update_trigger_config()
    
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Register services
    async def async_refresh_data(call) -> None:
        """Handle refresh data service call."""
        LOGGER.debug("Refresh data service called")
        await coordinator.async_request_refresh()

    async def async_recalculate_cheap_prices(call) -> None:
        """Handle recalculate cheap prices service call."""
        LOGGER.debug("Recalculate cheap prices service called")
        await cheap_price_coordinator.async_manual_update()

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
