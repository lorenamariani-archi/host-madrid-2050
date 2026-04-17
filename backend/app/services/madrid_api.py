"""Official Madrid Open Data access layer."""

from __future__ import annotations

import csv
import io
import json
import unicodedata
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .cache_utils import load_json_cache, store_json_cache

REQUEST_TIMEOUT_SECONDS = 8
PUBLIC_DATA_CACHE_TTL_SECONDS = 60 * 60 * 24
DISTRICT_FETCH_TIMEOUT_SECONDS = 5
MADRID_CKAN_PACKAGE_SHOW_URL = "https://datos.madrid.es/api/3/action/package_show?id={dataset_id}"
PADRON_DATASET_IDS = [
    "200076-0-padron",
    "209163-0-padron-municipal-historico",
]
PANEL_DATASET_ID = "300087-0-indicadores-distritos"
PUBLIC_SCHOOLS_DATASET_ID = "202311-0-colegios-publicos"
PADRON_FALLBACK_RESOURCES = [
    {
        "dataset_id": "209163-0-padron-municipal-historico",
        "dataset_title": "Padrón municipal. Histórico",
        "resource_url": (
            "https://datos.madrid.es/dataset/209163-0-padron-municipal-historico/"
            "resource/209163-335-padron-municipal-historico/download/"
            "209163_export_20260315_095313_json.json"
        ),
        "data_period_start": "2026-03-01",
        "data_period_end": "2026-03-31",
        "note": (
            "Official fallback resource used because the CKAN package_show endpoint was unavailable "
            "or in maintenance."
        ),
    }
]


class MadridOpenDataError(RuntimeError):
    """Raised when Madrid open data cannot be fetched or parsed."""


def normalize_district_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_name.upper().split())


def parse_madrid_decimal(value: Any) -> float:
    text = str(value).strip().replace(".", "").replace(",", ".")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _fetch_json(url: str) -> Any:
    try:
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "HOST-FastAPI-Backend/0.1.0"})
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_bytes = response.read()
        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw_bytes.decode("latin-1", errors="replace")
        stripped = text.lstrip()
        if stripped.startswith("<!DOCTYPE html") or stripped.startswith("<html"):
            raise MadridOpenDataError(f"Madrid open data returned an HTML maintenance page for {url}")
        return json.loads(text)
    except (URLError, ValueError, json.JSONDecodeError) as exc:
        raise MadridOpenDataError(f"Unable to fetch Madrid open data from {url}") from exc


def _fetch_csv_rows(url: str) -> list[dict[str, str]]:
    try:
        request = Request(url, headers={"User-Agent": "HOST-FastAPI-Backend/0.1.0"})
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_bytes = response.read()
            try:
                text = raw_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw_bytes.decode("latin-1", errors="replace")
        return list(csv.DictReader(io.StringIO(text), delimiter=";"))
    except (URLError, csv.Error) as exc:
        raise MadridOpenDataError(f"Unable to fetch Madrid CSV data from {url}") from exc


def _extract_json_resource_url(resources: list[dict[str, Any]]) -> str:
    for resource in resources:
        if str(resource.get("format", "")).upper() == "JSON" and resource.get("url"):
            return str(resource["url"])
    raise MadridOpenDataError("The requested Madrid dataset does not expose a JSON resource")


def _resource_timestamp(resource: dict[str, Any]) -> str:
    for key in ("last_modified", "metadata_modified", "created"):
        value = str(resource.get(key, "")).strip()
        if value:
            return value
    return ""


def _extract_latest_json_resource(resources: list[dict[str, Any]]) -> dict[str, Any]:
    json_resources = [
        resource
        for resource in resources
        if str(resource.get("format", "")).upper() == "JSON" and resource.get("url")
    ]
    if not json_resources:
        raise MadridOpenDataError("The requested Madrid dataset does not expose a JSON resource")
    return max(json_resources, key=_resource_timestamp)


def _extract_csv_resource_url(resources: list[dict[str, Any]]) -> str:
    for resource in resources:
        if str(resource.get("format", "")).upper() == "CSV" and resource.get("url"):
            return str(resource["url"])
    raise MadridOpenDataError("The requested Madrid dataset does not expose a CSV resource")


