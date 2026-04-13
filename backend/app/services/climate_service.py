"""Climate and future-risk helpers.

This file keeps the current climate logic in one place so that future official
sources can be plugged in cleanly.
"""

from typing import Any

from ..data.catalog import CLIMATE_STRATEGIES
from ..models.schemas import BuildingData, DistrictData


def calculate_climate_future_risk_index(
    building: BuildingData,
    district: DistrictData,
) -> dict[str, Any]:
    heat_risk = 5 if district["density"] > 25000 else 4 if district["density"] > 18000 else 3
    exposure = 5 if building["outdoor_space"] == 1 else 3
    roof_opportunity = 5 if building["roof_usable"] == 1 else 2
    adaptability = building["condition"]

    details = {
        "heat_risk": heat_risk,
        "outdoor_exposure": exposure,
        "roof_climate_opportunity": roof_opportunity,
        "adaptability_for_future": adaptability,
    }
    final_score = round(sum(details.values()) / len(details), 2)
    return {
        "score": final_score,
        "details": details,
        "strategic_lines": CLIMATE_STRATEGIES,
    }
