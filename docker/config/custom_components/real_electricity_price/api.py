"""API Client for Real Electricity Price using Nord Pool."""

from __future__ import annotations

import datetime
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

    async def async_get_data(self) -> Any:
        """Get data from Nord Pool API for today and tomorrow."""
        today = datetime.datetime.now(datetime.UTC).date()
        tomorrow = today + datetime.timedelta(days=1)

        currency = self._config.get("currency", "EUR")
        market = self._config.get("market", "DayAhead")
        area = COUNTRY_CODE_DEFAULT
        token = self._config.get("token")

        headers = {
            "Accept": "application/json",
            "User-Agent": "real-electricity-price/1.0",
        }
        if token:
            if not token.lower().startswith("bearer "):
                token = "Bearer " + token
            headers["Authorization"] = token

        url = "https://dataportal-api.nordpoolgroup.com/api/DayAheadPrices"

        # Fetch today's data
        today_params = {
            "date": today.isoformat(),
            "market": market,
            "currency": currency,
            "deliveryArea": area,
            "deliveryAreas": area,
        }

        today_data = await self._api_wrapper(
            method="get",
            url=url,
            params=today_params,
            headers=headers,
        )
        today_processed = self._modify_prices(today_data, area, today.isoformat())

        # Fetch tomorrow's data
        tomorrow_params = {
            "date": tomorrow.isoformat(),
            "market": market,
            "currency": currency,
            "deliveryArea": area,
            "deliveryAreas": area,
        }

        tomorrow_data = await self._api_wrapper(
            method="get",
            url=url,
            params=tomorrow_params,
            headers=headers,
        )
        tomorrow_processed = self._modify_prices(
            tomorrow_data, area, tomorrow.isoformat()
        )

        # Return combined data
        return {
            "today": today_processed,
            "tomorrow": tomorrow_processed,
        }

    def _modify_prices(self, data: dict, area: str, date: str) -> dict:
        """Modify prices with additional costs."""
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
        country_holidays = holidays.EE(years=year)
        date_obj = datetime.date.fromisoformat(date)
        saturday = 5
        is_weekend = date_obj.weekday() >= saturday
        is_holiday = date_obj in country_holidays

        hourly_prices = []
        for entry in data.get("multiAreaEntries", []):
            delivery_start_str = entry.get("deliveryStart")
            if delivery_start_str:
                dt = datetime.datetime.fromisoformat(delivery_start_str)
                hour = dt.hour
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
                }
            )

        data["hourly_prices"] = hourly_prices
        data["date"] = date
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