def _dataset_metadata(dataset_id: str) -> dict[str, Any]:
    metadata = _fetch_json(MADRID_CKAN_PACKAGE_SHOW_URL.format(dataset_id=dataset_id))
    result = metadata.get("result", {})
    return {
        "dataset_id": dataset_id,
        "dataset_title": result.get("title", dataset_id),
        "resources": result.get("resources", []),
    }


def _to_iso_date(raw_value: Any) -> str:
    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(raw_value / 1000, tz=UTC).date().isoformat()

    text_value = str(raw_value).strip()
    if "T" in text_value:
        return text_value.split("T", maxsplit=1)[0]
    return text_value[:10]


def _padron_source_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for dataset_id in PADRON_DATASET_IDS:
        try:
            metadata = _dataset_metadata(dataset_id)
            resource = _extract_latest_json_resource(metadata["resources"])
            candidates.append(
                {
                    "dataset_id": metadata["dataset_id"],
                    "dataset_title": metadata["dataset_title"],
                    "resource_url": str(resource["url"]),
                }
            )
        except MadridOpenDataError:
            continue

    candidates.extend(dict(resource) for resource in PADRON_FALLBACK_RESOURCES)
    return candidates


@lru_cache(maxsize=1)
def load_madrid_demographics() -> dict[str, dict[str, Any]]:
    cached = load_json_cache("madrid_demographics_v1", ttl_seconds=PUBLIC_DATA_CACHE_TTL_SECONDS)
    if cached is not None:
        return cached

    last_errors: list[str] = []
    rows: list[dict[str, Any]] | None = None
    source: dict[str, Any] | None = None

    for candidate in _padron_source_candidates():
        try:
            rows = _fetch_json(candidate["resource_url"])
            source = candidate
            break
        except MadridOpenDataError as exc:
            last_errors.append(str(exc))

    if rows is None or source is None:
        joined_errors = " | ".join(last_errors[:3]) if last_errors else "No Madrid padrón source was available."
        raise MadridOpenDataError(joined_errors)

    resource_url = source["resource_url"]

    district_index: dict[str, dict[str, Any]] = {}

    for row in rows:
        district_label = str(row.get("DESC_DISTRITO", "")).strip()
        if not district_label:
            continue

        district_key = normalize_district_name(district_label)
        total = (
            int(row.get("ESPANOLESHOMBRES", 0))
            + int(row.get("ESPANOLESMUJERES", 0))
            + int(row.get("EXTRANJEROSHOMBRES", 0))
            + int(row.get("EXTRANJEROSMUJERES", 0))
        )
        digits = "".join(char for char in str(row.get("COD_EDAD_INT", "0")) if char.isdigit())
        age = int(digits) if digits else 0

        district = district_index.setdefault(
            district_key,
            {
                "district": district_label.title(),
                "population_total": 0,
                "children": 0,
                "young_adults": 0,
                "adults": 0,
                "seniors": 0,
                "spanish": 0,
                "foreign": 0,
                "male": 0,
                "female": 0,
                "source": {
                    "dataset_id": source["dataset_id"],
                    "dataset_title": source["dataset_title"],
                    "resource_url": resource_url,
                    "data_period_start": source.get("data_period_start") or _to_iso_date(row.get("FX_DATOS_INI", "")),
                    "data_period_end": source.get("data_period_end") or _to_iso_date(row.get("FX_DATOS_FIN", "")),
                    "note": source.get("note", ""),
                },
            },
        )

        district["population_total"] += total
        district["spanish"] += int(row.get("ESPANOLESHOMBRES", 0)) + int(row.get("ESPANOLESMUJERES", 0))
        district["foreign"] += int(row.get("EXTRANJEROSHOMBRES", 0)) + int(row.get("EXTRANJEROSMUJERES", 0))
        district["male"] += int(row.get("ESPANOLESHOMBRES", 0)) + int(row.get("EXTRANJEROSHOMBRES", 0))
        district["female"] += int(row.get("ESPANOLESMUJERES", 0)) + int(row.get("EXTRANJEROSMUJERES", 0))

        if age <= 14:
            district["children"] += total
        elif age <= 29:
            district["young_adults"] += total
        elif age <= 64:
            district["adults"] += total
        else:
            district["seniors"] += total

    for district in district_index.values():
        total = max(district["population_total"], 1)
        district["age_groups"] = {
            "children": district.pop("children"),
            "young_adults": district.pop("young_adults"),
            "adults": district.pop("adults"),
            "seniors": district.pop("seniors"),
        }
        district["age_shares"] = {
            "children_share": round(district["age_groups"]["children"] / total, 4),
            "young_adults_share": round(district["age_groups"]["young_adults"] / total, 4),
            "adults_share": round(district["age_groups"]["adults"] / total, 4),
            "seniors_share": round(district["age_groups"]["seniors"] / total, 4),
        }
        district["nationality_breakdown"] = {
            "spanish": district.pop("spanish"),
            "foreign": district.pop("foreign"),
        }
        district["gender_breakdown"] = {
            "male": district.pop("male"),
            "female": district.pop("female"),
        }

    store_json_cache("madrid_demographics_v1", district_index)
    return district_index


