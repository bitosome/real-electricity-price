#!/usr/bin/env python3
"""
Export states and attributes of all entities created by a Home Assistant integration.

Non-hardcoded discovery:
- Determines entities via the entity registry by config_entry_id for the given domain
  and also by registry "platform" field matching the domain (fallback).
- Supports selecting domain and config directory via CLI arguments.

Reads Home Assistant's entity registry and SQLite recorder database
from the local dev environment.

Usage:
  python3 scripts/export_integration_entities.py \
    [--domain DOMAIN] \
    [--config-dir PATH_TO_HA_CONFIG] \
    [--out OUTPUT_PATH]

Defaults (repo dev env):
  --domain: auto-detected from custom_components folder (or 'real_electricity_price' if present)
  --config-dir: container/config
  --out: <config-dir>/real_electricity_price_entities.json
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths are resolved later after CLI args
CONFIG_DIR = None  # type: ignore[assignment]
STORAGE_DIR = None  # type: ignore[assignment]
ENTITY_REG_PATH = None  # type: ignore[assignment]
CONFIG_ENTRIES_PATH = None  # type: ignore[assignment]
DB_PATH = None  # type: ignore[assignment]


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_integration_entry_ids(domain: str) -> List[str]:
    data = load_json(CONFIG_ENTRIES_PATH)
    entry_ids: List[str] = []
    # core.config_entries schema: { "data": { "entries": [ {"domain": str, "entry_id": str, ...}, ...]}}
    entries = data.get("data", {}).get("entries", [])
    for entry in entries:
        if entry.get("domain") == domain:
            eid = entry.get("entry_id")
            if isinstance(eid, str):
                entry_ids.append(eid)
    return entry_ids


@dataclass
class EntityInfo:
    entity_id: str
    unique_id: Optional[str]
    platform: Optional[str]
    entity_domain: Optional[str]
    name: Optional[str]
    original_name: Optional[str]


def get_integration_entities(entry_ids: List[str], domain: str) -> List[EntityInfo]:
    reg = load_json(ENTITY_REG_PATH)
    out: List[EntityInfo] = []
    entities = reg.get("data", {}).get("entities", [])
    for ent in entities:
        ent_id = ent.get("entity_id")
        if not ent_id:
            continue
        # Match by config_entry_id OR by registry platform == domain (fallback)
        if ent.get("config_entry_id") in entry_ids or ent.get("platform") == domain:
            ent_dom = ent_id.split(".")[0] if isinstance(ent_id, str) and "." in ent_id else None
            out.append(
                EntityInfo(
                    entity_id=ent_id,
                    unique_id=ent.get("unique_id"),
                    platform=ent.get("platform"),
                    entity_domain=ent_dom,
                    name=ent.get("name"),
                    original_name=ent.get("original_name"),
                )
            )
    return out


def has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def get_latest_state(conn: sqlite3.Connection, entity_id: str) -> Tuple[Optional[str], Optional[float], Optional[float], Dict[str, Any]]:
    """Return latest (state, last_changed_ts, last_updated_ts, attributes_dict) for entity_id.

    Uses the recorder schema states + states_meta.
    """
    # Determine time columns available
    use_ts = has_column(conn, "states", "last_updated_ts")
    time_cols = "s.last_changed_ts, s.last_updated_ts" if use_ts else "s.last_changed, s.last_updated"

    # Prefer joined attributes from state_attributes.shared_attrs when available
    has_attr_id = has_column(conn, "states", "attributes_id")
    has_state_attr = bool(
        [t for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() if t[0] == "state_attributes"]
    )
    shared_col = None
    if has_state_attr and has_attr_id and has_column(conn, "state_attributes", "shared_attrs"):
        shared_col = "sa.shared_attrs"

    attrs_expr = f"COALESCE({shared_col}, s.attributes)" if shared_col else "s.attributes"
    order_col = "s.last_updated_ts" if use_ts else "s.last_updated"

    sql = (
        f"SELECT s.state, {time_cols}, {attrs_expr} as attrs "
        "FROM states s "
        "JOIN states_meta sm ON s.metadata_id = sm.metadata_id "
        + ("LEFT JOIN state_attributes sa ON sa.attributes_id = s.attributes_id " if shared_col else "")
        + "WHERE sm.entity_id = ? "
        f"ORDER BY {order_col} DESC LIMIT 1"
    )
    cur = conn.execute(sql, (entity_id,))
    row = cur.fetchone()
    if not row:
        return None, None, None, {}

    state = row[0]
    last_changed = row[1]
    last_updated = row[2]
    attrs_raw = row[3]
    attrs: Dict[str, Any]
    try:
        if isinstance(attrs_raw, (bytes, bytearray)):
            attrs_raw = attrs_raw.decode("utf-8", "ignore")
        attrs = json.loads(attrs_raw) if isinstance(attrs_raw, str) else {}
    except Exception:
        attrs = {"_error": "failed_to_parse_attributes"}
    return state, last_changed, last_updated, attrs


def _auto_detect_domain(default: Optional[str] = None) -> str:
    """Try to auto-detect the integration domain from custom_components."""
    cc_dir = os.path.join(ROOT, "custom_components")
    candidates = []
    if os.path.isdir(cc_dir):
        for name in os.listdir(cc_dir):
            if os.path.isdir(os.path.join(cc_dir, name)) and not name.startswith("__"):
                candidates.append(name)
    if default and default in candidates:
        return default
    if len(candidates) == 1:
        return candidates[0]
    # Fallback to known domain if present
    if "real_electricity_price" in candidates:
        return "real_electricity_price"
    # As last resort
    return default or "real_electricity_price"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=None, help="Integration domain (e.g., real_electricity_price)")
    parser.add_argument("--config-dir", default=None, help="Path to Home Assistant config directory")
    parser.add_argument("--out", default=None, help="Output JSON path")
    args = parser.parse_args()

    # Resolve config dir
    cfg_dir = args.config_dir or os.path.join(ROOT, "container", "config")
    global CONFIG_DIR, STORAGE_DIR, ENTITY_REG_PATH, CONFIG_ENTRIES_PATH, DB_PATH
    CONFIG_DIR = cfg_dir
    STORAGE_DIR = os.path.join(CONFIG_DIR, ".storage")
    ENTITY_REG_PATH = os.path.join(STORAGE_DIR, "core.entity_registry")
    CONFIG_ENTRIES_PATH = os.path.join(STORAGE_DIR, "core.config_entries")
    DB_PATH = os.path.join(CONFIG_DIR, "home-assistant_v2.db")

    # Resolve domain dynamically if not provided
    domain = args.domain or _auto_detect_domain()

    # Resolve output path
    out_default = os.path.join(CONFIG_DIR, f"{domain}_entities.json")
    out_path = args.out or out_default

    if not os.path.exists(STORAGE_DIR):
        raise SystemExit(f"Storage directory not found: {STORAGE_DIR}")
    if not os.path.exists(ENTITY_REG_PATH):
        raise SystemExit(f"Entity registry not found: {ENTITY_REG_PATH}")
    if not os.path.exists(CONFIG_ENTRIES_PATH):
        raise SystemExit(f"Config entries not found: {CONFIG_ENTRIES_PATH}")

    entry_ids = get_integration_entry_ids(domain)
    if not entry_ids:
        raise SystemExit(f"No config entries found for domain '{domain}'.")

    entities = get_integration_entities(entry_ids, domain)

    results: List[Dict[str, Any]] = []
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        try:
            for info in entities:
                state, last_changed, last_updated, attrs = get_latest_state(conn, info.entity_id)
                results.append(
                    {
                        "entity_id": info.entity_id,
                        "name": info.name or info.original_name,
                        "platform": info.platform,
                        "unique_id": info.unique_id,
                        "state": state,
                        "last_changed": last_changed,
                        "last_updated": last_updated,
                        "attributes": attrs,
                    }
                )
        finally:
            conn.close()
    else:
        # DB not present; export registry info only
        for info in entities:
            results.append(
                {
                    "entity_id": info.entity_id,
                    "name": info.name or info.original_name,
                    "platform": info.platform,
                    "unique_id": info.unique_id,
                    "state": None,
                    "last_changed": None,
                    "last_updated": None,
                    "attributes": {},
                }
            )

    # Write output
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"integration": "real_electricity_price", "entities": results}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(results)} entities to {out_path}")


if __name__ == "__main__":
    main()
