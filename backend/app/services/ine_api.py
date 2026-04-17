"""Official INE JSON API helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .cache_utils import load_json_cache, store_json_cache

INE_BASE_URL = "https://servicios.ine.es/wstempus/js/es"
MADRID_MUNICIPALITY_CODE = "28079 Madrid"
HOUSEHOLD_SIZE_TABLE_ID = "59543"
HOUSEHOLD_TYPE_TABLE_ID = "59544"
REQUEST_TIMEOUT_SECONDS = 6
INE_CACHE_TTL_SECONDS = 60 * 60 * 24


class IneApiError(RuntimeError):
    """Raised when the INE API cannot be reached or parsed."""


def _fetch_json(url: str) -> Any:
    try:
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "HOST-FastAPI-Backend/0.1.0"})
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            import json

            return json.load(response)
    except (URLError, ValueError) as exc:
        raise IneApiError(f"Unable to fetch INE data from {url}") from exc


def _share(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round(value / total, 4)


def _extract_madrid_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("Nombre", "")).startswith(MADRID_MUNICIPALITY_CODE)]


@lru_cache(maxsize=1)
def get_madrid_city_household_statistics() -> dict[str, Any]:
    cached = load_json_cache("ine_madrid_households_v1", ttl_seconds=INE_CACHE_TTL_SECONDS)
    if cached is not None:
        return cached

    size_rows = _extract_madrid_rows(
        _fetch_json(f"{INE_BASE_URL}/DATOS_TABLA/{HOUSEHOLD_SIZE_TABLE_ID}")
    )
    type_rows = _extract_madrid_rows(
        _fetch_json(f"{INE_BASE_URL}/DATOS_TABLA/{HOUSEHOLD_TYPE_TABLE_ID}")
    )

    total_households = int(size_rows[0]["Data"][0]["Valor"]) if size_rows else 0

    household_size = {}
    for row in size_rows[1:]:
        name = row["Nombre"].split(", ", maxsplit=1)[1]
        value = int(row["Data"][0]["Valor"])
        household_size[name] = {"count": value, "share": _share(value, total_households)}

    household_type = {}
    for row in type_rows[1:]:
        name = row["Nombre"].split(", ", maxsplit=2)[2]
        value = int(row["Data"][0]["Valor"])
        household_type[name] = {"count": value, "share": _share(value, total_households)}

    payload = {
        "municipality": "Madrid",
        "household_size_distribution": household_size,
        "household_type_distribution": household_type,
        "total_households": total_households,
        "source": {
            "provider": "INE",
            "table_ids": [HOUSEHOLD_SIZE_TABLE_ID, HOUSEHOLD_TYPE_TABLE_ID],
            "base_url": INE_BASE_URL,
        },
    }
    store_json_cache("ine_madrid_households_v1", payload)
    return payload


def clear_ine_cache() -> None:
    get_madrid_city_household_statistics.cache_clear()
