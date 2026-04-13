"""Core scoring and proposal logic.

This module is intentionally separate from API clients. The goal is that the
scoring engine can be tested and explained on its own, whether the inputs come
from demo dictionaries, Madrid Open Data, Catastro, or future sources.
"""

from typing import Any

from ..data.catalog import (
    CATEGORY_KEYS,
    CATEGORY_LABELS,
    CLIMATE_CATEGORY_BONUS,
    CLIMATE_STRATEGIES,
    PROFILE_DISPLAY_ORDER,
    PROFILE_NEEDS,
)
from ..models.schemas import BuildingData, DistrictData
from .climate_service import calculate_climate_future_risk_index


def clamp_0_5(value: float) -> float:
    return max(0, min(5, round(value, 2)))


def interpolate_score(value: float, anchors: list[tuple[float, float]]) -> float:
    if value <= anchors[0][0]:
        return clamp_0_5(anchors[0][1])

    for (left_x, left_y), (right_x, right_y) in zip(anchors, anchors[1:]):
        if value <= right_x:
            span = right_x - left_x
            if span == 0:
                return clamp_0_5(right_y)
            progress = (value - left_x) / span
            return clamp_0_5(left_y + ((right_y - left_y) * progress))

    return clamp_0_5(anchors[-1][1])


def likert_score(value: int, mapping: dict[int, float]) -> float:
    return clamp_0_5(mapping.get(value, float(value)))


def score_total_area(total_area: float) -> float:
    return interpolate_score(
        total_area,
        [
            (1500, 1.0),
            (3000, 2.0),
            (6000, 3.1),
            (10000, 4.2),
            (16000, 5.0),
        ],
    )


def score_average_floor_plate(building: BuildingData) -> float:
    floors = max(building["floors"], 1)
    average_floor_plate = building["total_area"] / floors
    return interpolate_score(
        average_floor_plate,
        [
            (500, 1.0),
            (1000, 2.1),
            (1800, 3.4),
            (2600, 4.3),
            (4000, 5.0),
        ],
    )


def score_floor_configuration(floors: int) -> float:
    return interpolate_score(
        floors,
        [
            (1, 2.2),
            (2, 4.1),
            (3, 5.0),
            (4, 4.7),
            (5, 4.0),
            (6, 3.2),
            (8, 2.5),
        ],
    )


def score_spatial_height(height: float) -> float:
    return interpolate_score(
        height,
        [
            (3, 1.0),
            (4, 2.2),
            (5, 3.4),
            (6, 4.2),
            (8, 5.0),
            (10, 4.6),
            (14, 4.0),
        ],
    )


def score_site_support_capacity(building: BuildingData) -> float:
    floors = max(building["floors"], 1)
    estimated_footprint = building["total_area"] / floors
    plot_area = max(building["plot_area"], 1)
    open_site_ratio = max(0.0, min(1.0, (plot_area - estimated_footprint) / plot_area))

    score = 1.4
    if building["outdoor_space"] == 1:
        score += 1.8
    if building["roof_usable"] == 1:
        score += 1.0
    score += open_site_ratio * 1.4

    return clamp_0_5(score)


def capacity_band(score: float) -> str:
    if score >= 4.2:
        return "high"
    if score >= 3.0:
        return "medium"
    return "low"


