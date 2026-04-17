"""Orchestration helpers for the new real-data routes."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from copy import deepcopy
from typing import Any

from ..data.catalog import DISTRICT_DATA
from ..models.schemas import BuildingOverridesInput, OfficialAddressInput
from .cache_utils import load_json_cache, store_json_cache
from .catastro_api import CatastroApiError, get_catastro_coordinates, lookup_catastro_by_address
from .data_normalizers import build_host_building_from_catastro, build_host_district_from_official_data
from .ine_api import IneApiError, clear_ine_cache, get_madrid_city_household_statistics
from .madrid_api import MadridOpenDataError, clear_madrid_cache, get_madrid_district_official_data, normalize_district_name
from .scoring_engine import calculate_architectural_capacity_index, run_district_only_analysis, run_full_analysis


class RealDataServiceError(RuntimeError):
    """Raised when a real-data endpoint cannot assemble enough information."""


DISTRICT_CACHE_TTL_SECONDS = 60 * 60 * 6
BUILDING_CACHE_TTL_SECONDS = 60 * 60 * 24
PROPOSAL_CACHE_TTL_SECONDS = 60 * 60 * 6
DISTRICT_ASSEMBLY_TIMEOUT_SECONDS = 6


def _refresh_if_needed(refresh: bool) -> None:
    if refresh:
        clear_madrid_cache()
        clear_ine_cache()


def _district_cache_key(district_name: str) -> str:
    return f"real_district_v1:{normalize_district_name(district_name)}"


def _building_cache_key(address: OfficialAddressInput, overrides: BuildingOverridesInput | None) -> str:
    overrides_payload = overrides.model_dump(exclude_none=True) if overrides else {}
    return f"real_building_v1:{address.model_dump()}:{overrides_payload}"


def _proposal_cache_key(
    district_name: str,
    address: OfficialAddressInput | None,
    overrides: BuildingOverridesInput | None,
) -> str:
    normalized_address = address.model_dump() if address else {}
    overrides_payload = overrides.model_dump(exclude_none=True) if overrides else {}
    return f"real_proposal_v1:{normalize_district_name(district_name)}:{normalized_address}:{overrides_payload}"


def _fallback_district_payload(district_name: str, *, reason: str, ine_context: dict[str, Any] | None) -> dict[str, Any]:
    requested_key = normalize_district_name(district_name)
    local_match = next(
        (deepcopy(district) for district in DISTRICT_DATA.values() if normalize_district_name(district["name"]) == requested_key),
        None,
    )

    if local_match is None:
        local_match = {
            "name": district_name.title(),
            "population": 150000,
            "density": 18000,
            "children_share": 0.14,
            "young_adults_share": 0.18,
            "adults_share": 0.43,
            "seniors_share": 0.25,
            "main_profiles": [
                "mom_with_kids",
                "businessman",
                "retired couple",
                "teenager",
            ],
            "existing_facilities": {
                "green": 3,
                "sport": 3,
                "cultural": 3,
                "learning": 3,
                "community": 3,
                "care": 3,
            },
        }

    population = local_match["population"]
    age_groups = {
        "children": round(population * local_match["children_share"]),
        "young_adults": round(population * local_match["young_adults_share"]),
        "adults": round(population * local_match["adults_share"]),
        "seniors": round(population * local_match["seniors_share"]),
    }
    households = (ine_context or {}).get("households", {})
    district_preview = run_district_only_analysis(local_match)

    return {
        "district": local_match["name"],
        "normalized_district": local_match,
        "indices_preview": district_preview,
        "profile_programs": district_preview["profile_programs"],
        "official_sources": {
            "madrid_open_data": {
                "status": "unavailable",
                "error": reason,
                "mode": "local_fallback_snapshot",
            },
            "ine": (ine_context or {}).get("source", {}),
        },
        "raw_summary": {
            "population_total": population,
            "surface_ha": None,
            "density_per_km2": local_match["density"],
            "age_groups": age_groups,
            "households": households,
            "facilities": local_match["existing_facilities"],
            "source": {
                "mode": "local_fallback_snapshot",
                "reason": reason,
            },
        },
        "supplemental_city_context": ine_context or {},
        "notes": [
            "Madrid Open Data was temporarily unavailable, so HOST used a local fallback district snapshot to keep the proposal flow working.",
            reason,
        ],
    }


def get_real_district_payload(district_name: str, *, refresh: bool = False) -> dict[str, Any]:
    _refresh_if_needed(refresh)

    cache_key = _district_cache_key(district_name)
    if not refresh:
        cached = load_json_cache(cache_key, ttl_seconds=DISTRICT_CACHE_TTL_SECONDS)
        if cached is not None:
            return cached

    official_data = None
    ine_context: dict[str, Any] = {}
    madrid_error: str | None = None
    ine_error: str | None = None

    with ThreadPoolExecutor(max_workers=2) as executor:
        official_future = executor.submit(get_madrid_district_official_data, district_name)
        ine_future = executor.submit(get_madrid_city_household_statistics)

        try:
            official_data = official_future.result(timeout=DISTRICT_ASSEMBLY_TIMEOUT_SECONDS)
        except MadridOpenDataError as exc:
            madrid_error = str(exc)
        except TimeoutError as exc:
            madrid_error = "Madrid official district request exceeded the response time budget"

        try:
            ine_context = ine_future.result(timeout=DISTRICT_ASSEMBLY_TIMEOUT_SECONDS)
        except IneApiError as exc:
            ine_error = str(exc)
            ine_context = {
                "households": {},
                "source": {
                    "status": "unavailable",
                    "error": ine_error,
                    "mode": "missing_official_context",
                },
            }
        except TimeoutError:
            ine_error = "INE household context request exceeded the response time budget"
            ine_context = {
                "households": {},
                "source": {
                    "status": "unavailable",
                    "error": ine_error,
                    "mode": "missing_official_context",
                },
            }

    if official_data is None:
        payload = _fallback_district_payload(
            district_name,
            reason=madrid_error or "No official Madrid district payload was available.",
            ine_context=ine_context,
        )
        if ine_error:
            payload["notes"].append("INE household context was also unavailable, so household-based inference was reduced.")
        store_json_cache(cache_key, payload)
        return payload

    district_data, normalized_context = build_host_district_from_official_data(official_data)

    notes = [
        "District data comes from official Madrid Open Data datasets and supplementary INE municipal statistics.",
        "HOST facility scores are normalized from official counts and area metrics into a 0-5 adequacy scale before scoring.",
    ]
    if ine_error:
        notes[0] = "District data comes from official Madrid Open Data datasets."
        notes.append("INE household context was unavailable for this request, so household-based inference was reduced.")

    district_preview = run_district_only_analysis(district_data)

    payload = {
        "district": district_data["name"],
        "normalized_district": district_data,
        "indices_preview": district_preview,
        "profile_programs": district_preview["profile_programs"],
        "official_sources": {
            "madrid_open_data": official_data["sources"],
            "ine": ine_context["source"],
        },
        "raw_summary": {
            "population_total": official_data["demographics"]["population_total"],
            "surface_ha": official_data["surface_ha"],
            "density_per_km2": official_data["density_per_km2"],
            "age_groups": official_data["demographics"]["age_groups"],
            "households": normalized_context["households"],
            "facilities": normalized_context["facilities_raw"],
        },
        "supplemental_city_context": ine_context,
        "notes": notes,
    }
    store_json_cache(cache_key, payload)
    return payload


def get_real_building_payload(
    address: OfficialAddressInput,
    *,
    overrides: BuildingOverridesInput | None = None,
) -> dict[str, Any]:
    cache_key = _building_cache_key(address, overrides)
    cached = load_json_cache(cache_key, ttl_seconds=BUILDING_CACHE_TTL_SECONDS)
    if cached is not None:
        return cached

    try:
        catastro_data = lookup_catastro_by_address(address)
    except CatastroApiError as exc:
        raise RealDataServiceError(str(exc)) from exc

    building_data, normalization_context = build_host_building_from_catastro(catastro_data, overrides)
    payload = {
        "requested_address": address.model_dump(),
        "lookup_status": catastro_data.get("status", "unavailable"),
        "official_sources": {"catastro": catastro_data.get("source", {})},
        "raw_catastro": catastro_data,
        "notes": normalization_context.get("notes", []),
    }

    if catastro_data.get("status") == "ok":
        try:
            location_preview = get_catastro_coordinates(
                cadastral_reference=catastro_data.get("parcel_cadastral_reference", ""),
                province=address.province,
                municipality=address.municipality,
            )
        except CatastroApiError:
            location_preview = None

        if location_preview is not None:
            payload["location_preview"] = location_preview

    if building_data is not None:
        payload["normalized_building"] = building_data
        payload["architectural_capacity_index"] = calculate_architectural_capacity_index(building_data)
        payload["normalization_context"] = normalization_context

    store_json_cache(cache_key, payload)
    return payload


def get_real_proposal_payload(
    district_name: str,
    *,
    address: OfficialAddressInput | None = None,
    overrides: BuildingOverridesInput | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    cache_key = _proposal_cache_key(district_name, address, overrides)
    if not refresh:
        cached = load_json_cache(cache_key, ttl_seconds=PROPOSAL_CACHE_TTL_SECONDS)
        if cached is not None:
            return cached

    if address is None:
        district_payload = get_real_district_payload(district_name, refresh=refresh)
        if not district_payload:
            return {}
        payload = {
            **district_payload,
            "proposal_status": "partial",
            "notes": district_payload["notes"] + ["No structured building address was provided, so only district-level analysis is available."],
        }
        store_json_cache(cache_key, payload)
        return payload

    if refresh:
        district_payload = get_real_district_payload(district_name, refresh=True)
        if not district_payload:
            return {}
        building_payload = get_real_building_payload(address, overrides=overrides)
    else:
        with ThreadPoolExecutor(max_workers=2) as executor:
            district_future = executor.submit(get_real_district_payload, district_name, refresh=False)
            building_future = executor.submit(get_real_building_payload, address, overrides=overrides)
            district_payload = district_future.result()
            building_payload = building_future.result()

    if not district_payload:
        return {}

    normalized_building = building_payload.get("normalized_building")
    if normalized_building is None:
        payload = {
            **district_payload,
            "proposal_status": "partial",
            "building_lookup": building_payload,
            "notes": district_payload["notes"] + ["The building lookup did not return a detailed single Catastro property, so a full proposal could not be generated."],
        }
        store_json_cache(cache_key, payload)
        return payload

    proposal = run_full_analysis(district_payload["normalized_district"], normalized_building)
    payload = {
        "proposal_status": "ok",
        "district_data": district_payload["normalized_district"],
        "building_data": normalized_building,
        "proposal": proposal,
        "location_preview": building_payload.get("location_preview"),
        "official_sources": {
            "district": district_payload["official_sources"],
            "building": building_payload["official_sources"],
        },
        "district_context": district_payload["raw_summary"],
        "building_context": building_payload.get("normalization_context", {}),
        "notes": district_payload["notes"] + building_payload.get("notes", []),
    }
    store_json_cache(cache_key, payload)
    return payload
