"""Shared helpers for cheap-hours analysis."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util


def collect_hourly_price_entries(
    data: dict[str, Any] | None,
    *,
    data_keys: Iterable[str] | None = None,
    min_start_time: datetime | None = None,
) -> list[dict[str, Any]]:
    """Collect sorted hourly price entries from coordinator-style day data."""
    if not data:
        return []

    entries: list[dict[str, Any]] = []
    keys = list(data_keys) if data_keys is not None else list(data.keys())

    for data_key in keys:
        day_data = data.get(data_key)
        if not isinstance(day_data, dict) or not day_data.get("data_available", False):
            continue

        hourly_prices = day_data.get("hourly_prices", [])
        for price_entry in hourly_prices:
            price = price_entry.get("actual_price")
            if price is None:
                continue

            try:
                start_time = dt_util.parse_datetime(price_entry["start_time"])
                if start_time is None:
                    continue
            except (TypeError, ValueError, KeyError):
                continue

            if min_start_time is not None and start_time < min_start_time:
                continue

            try:
                entries.append(
                    {
                        "start_time": price_entry["start_time"],
                        "end_time": price_entry["end_time"],
                        "price": price,
                        "start_time_dt": start_time,
                    }
                )
            except KeyError:
                continue

    entries.sort(key=lambda item: item["start_time_dt"])
    return entries


def group_consecutive_price_entries(
    cheap_prices: list[dict[str, Any]],
    *,
    round_price: Callable[[float], float] | None = None,
    include_first_price_field: bool = False,
) -> list[dict[str, Any]]:
    """Group consecutive hourly prices into ranges."""
    if not cheap_prices:
        return []

    def _round(value: float) -> float:
        return round_price(value) if round_price is not None else value

    ranges: list[dict[str, Any]] = []
    current_range: dict[str, Any] | None = None

    for price_entry in cheap_prices:
        start_time_dt = price_entry.get("start_time_dt")
        if start_time_dt is None:
            start_time_dt = dt_util.parse_datetime(price_entry["start_time"])
        if start_time_dt is None:
            continue

        price = price_entry["price"]
        if not isinstance(price, (int, float)):
            continue

        if current_range is None:
            current_range = _new_range(
                price_entry, float(price), _round, include_first_price_field
            )
            continue

        current_end_time = dt_util.parse_datetime(current_range["end_time"])
        if current_end_time is not None and start_time_dt == current_end_time:
            current_range["end_time"] = price_entry["end_time"]
            current_range["hour_count"] += 1
            current_range["prices"].append(float(price))
            current_range["min_price"] = _round(
                min(current_range["min_price"], float(price))
            )
            current_range["max_price"] = _round(
                max(current_range["max_price"], float(price))
            )
            current_range["avg_price"] = _round(
                sum(current_range["prices"]) / len(current_range["prices"])
            )
            continue

        current_range.pop("prices", None)
        ranges.append(current_range)
        current_range = _new_range(
            price_entry, float(price), _round, include_first_price_field
        )

    if current_range is not None:
        current_range.pop("prices", None)
        ranges.append(current_range)

    return ranges


def _new_range(
    price_entry: dict[str, Any],
    price: float,
    round_price: Callable[[float], float],
    include_first_price_field: bool,
) -> dict[str, Any]:
    """Create a new range object."""
    new_range: dict[str, Any] = {
        "start_time": price_entry["start_time"],
        "end_time": price_entry["end_time"],
        "hour_count": 1,
        "min_price": round_price(price),
        "max_price": round_price(price),
        "avg_price": round_price(price),
        "prices": [price],
    }
    if include_first_price_field:
        new_range["price"] = price
    return new_range