def calculate_architectural_capacity_index(building: BuildingData) -> dict[str, Any]:
    floors = max(building["floors"], 1)
    average_floor_plate = round(building["total_area"] / floors, 2)
    estimated_footprint_ratio = round(
        min((building["total_area"] / floors) / max(building["plot_area"], 1), 1),
        2,
    )
    estimated_open_site_ratio = round(max(0.0, 1 - estimated_footprint_ratio), 2)

    scores = {
        "gross_floor_area": score_total_area(building["total_area"]),
        "average_floor_plate": score_average_floor_plate(building),
        "floor_configuration": score_floor_configuration(building["floors"]),
        "spatial_height": score_spatial_height(building["average_height"]),
        "structure_flexibility": likert_score(
            building["structure_flexibility"],
            {1: 1.0, 2: 2.1, 3: 3.3, 4: 4.2, 5: 5.0},
        ),
        "site_support_capacity": score_site_support_capacity(building),
        "heritage_adaptability": likert_score(
            building["heritage_constraint"],
            {1: 5.0, 2: 4.3, 3: 3.4, 4: 2.4, 5: 1.4},
        ),
        "physical_condition": likert_score(
            building["condition"],
            {1: 1.0, 2: 2.2, 3: 3.3, 4: 4.2, 5: 5.0},
        ),
    }
    weights = {
        "gross_floor_area": 0.18,
        "average_floor_plate": 0.14,
        "floor_configuration": 0.10,
        "spatial_height": 0.14,
        "structure_flexibility": 0.18,
        "site_support_capacity": 0.10,
        "heritage_adaptability": 0.08,
        "physical_condition": 0.08,
    }
    final_score = round(sum(scores[key] * weights[key] for key in scores), 2)

    return {
        "score": final_score,
        "capacity_band": capacity_band(final_score),
        "details": scores,
        "weights": weights,
        "metrics": {
            "gross_floor_area_m2": building["total_area"],
            "plot_area_m2": building["plot_area"],
            "average_floor_plate_m2": average_floor_plate,
            "estimated_footprint_ratio": estimated_footprint_ratio,
            "estimated_open_site_ratio": estimated_open_site_ratio,
            "floors": building["floors"],
            "average_height_m": building["average_height"],
        },
    }


def calculate_urban_deficit_index(district: DistrictData) -> dict[str, Any]:
    ideal = 5
    deficits = {
        category: ideal - value
        for category, value in district["existing_facilities"].items()
    }
    final_score = round(sum(deficits.values()) / len(deficits), 2)
    return {"score": final_score, "details": deficits}


def calculate_demographic_pressure_index(district: DistrictData) -> dict[str, Any]:
    profile_scores: dict[str, float] = {}

    for profile in district["main_profiles"]:
        score = 0.0
        if profile == "mom_with_kids":
            score = (district["children_share"] * 15) + 1.5
        elif profile == "businessman":
            score = (district["adults_share"] * 8) + (district["density"] / 15000)
        elif profile == "teenager":
            score = (district["children_share"] * 8) + (district["young_adults_share"] * 7) + 1.2
        elif profile == "international student":
            score = (district["young_adults_share"] * 12) + 1.5
        elif profile == "retired couple":
            score = (district["seniors_share"] * 12) + 1.5

        profile_scores[profile] = clamp_0_5(score)

    final_score = round(sum(profile_scores.values()) / len(profile_scores), 2)
    return {"score": final_score, "details": profile_scores}


def build_profile_programs(district: DistrictData) -> dict[str, dict[str, Any]]:
    result = {}

    for profile in district["main_profiles"]:
        profile_needs = PROFILE_NEEDS.get(profile)
        if profile_needs is None:
            continue
        result[profile] = {
            "label": profile_needs["label"],
            "activity_text": profile_needs["activity_text"],
            "priority_categories": profile_needs["priority_categories"],
            "spaces": profile_needs["spaces"],
        }

    return result


def build_grouped_program_from_profiles(district: DistrictData) -> dict[str, list[str]]:
    grouped = {category_name: [] for category_name in CATEGORY_KEYS}

    for profile in district["main_profiles"]:
        profile_needs = PROFILE_NEEDS.get(profile)
        if profile_needs is None:
            continue

        for category_key in profile_needs["priority_categories"]:
            category_name = CATEGORY_LABELS[category_key]
            for space in profile_needs["spaces"]:
                if space not in grouped[category_name]:
                    grouped[category_name].append(space)

    return {category_name: spaces for category_name, spaces in grouped.items() if spaces}