@lru_cache(maxsize=1)
def load_panel_indicators() -> list[dict[str, str]]:
    cached = load_json_cache("madrid_panel_indicators_v1", ttl_seconds=PUBLIC_DATA_CACHE_TTL_SECONDS)
    if cached is not None:
        return cached

    metadata = _dataset_metadata(PANEL_DATASET_ID)
    resource_url = _extract_csv_resource_url(metadata["resources"])
    rows = _fetch_csv_rows(resource_url)
    store_json_cache("madrid_panel_indicators_v1", rows)
    return rows


@lru_cache(maxsize=1)
def load_public_schools_by_district() -> dict[str, int]:
    cached = load_json_cache("madrid_public_schools_v1", ttl_seconds=PUBLIC_DATA_CACHE_TTL_SECONDS)
    if cached is not None:
        return cached

    metadata = _dataset_metadata(PUBLIC_SCHOOLS_DATASET_ID)
    resource_url = _extract_csv_resource_url(metadata["resources"])
    rows = _fetch_csv_rows(resource_url)

    counts: dict[str, int] = {}
    for row in rows:
        district_name = row.get("DISTRITO", "")
        if not district_name:
            continue
        district_key = normalize_district_name(district_name)
        counts[district_key] = counts.get(district_key, 0) + 1

    store_json_cache("madrid_public_schools_v1", counts)
    return counts


def _district_level_panel_rows(district_name: str) -> list[dict[str, str]]:
    district_key = normalize_district_name(district_name)
    return [
        row
        for row in load_panel_indicators()
        if normalize_district_name(row.get("distrito", "")) == district_key and not row.get("cod_barrio")
    ]


def get_district_panel_snapshot(district_name: str) -> dict[str, Any] | None:
    rows = _district_level_panel_rows(district_name)
    if not rows:
        return None

    snapshot: dict[str, dict[str, Any]] = {}
    for row in rows:
        indicator_name = row.get("indicador_completo", "").strip()
        year = int(parse_madrid_decimal(row.get("año", 0)))
        current = snapshot.get(indicator_name)
        if current is None or year > current["year"]:
            snapshot[indicator_name] = {
                "value": row.get("valor_indicador", ""),
                "numeric_value": parse_madrid_decimal(row.get("valor_indicador", "")),
                "year": year,
                "unit": row.get("unidad_indicador", ""),
                "source": row.get("fuente_indicador", ""),
            }

    return snapshot


def get_madrid_district_demographics(
    district_name: str,
    *,
    refresh: bool = False,
) -> dict[str, Any] | None:
    if refresh:
        clear_madrid_cache()
    return load_madrid_demographics().get(normalize_district_name(district_name))


