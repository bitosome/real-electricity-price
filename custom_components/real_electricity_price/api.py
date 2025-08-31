"""API Client for Real Electricity Price using Nord Pool."""

from __future__ import annotations

import asyncio
import datetime
import logging
import socket
from typing import Any

import aiohttp
import async_timeout
import holidays

from .const import (
    CONF_GRID_ELECTRICITY_EXCISE_DUTY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY,
    CONF_GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT,
    CONF_GRID_RENEWABLE_ENERGY_CHARGE,
    CONF_SUPPLIER_MARGIN,
    CONF_SUPPLIER_RENEWABLE_ENERGY_CHARGE,
    CONF_VAT,
    COUNTRY_CODE_DEFAULT,
    GRID_ELECTRICITY_EXCISE_DUTY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_DAY_DEFAULT,
    GRID_ELECTRICITY_TRANSMISSION_PRICE_NIGHT_DEFAULT,
    GRID_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    SUPPLIER_MARGIN_DEFAULT,
    SUPPLIER_RENEWABLE_ENERGY_CHARGE_DEFAULT,
    VAT_DEFAULT,
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
        """Get data from Nord Pool API for today and tomorrow."""
        try:
            today = datetime.datetime.now(datetime.UTC).date()
            tomorrow = today + datetime.timedelta(days=1)

            currency = self._config.get("currency", "EUR")
            market = self._config.get("market", "DayAhead")
            area = COUNTRY_CODE_DEFAULT
            token = self._config.get("token")

            headers = self._get_request_headers(token)

            # Fetch today's and tomorrow's data
            today_data = await self._fetch_day_data(today, currency, market, area, headers)
            tomorrow_data = await self._fetch_day_data(tomorrow, currency, market, area, headers)

            if not today_data:
                _LOGGER.warning("Failed to fetch today's electricity price data")
                return None

            # Process the data
            today_processed = await self._modify_prices(today_data, area, today.isoformat())
            tomorrow_processed = await self._modify_prices(tomorrow_data, area, tomorrow.isoformat()) if tomorrow_data else None

            result = {"today": today_processed}
            if tomorrow_processed:
                result["tomorrow"] = tomorrow_processed

            return result

        except Exception as exception:
            _LOGGER.error("Unexpected error in async_get_data: %s", exception)
            raise RealElectricityPriceApiClientError(f"Unexpected error: {exception}") from exception

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
        headers: dict[str, str]
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

    async def _modify_prices(self, data: dict, area: str, date: str) -> dict:
        """Modify prices with additional costs.

        This method performs some blocking work (holidays lookup and
        locale file access). Run blocking parts in the executor to avoid
        blocking the event loop.
        """
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
        vat_pct = self._config.get(CONF_VAT, VAT_DEFAULT)
        night_start = 22
        night_end = 7

        year = int(date[:4])
        # holidays.EE may perform blocking I/O (import/module locale access).
        # Run it in the default executor to avoid blocking the event loop.
        loop = asyncio.get_running_loop()
        country_holidays = await loop.run_in_executor(
            None, lambda: holidays.EE(years=year)
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
                hour = dt.hour
                
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
                                block_start_str.replace("Z", "+00:00")
                            )
                            block_end = datetime.datetime.fromisoformat(
                                block_end_str.replace("Z", "+00:00")
                            )

                            if block_start <= dt < block_end:
                                block_name = block.get("blockName", "")
                                tariff = "day" if block_name == "Peak" else "night"
                                break
                
                if (
                    is_weekend
                    or is_holiday
                    or (hour >= night_start or hour < night_end)
                ):
                    transmission = grid_electricity_transmission_price_night
                else:
                    transmission = grid_electricity_transmission_price_day

                if area in entry.get("entryPerArea", {}):
                    original_price = entry["entryPerArea"][area]
                    price = original_price / 1000  # Convert from EUR/MWh to EUR/kWh
                    price += grid_electricity_excise_duty
                    price += grid_renewable_energy_charge
                    price += supplier_renewable_energy_charge
                    price += supplier_margin
                    price += transmission
                    price *= 1 + vat_pct / 100
                    entry["entryPerArea"][area] = round(price, 6)
                    entry["price_raw_kwh"] = round(original_price / 1000, 6)

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