def build_people_program_guides(
    district: DistrictData,
    selected_program: dict[str, list[str]],
) -> list[dict[str, Any]]:
    guides = []

    for profile in PROFILE_DISPLAY_ORDER:
        profile_needs = PROFILE_NEEDS.get(profile)
        if profile_needs is None:
            continue

        matched_categories = []
        for category_key in profile_needs["priority_categories"]:
            category_name = CATEGORY_LABELS[category_key]
            if category_name in selected_program:
                matched_categories.append(category_name)

        matched_spaces = profile_needs["spaces"][:4]
        if matched_categories:
            selected_spaces = {
                space
                for category_name in matched_categories
                for space in selected_program.get(category_name, [])
            }
            intersected_spaces = [space for space in profile_needs["spaces"] if space in selected_spaces]
            if intersected_spaces:
                matched_spaces = intersected_spaces[:4]

        category_count = len(matched_categories)
        is_priority_profile = profile in district["main_profiles"]
        fit_level = "support"
        if is_priority_profile and category_count >= 3:
            fit_level = "strong"
        elif is_priority_profile or category_count >= 2:
            fit_level = "good"

        guides.append(
            {
                "profile_key": profile,
                "label": profile_needs["label"],
                "fit_level": fit_level,
                "is_priority_profile": is_priority_profile,
                "matched_categories": matched_categories,
                "matched_spaces": matched_spaces,
                "activity_text": profile_needs["activity_text"],
            }
        )

    return guides


def category_building_fit(category_name: str, building: BuildingData) -> float:
    if category_name == "Green Infrastructures":
        score = 2
        if building["outdoor_space"] == 1:
            score += 2
        if building["roof_usable"] == 1:
            score += 1
        return clamp_0_5(score)

    if category_name == "Sport":
        score = 1
        if building["average_height"] >= 6:
            score += 2
        if building["structure_flexibility"] >= 4:
            score += 1
        if building["total_area"] >= 7000:
            score += 1
        return clamp_0_5(score)

    if category_name == "Cultural":
        score = 2
        if building["average_height"] >= 5:
            score += 1
        if building["heritage_constraint"] >= 3:
            score += 1
        if building["structure_flexibility"] >= 3:
            score += 1
        return clamp_0_5(score)

    if category_name == "Learning and Innovation":
        score = 2
        if building["structure_flexibility"] >= 3:
            score += 2
        if building["condition"] >= 3:
            score += 1
        return clamp_0_5(score)

    if category_name == "Community":
        score = 2
        if building["structure_flexibility"] >= 3:
            score += 1
        if building["total_area"] >= 5000:
            score += 1
        if building["condition"] >= 3:
            score += 1
        return clamp_0_5(score)

    if category_name == "Care and Social Support":
        score = 2
        if building["condition"] >= 3:
            score += 1
        if building["floors"] <= 3:
            score += 1
        if building["outdoor_space"] == 1:
            score += 1
        return clamp_0_5(score)

    return 0


def determine_program_scale(building: BuildingData) -> str:
    area = building["total_area"]

    if area >= 15000:
        return "metropolitan"
    if area >= 10000:
        return "large"
    if area >= 6000:
        return "medium"
    return "small"


def calculate_category_scores(
    district: DistrictData,
    building: BuildingData,
) -> dict[str, dict[str, float]]:
    urban_deficit = calculate_urban_deficit_index(district)
    demographic_pressure = calculate_demographic_pressure_index(district)
    climate_risk = calculate_climate_future_risk_index(building, district)

    category_scores = {}

    for category_name, category_key in CATEGORY_KEYS.items():
        deficit_score = urban_deficit["details"].get(category_key, 0)
        profile_pressure_values = []

        for profile in district["main_profiles"]:
            profile_needs = PROFILE_NEEDS.get(profile)
            if profile_needs and category_key in profile_needs["priority_categories"]:
                profile_pressure_values.append(demographic_pressure["details"].get(profile, 0))

        demographic_score = 0.0
        if profile_pressure_values:
            demographic_score = round(
                sum(profile_pressure_values) / len(profile_pressure_values),
                2,
            )

        building_fit = category_building_fit(category_name, building)
        climate_bonus = climate_risk["score"] * CLIMATE_CATEGORY_BONUS[category_name] / 5
        final_score = round(
            (deficit_score * 0.30)
            + (demographic_score * 0.30)
            + (building_fit * 0.30)
            + (climate_bonus * 0.10),
            2,
        )

        category_scores[category_name] = {
            "urban_deficit_score": deficit_score,
            "demographic_score": demographic_score,
            "building_fit_score": building_fit,
            "climate_bonus": round(climate_bonus, 2),
            "final_score": final_score,
        }

    return category_scores