def get_madrid_district_official_data(
    district_name: str,
    *,
    refresh: bool = False,
) -> dict[str, Any] | None:
    if refresh:
        clear_madrid_cache()

    with ThreadPoolExecutor(max_workers=3) as executor:
        demographics_future = executor.submit(get_madrid_district_demographics, district_name)
        panel_future = executor.submit(get_district_panel_snapshot, district_name)
        schools_future = executor.submit(load_public_schools_by_district)

        try:
            demographics = demographics_future.result(timeout=DISTRICT_FETCH_TIMEOUT_SECONDS)
            panel = panel_future.result(timeout=DISTRICT_FETCH_TIMEOUT_SECONDS)
            schools_by_district = schools_future.result(timeout=DISTRICT_FETCH_TIMEOUT_SECONDS)
        except TimeoutError as exc:
            raise MadridOpenDataError("Madrid official data timed out before the district snapshot could be assembled") from exc

    if demographics is None or panel is None:
        return None

    facilities = {
        "green_space_ha": panel.get("Superficie de zonas verdes y parques de distrito (ha.)", {}).get("numeric_value", 0.0),
        "cultural_spaces": panel.get("Centros y espacios culturales", {}).get("numeric_value", 0.0),
        "libraries": (
            panel.get("Bibliotecas municipales", {}).get("numeric_value", 0.0)
            + panel.get("Bibliotecas Comunidad Madrid", {}).get("numeric_value", 0.0)
        ),
        "sports_centers": panel.get("Centros deportivos municipales", {}).get("numeric_value", 0.0),
        "basic_sports": panel.get("Instalaciones deportivas básicas", {}).get("numeric_value", 0.0),
        "social_services": panel.get("Centros de servicios sociales", {}).get("numeric_value", 0.0),
        "senior_centers": panel.get("Centros municipales de mayores", {}).get("numeric_value", 0.0),
        "family_support_centers": panel.get("Centros de apoyo a las familias (CAF)", {}).get("numeric_value", 0.0),
        "childcare_centers": panel.get("Centros de atención a la infancia (CAI)", {}).get("numeric_value", 0.0),
        "youth_centers": panel.get("Espacios de ocio para adolescentes (El Enredadero)", {}).get("numeric_value", 0.0),
        "health_centers": panel.get("Centros municipales de salud comunitaria (CMSC)", {}).get("numeric_value", 0.0),
        "addiction_centers": panel.get("Centros de atención a las adicciones (CAD y CCAD)", {}).get("numeric_value", 0.0),
        "homeless_centers": panel.get("Centros para personas sin hogar", {}).get("numeric_value", 0.0),
        "schools": float(schools_by_district.get(normalize_district_name(district_name), 0)),
    }

    households = {
        "total_households": panel.get("Total hogares", {}).get("numeric_value", 0.0),
        "average_household_size": panel.get("Tamaño medio del hogar", {}).get("numeric_value", 0.0),
        "elderly_women_living_alone": panel.get("Hogares con una mujer sola mayor de 65 años", {}).get("numeric_value", 0.0),
        "elderly_men_living_alone": panel.get("Hogares con un hombre solo mayor de 65 años", {}).get("numeric_value", 0.0),
        "single_parent_mothers": panel.get("Hogares monoparentales: una mujer adulta con uno o más menores", {}).get("numeric_value", 0.0),
        "single_parent_fathers": panel.get("Hogares monoparentales: un hombre adulto con uno o más menores", {}).get("numeric_value", 0.0),
    }

    surface_ha = panel.get("Superficie (ha.)", {}).get("numeric_value", 0.0)
    population = demographics["population_total"]
    density = round(population / (surface_ha / 100), 2) if surface_ha else 0.0

    return {
        "district": demographics["district"],
        "demographics": demographics,
        "surface_ha": surface_ha,
        "density_per_km2": density,
        "households": households,
        "facilities": facilities,
        "panel_indicators": panel,
        "sources": {
            "demographics": demographics["source"],
            "panel": {
                "dataset_id": PANEL_DATASET_ID,
                "dataset_title": "Panel de indicadores de distritos y barrios de Madrid",
            },
        },
    }


def clear_madrid_cache() -> None:
    load_madrid_demographics.cache_clear()
    load_panel_indicators.cache_clear()
    load_public_schools_by_district.cache_clear()
