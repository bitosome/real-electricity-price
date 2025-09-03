"""API Client for Real Electricity Price using Nord Pool."""

from __future__ import annotations

import asyncio
import datetime
import logging
import re
import socket
from typing import Any

import aiohttp
import async_timeout
import holidays
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COUNTRY_CODE,
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
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
    GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
    GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    PRICE_DECIMAL_PRECISION,
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

_LOGGER = logging.getLogger(__name__)

# Constants
NORD_POOL_API_URL = "https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices"
API_TIMEOUT = 20
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 7


class RealElectricityPriceApiClientError(Exception):
    """Exception to indicate a general API error."""


class RealElectricityPriceApiClientCommunicationError(
    RealElectricityPriceApiClientError
):
    """Exception to indicate a communication error."""


class RealElectricityPriceApiClientAuthenticationError(
    RealElectricityPriceApiClientError
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise RealElectricityPriceApiClientAuthenticationError(msg)
    response.raise_for_status()


def extract_country_code_from_area(area_code: str) -> str:
    """
    Extract ISO country code from Nord Pool area code.

    Nord Pool uses area codes that may include numbers for sub-regions.
    This function extracts the two-letter country code prefix.

    Args:
        area_code: Nord Pool area code (e.g., "EE", "SE1", "NO2")

    Returns:
        Two-letter ISO country code

    Examples:
        - "EE" -> "EE"
        - "FI" -> "FI"
        - "SE1" -> "SE"
        - "NO2" -> "NO"
        - "DK1" -> "DK"

    """
    if not area_code or len(area_code) < 2:
        return "EE"  # Default fallback for empty or single character

    # Extract first 2 letters using regex for better validation
    match = re.match(r"^([A-Z]{2})", area_code.upper())
    if match:
        return match.group(1)

    # Fallback: just take first 2 characters and uppercase them
    return area_code[:2].upper()


class RealElectricityPriceApiClient:
    """API Client for Nord Pool."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        config: dict[str, Any],
    ) -> None:
        """Initialize the API Client."""
        self._session = session
        self._config = config

    async def async_get_data(self) -> dict[str, Any] | None:
        """Get data from Nord Pool API for yesterday, today and tomorrow."""
        try:
            today = datetime.datetime.now(datetime.UTC).date()
            yesterday = today - datetime.timedelta(days=1)
            tomorrow = today + datetime.timedelta(days=1)

            currency = self._config.get("currency", "EUR")
            market = self._config.get("market", "DayAhead")
            # Use configured delivery area (country code) for Nord Pool
            area = self._config.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT)
            token = self._config.get("token")

            headers = self._get_request_headers(token)

            # Fetch yesterday's, today's and tomorrow's data
            yesterday_data = await self._fetch_day_data(
                yesterday, currency, market, area, headers
            )
            today_data = await self._fetch_day_data(
                today, currency, market, area, headers
            )
            tomorrow_data = await self._fetch_day_data(
                tomorrow, currency, market, area, headers
            )

            if not today_data:
                _LOGGER.warning("Failed to fetch today's electricity price data")
                return None

            # Process the data
            result = {}

            if yesterday_data:
                yesterday_processed = await self._modify_prices(
                    yesterday_data, area, yesterday.isoformat()
                )
                result["yesterday"] = yesterday_processed
            else:
                _LOGGER.info(
                    "Yesterday's data not available for %s", yesterday.isoformat()
                )

            today_processed = await self._modify_prices(
                today_data, area, today.isoformat()
            )
            result["today"] = today_processed

            if tomorrow_data:
                tomorrow_processed = await self._modify_prices(
                    tomorrow_data, area, tomorrow.isoformat()
                )
                result["tomorrow"] = tomorrow_processed
            else:
                _LOGGER.info(
                    "Tomorrow's data not available for %s (normal before ~14:00 CET)",
                    tomorrow.isoformat(),
                )
                # Create placeholder data with time ranges but unavailable prices
                tomorrow_placeholder = await self._create_placeholder_day_data(
                    tomorrow, area
                )
                result["tomorrow"] = tomorrow_placeholder

            return result

        except Exception as exception:
            _LOGGER.exception("Unexpected error in async_get_data: %s", exception)
            msg = f"Unexpected error: {exception}"
            raise RealElectricityPriceApiClientError(msg) from exception

    def _get_request_headers(self, token: str | None) -> dict[str, str]:
        """Get request headers with optional authorization."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "real-electricity-price/1.0",
        }
        if token:
            if not token.lower().startswith("bearer "):
                token = "Bearer " + token
            headers["Authorization"] = token
        return headers

    async def _fetch_day_data(
        self,
        date: datetime.date,
        currency: str,
        market: str,
        area: str,
        headers: dict[str, str],
    ) -> dict[str, Any] | None:
        """Fetch data for a specific day."""
        params = {
            "date": date.isoformat(),
            "market": market,
            "currency": currency,
            "deliveryArea": area,
            "deliveryAreas": area,
        }

        try:
            return await self._api_wrapper(
                method="get",
                url=NORD_POOL_API_URL,
                params=params,
                headers=headers,
            )
        except RealElectricityPriceApiClientError:
            _LOGGER.warning("Failed to fetch data for %s", date.isoformat())
            return None

    async def _create_placeholder_day_data(
        self, date: datetime.date, area: str
    ) -> dict:
        """Create placeholder day data with time ranges but unavailable prices."""
        # Get configuration for tariff calculation
        night_start = self._config.get("night_price_start_hour", 22)
        night_end = self._config.get("night_price_end_hour", 7)
        tz_name = self._config.get("time_zone")
        tzinfo = (
            dt_util.get_time_zone(tz_name) if tz_name else dt_util.DEFAULT_TIME_ZONE
        )
        area_code = self._config.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT)

        # Extract ISO country code from Nord Pool area code for holiday detection
        country_code = extract_country_code_from_area(area_code)

        # Calculate holiday and weekend status for this date
        year = date.year
        loop = asyncio.get_running_loop()
        country_holidays = await loop.run_in_executor(
            None, lambda: holidays.country_holidays(country_code, years=year)
        )
        is_holiday = date in country_holidays
        is_weekend = date.weekday() >= 5  # Saturday = 5, Sunday = 6

        # Create 24 hourly time slots for the day
        hourly_prices = []

        for hour in range(24):
            start_time = datetime.datetime.combine(date, datetime.time(hour=hour))
            start_time = start_time.replace(tzinfo=datetime.UTC)
            end_time = start_time + datetime.timedelta(hours=1)

            # Convert to local time for tariff calculation
            local_hour = start_time.astimezone(tzinfo).hour

            # Determine tariff based on local time and selected country's calendar
            tariff = "night"  # Default
            if is_holiday or is_weekend:
                tariff = "night"
            else:
                # Check if it's night hours in local time
                if night_start > night_end:  # Night crosses midnight (e.g., 22-7)
                    is_night_hour = local_hour >= night_start or local_hour < night_end
                else:  # Night doesn't cross midnight (e.g., 0-6)
                    is_night_hour = night_start <= local_hour < night_end

                tariff = "night" if is_night_hour else "day"

            hourly_prices.append(
                {
                    "start_time": start_time.isoformat().replace("+00:00", "Z"),
                    "end_time": end_time.isoformat().replace("+00:00", "Z"),
                    "nord_pool_price": None,  # Unavailable
                    "actual_price": None,  # Unavailable
                    "tariff": tariff,  # Calculated based on time and calendar
                    "is_holiday": is_holiday,  # Calculated
                    "is_weekend": is_weekend,  # Calculated
                }
            )

        return {
            "hourly_prices": hourly_prices,
            "date": date.isoformat(),
            "is_holiday": is_holiday,  # Calculated
            "is_weekend": is_weekend,  # Calculated
            "data_available": False,  # Flag to indicate this is placeholder data
        }

    async def _modify_prices(self, data: dict, area: str, date: str) -> dict:
        """
        Modify prices with additional costs.

        This method performs some blocking work (holidays lookup and
        locale file access). Run blocking parts in the executor to avoid
        blocking the event loop.
        """
        # Get price component values
        grid_electricity_excise_duty = self._config.get(
            CONF_GRID_ELECTRICITY_EXCISE_DUTY, GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT
        )
        grid_renewable_energy_charge = self._config.get(
            CONF_GRID_RENEWABLE_ENERGY_CHARGE, GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT
        )
        grid_electricity_transmission_price_night = self._config.get(
            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
            GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
        )
        grid_electricity_transmission_price_day = self._config.get(
            CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
            GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
        )
        supplier_renewable_energy_charge = self._config.get(
            CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
            SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
        )
        supplier_margin = self._config.get(
            CONF_SUPPLIER_MARGIN, SUPPLIER_MARGIN_DEFAULT
        )

        # Get VAT percentage and individual VAT flags
        vat_pct = self._config.get(CONF_VAT, VAT_DEFAULT)
        vat_nord_pool = self._config.get(CONF_VAT_NORD_POOL, VAT_NORD_POOL_DEFAULT)
        vat_grid_excise_duty = self._config.get(
            CONF_VAT_GRID_ELECTRICITY_EXCISE_DUTY,
            VAT_GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
        )
        vat_grid_renewable = self._config.get(
            CONF_VAT_GRID_RENEWABLE_ENERGY_CHARGE,
            VAT_GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
        )
        vat_grid_transmission_night = self._config.get(
            CONF_VAT_GRID_TRANSMISSION_NIGHT, VAT_GRID_TRANSMISSION_NIGHT_DEFAULT
        )
        vat_grid_transmission_day = self._config.get(
            CONF_VAT_GRID_TRANSMISSION_DAY, VAT_GRID_TRANSMISSION_DAY_DEFAULT
        )
        vat_supplier_renewable = self._config.get(
            CONF_VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
            VAT_SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
        )
        vat_supplier_margin = self._config.get(
            CONF_VAT_SUPPLIER_MARGIN, VAT_SUPPLIER_MARGIN_DEFAULT
        )
        night_start = self._config.get("night_price_start_hour", 22)
        night_end = self._config.get("night_price_end_hour", 7)
        tz_name = self._config.get("time_zone")
        tzinfo = (
            dt_util.get_time_zone(tz_name) if tz_name else dt_util.DEFAULT_TIME_ZONE
        )
        area_code = self._config.get(CONF_COUNTRY_CODE, COUNTRY_CODE_DEFAULT)

        # Extract ISO country code from Nord Pool area code for holiday detection
        country_code = extract_country_code_from_area(area_code)

        year = int(date[:4])
        # holidays.EE may perform blocking I/O (import/module locale access).
        # Run it in the default executor to avoid blocking the event loop.
        loop = asyncio.get_running_loop()
        country_holidays = await loop.run_in_executor(
            None, lambda: holidays.country_holidays(country_code, years=year)
        )
        date_obj = datetime.date.fromisoformat(date)
        saturday = 5
        is_weekend = date_obj.weekday() >= saturday
        is_holiday = date_obj in country_holidays

        hourly_prices = []
        for entry in data.get("multiAreaEntries", []):
            delivery_start_str = entry.get("deliveryStart")
            if delivery_start_str:
                # deliveryStart may end with 'Z' — make it ISO-8601 compatible
                start_iso = delivery_start_str.replace("Z", "+00:00")
                dt = datetime.datetime.fromisoformat(start_iso)
                local_hour = dt.astimezone(tzinfo).hour

                # Determine tariff for this specific hour
                tariff = "night"  # Default to night

                # If it's a holiday or weekend, always use night tariff
                if is_holiday or is_weekend:
                    tariff = "night"
                else:
                    # Check block aggregates for this specific hour
                    for block in data.get("blockPriceAggregates", []):
                        block_start_str = block.get("deliveryStart")
                        block_end_str = block.get("deliveryEnd")

                        if block_start_str and block_end_str:
                            block_start = datetime.datetime.fromisoformat(
                                block_start_str
                            )
                            block_end = datetime.datetime.fromisoformat(block_end_str)

                            if block_start <= dt < block_end:
                                block_name = block.get("blockName", "")
                                tariff = "day" if block_name == "Peak" else "night"
                                break

                # Determine transmission price based on time and tariff
                if (
                    is_weekend
                    or is_holiday
                    or (local_hour >= night_start or local_hour < night_end)
                ):
                    transmission_price = grid_electricity_transmission_price_night
                    vat_transmission = vat_grid_transmission_night
                else:
                    transmission_price = grid_electricity_transmission_price_day
                    vat_transmission = vat_grid_transmission_day

                if area in entry.get("entryPerArea", {}):
                    original_price = entry["entryPerArea"][area]

                    # Start with base Nord Pool price and apply VAT if configured
                    base_price = (
                        original_price / 1000
                    )  # Convert from EUR/MWh to EUR/kWh
                    if vat_nord_pool:
                        base_price *= 1 + vat_pct / 100

                    # Add each component with individual VAT application
                    excise_component = grid_electricity_excise_duty
                    if vat_grid_excise_duty:
                        excise_component *= 1 + vat_pct / 100

                    renewable_grid_component = grid_renewable_energy_charge
                    if vat_grid_renewable:
                        renewable_grid_component *= 1 + vat_pct / 100

                    renewable_supplier_component = supplier_renewable_energy_charge
                    if vat_supplier_renewable:
                        renewable_supplier_component *= 1 + vat_pct / 100

                    margin_component = supplier_margin
                    if vat_supplier_margin:
                        margin_component *= 1 + vat_pct / 100

                    transmission_component = transmission_price
                    if vat_transmission:
                        transmission_component *= 1 + vat_pct / 100

                    # Calculate final price by summing all components
                    final_price = (
                        base_price
                        + excise_component
                        + renewable_grid_component
                        + renewable_supplier_component
                        + margin_component
                        + transmission_component
                    )

                    entry["entryPerArea"][area] = round(
                        final_price, PRICE_DECIMAL_PRECISION
                    )
                    entry["price_raw_kwh"] = round(
                        original_price / 1000, PRICE_DECIMAL_PRECISION
                    )

            start_time = entry.get("deliveryStart")
            end_time = entry.get("deliveryEnd")
            nord_pool_price = entry.get("price_raw_kwh", 0)
            actual_price = entry["entryPerArea"].get(area, 0)
            hourly_prices.append(
                {
                    "start_time": start_time,
                    "end_time": end_time,
                    "nord_pool_price": nord_pool_price,
                    "actual_price": actual_price,
                    "tariff": tariff,
                    "is_holiday": is_holiday,
                    "is_weekend": is_weekend,
                }
            )

        data["hourly_prices"] = hourly_prices
        data["date"] = date
        data["is_holiday"] = is_holiday
        data["is_weekend"] = is_weekend
        data["data_available"] = True  # Flag to indicate this is real data
        return data

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(20):
                response = await self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise RealElectricityPriceApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise RealElectricityPriceApiClientCommunicationError(msg) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise RealElectricityPriceApiClientError(msg) from exception
