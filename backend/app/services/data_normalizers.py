"""Turn official raw data into HOST-ready scoring inputs."""

from __future__ import annotations

from typing import Any

from ..models.schemas import BuildingData, BuildingOverridesInput, DistrictData


def clamp_score(value: float) -> int:
    return max(0, min(5, int(round(value))))


def _share(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round(value / total, 4)


def _score_ratio(value: float, anchors: list[tuple[float, float]]) -> int:
    if value <= anchors[0][0]:
        return clamp_score(anchors[0][1])

    for (left_x, left_y), (right_x, right_y) in zip(anchors, anchors[1:]):
        if value <= right_x:
            span = right_x - left_x
            progress = 0 if span == 0 else (value - left_x) / span
            return clamp_score(left_y + ((right_y - left_y) * progress))

    return clamp_score(anchors[-1][1])


def _infer_main_profiles(
    *,
    children_share: float,
    young_adults_share: float,
    adults_share: float,
    seniors_share: float,
    density: float,
    households: dict[str, Any],
) -> list[str]:
    total_households = households.get("total_households", 0.0) or 0.0
    senior_alone = households.get("elderly_women_living_alone", 0.0) + households.get("elderly_men_living_alone", 0.0)
    single_parents = households.get("single_parent_mothers", 0.0) + households.get("single_parent_fathers", 0.0)

    profile_scores = {
        "mom_with_kids": (children_share * 15) + (_share(single_parents, total_households) * 10) + 0.8,
        "businessman": (adults_share * 8) + (density / 15000),
        "teenager": (children_share * 8) + (young_adults_share * 7) + (density / 30000) + 0.7,
        "international student": (young_adults_share * 12) + (density / 25000) + 0.8,
        "retired couple": (seniors_share * 12) + (_share(senior_alone, total_households) * 10) + 0.5,
    }

    ranked = sorted(profile_scores.items(), key=lambda item: item[1], reverse=True)
    selected = [profile for profile, score in ranked if score >= 2.0][:4]
    return selected or [profile for profile, _ in ranked[:3]]


def build_host_district_from_official_data(official_data: dict[str, Any]) -> tuple[DistrictData, dict[str, Any]]:
    demographics = official_data["demographics"]
    facilities = official_data["facilities"]
    households = official_data["households"]
    population = demographics["population_total"]

    green_ratio = facilities["green_space_ha"] / (population / 10000) if population else 0.0
    sport_ratio = (facilities["sports_centers"] + facilities["basic_sports"]) / (population / 10000) if population else 0.0
    cultural_ratio = (facilities["cultural_spaces"] + facilities["libraries"]) / (population / 10000) if population else 0.0
    learning_ratio = (facilities["schools"] + facilities["libraries"]) / (population / 10000) if population else 0.0
    community_ratio = (
        facilities["senior_centers"] + facilities["family_support_centers"] + facilities["childcare_centers"] + facilities["youth_centers"]
    ) / (population / 10000) if population else 0.0
    care_ratio = (
        facilities["social_services"] + facilities["health_centers"] + facilities["addiction_centers"] + facilities["homeless_centers"]
    ) / (population / 10000) if population else 0.0

    existing_facilities = {
        "green": _score_ratio(green_ratio, [(1.5, 1), (3.0, 2), (5.0, 3), (7.5, 4), (10.0, 5)]),
        "sport": _score_ratio(sport_ratio, [(0.2, 1), (0.4, 2), (0.8, 3), (1.2, 4), (1.8, 5)]),
        "cultural": _score_ratio(cultural_ratio, [(0.2, 1), (0.4, 2), (0.7, 3), (1.0, 4), (1.4, 5)]),
        "learning": _score_ratio(learning_ratio, [(0.3, 1), (0.6, 2), (1.0, 3), (1.5, 4), (2.2, 5)]),
        "community": _score_ratio(community_ratio, [(0.2, 1), (0.4, 2), (0.7, 3), (1.0, 4), (1.5, 5)]),
        "care": _score_ratio(care_ratio, [(0.15, 1), (0.3, 2), (0.5, 3), (0.8, 4), (1.2, 5)]),
    }

    density = official_data["density_per_km2"]
    age_shares = demographics["age_shares"]
    main_profiles = _infer_main_profiles(
        children_share=age_shares["children_share"],
        young_adults_share=age_shares["young_adults_share"],
        adults_share=age_shares["adults_share"],
        seniors_share=age_shares["seniors_share"],
        density=density,
        households=households,
    )

    district: DistrictData = {
        "name": official_data["district"],
        "population": population,
        "density": density,
        "children_share": age_shares["children_share"],
        "young_adults_share": age_shares["young_adults_share"],
        "adults_share": age_shares["adults_share"],
        "seniors_share": age_shares["seniors_share"],
        "main_profiles": main_profiles,
        "existing_facilities": existing_facilities,
    }

    normalized_context = {
        "surface_ha": official_data["surface_ha"],
        "households": households,
        "facilities_raw": facilities,
        "facility_ratios_per_10000": {
            "green_ha_per_10000": round(green_ratio, 2),
            "sport_facilities_per_10000": round(sport_ratio, 2),
            "cultural_facilities_per_10000": round(cultural_ratio, 2),
            "learning_facilities_per_10000": round(learning_ratio, 2),
            "community_facilities_per_10000": round(community_ratio, 2),
            "care_facilities_per_10000": round(care_ratio, 2),
        },
    }

    return district, normalized_context


def _use_based_structure_flexibility(main_use: str) -> int:
    use_key = main_use.lower()
    if "industrial" in use_key or "almacen" in use_key:
        return 5
    if "oficina" in use_key or "comercio" in use_key:
        return 4
    if "residencial" in use_key or "vivienda" in use_key:
        return 2
    return 3


def _year_based_heritage_constraint(year: int) -> int:
    if year and year <= 1940:
        return 4
    if year and year <= 1970:
        return 3
    if year and year <= 1995:
        return 2
    return 1


def _year_based_condition(year: int) -> int:
    if year == 0:
        return 3
    if year <= 1940:
        return 2
    if year <= 1970:
        return 3
    if year <= 2000:
        return 4
    return 5


def _use_based_height(main_use: str) -> float:
    use_key = main_use.lower()
    if "oficina" in use_key or "comercio" in use_key:
        return 3.6
    if "industrial" in use_key or "almacen" in use_key:
        return 4.5
    return 3.0


def build_host_building_from_catastro(
    catastro_data: dict[str, Any],
    overrides: BuildingOverridesInput | None = None,
) -> tuple[BuildingData | None, dict[str, Any]]:
    if catastro_data.get("status") != "ok":
        return None, {"status": catastro_data.get("status", "unavailable"), "notes": catastro_data.get("notes", [])}

    year = int(catastro_data.get("construction_year") or 0)
    total_area = float(catastro_data.get("built_area_m2") or 0)
    floors = int(catastro_data.get("floor_count_observed") or 1)
    estimated_footprint = total_area / max(floors, 1) if total_area else 0.0
    estimated_plot_area = round(max(estimated_footprint * 1.1, total_area * 0.35, estimated_footprint), 2)

    building: BuildingData = {
        "name": f"{catastro_data.get('street_name', '')} {catastro_data.get('street_number', '')}".strip(),
        "total_area": total_area,
        "plot_area": estimated_plot_area,
        "floors": max(floors, 1),
        "average_height": _use_based_height(catastro_data.get("main_use", "")),
        "structure_flexibility": _use_based_structure_flexibility(catastro_data.get("main_use", "")),
        "outdoor_space": 0,
        "roof_usable": 0,
        "heritage_constraint": _year_based_heritage_constraint(year),
        "condition": _year_based_condition(year),
    }

    notes = [
        "Catastro public non-protected data does not directly expose all HOST architectural inputs.",
        "Some building fields were estimated from public descriptors such as use, year, surface, and observed floor labels.",
    ]

    if overrides is not None:
        for key, value in overrides.model_dump(exclude_none=True).items():
            building[key] = value
        notes.append("Manual building overrides were applied on top of the official Catastro data.")

    context = {
        "status": "ok",
        "notes": notes,
        "cadastral_reference": catastro_data.get("cadastral_reference", ""),
        "main_use": catastro_data.get("main_use", ""),
        "construction_year": year,
        "estimated_values": {
            "plot_area": "Estimated because the chosen public non-protected Catastro service does not directly return parcel area here.",
            "average_height": "Estimated from main use.",
            "structure_flexibility": "Estimated from main use.",
            "outdoor_space": "Unknown in public response, defaulted conservatively.",
            "roof_usable": "Unknown in public response, defaulted conservatively.",
            "heritage_constraint": "Estimated from construction year.",
            "condition": "Estimated from construction year.",
        },
    }

    return building, context
