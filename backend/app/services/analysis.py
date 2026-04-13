"""Compatibility wrapper.

The scoring logic now lives in :mod:`app.services.scoring_engine` so that data
access and scoring are cleanly separated.
"""

from .scoring_engine import (
    build_grouped_program_from_profiles,
    build_profile_programs,
    calculate_architectural_capacity_index,
    calculate_category_scores,
    calculate_demographic_pressure_index,
    calculate_urban_deficit_index,
    category_building_fit,
    clamp_0_5,
    determine_program_scale,
    generate_narrative,
    interpolate_score,
    likert_score,
    rank_categories,
    run_district_only_analysis,
    run_full_analysis,
    score_average_floor_plate,
    score_floor_configuration,
    score_site_support_capacity,
    score_spatial_height,
    score_total_area,
    select_top_program,
    suggest_climate_package,
)
