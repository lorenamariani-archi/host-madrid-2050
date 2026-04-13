"""Compatibility wrapper around the new Madrid API service."""

from .madrid_api import (
    MadridOpenDataError,
    clear_madrid_cache as clear_madrid_demographics_cache,
    get_madrid_district_demographics,
    normalize_district_name,
)