def rank_categories(category_scores: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    ranked = sorted(
        category_scores.items(),
        key=lambda item: item[1]["final_score"],
        reverse=True,
    )
    return [{"category": category, "scores": scores} for category, scores in ranked]


def select_top_program(
    grouped_program: dict[str, list[str]],
    ranked_categories: list[dict[str, Any]],
    scale: str,
) -> dict[str, list[str]]:
    scale_limits = {
        "small": 3,
        "medium": 4,
        "large": 5,
        "metropolitan": 6,
    }
    max_categories = scale_limits[scale]
    selected = {}

    for item in ranked_categories[:max_categories]:
        category = item["category"]
        if category in grouped_program:
            selected[category] = grouped_program[category]

    return selected


def generate_narrative(
    district: DistrictData,
    building: BuildingData,
    ranked_categories: list[dict[str, Any]],
    scale: str,
) -> str:
    top_categories = [item["category"] for item in ranked_categories[:3]]
    profiles = ", ".join(district["main_profiles"])
    return (
        f"In {district['name']}, the strongest urban pressure comes from the profiles of {profiles}. "
        f"The host building {building['name']} has a {scale} programmatic capacity, with {building['total_area']} m², "
        f"{building['floors']} floors, and an average height of {building['average_height']} m. "
        f"The most suitable categories for intervention are {top_categories[0]}, {top_categories[1]}, and {top_categories[2]}. "
        f"This suggests a reuse strategy that combines neighborhood deficit, demographic demand, architectural adaptability, "
        f"and long-term climate resilience for Madrid 2050 and beyond."
    )


def suggest_climate_package(building: BuildingData) -> list[str]:
    package = list(CLIMATE_STRATEGIES["heat"])

    if building["roof_usable"] == 1:
        package.append("Roof solar canopy and accessible climate refuge terrace")

    if building["outdoor_space"] == 1:
        package.append("Shaded exterior public space with biodiversity planting")
        package.append("Permeable and cooled public ground surfaces")

    package.extend(CLIMATE_STRATEGIES["energy"])
    package.extend(CLIMATE_STRATEGIES["water"])
    package.extend(CLIMATE_STRATEGIES["future_adaptation"])

    unique_package = []
    for item in package:
        if item not in unique_package:
            unique_package.append(item)

    return unique_package


def run_full_analysis(district: DistrictData, building: BuildingData) -> dict[str, Any]:
    architectural_capacity = calculate_architectural_capacity_index(building)
    urban_deficit = calculate_urban_deficit_index(district)
    demographic_pressure = calculate_demographic_pressure_index(district)
    climate_risk = calculate_climate_future_risk_index(building, district)
    grouped_program = build_grouped_program_from_profiles(district)
    category_scores = calculate_category_scores(district, building)
    ranked_categories = rank_categories(category_scores)
    scale = determine_program_scale(building)
    selected_program = select_top_program(grouped_program, ranked_categories, scale)
    people_programs = build_people_program_guides(district, selected_program)
    narrative = generate_narrative(district, building, ranked_categories, scale)
    climate_package = suggest_climate_package(building)

    return {
        "district": district["name"],
        "building": building["name"],
        "indices": {
            "architectural_capacity_index": architectural_capacity,
            "urban_deficit_index": urban_deficit,
            "demographic_pressure_index": demographic_pressure,
            "climate_future_risk_index": climate_risk,
        },
        "program_scale": scale,
        "category_ranking": ranked_categories,
        "recommended_program": selected_program,
        "people_programs": people_programs,
        "climate_adaptation_package": climate_package,
        "architectural_narrative": narrative,
    }


def run_district_only_analysis(district: DistrictData) -> dict[str, Any]:
    return {
        "district": district["name"],
        "urban_deficit_index": calculate_urban_deficit_index(district),
        "demographic_pressure_index": calculate_demographic_pressure_index(district),
        "profile_programs": build_profile_programs(district),
    }
