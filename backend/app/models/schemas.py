"""Shared schemas for request validation and normalized project data.

This module centralizes the models used by both the legacy demo routes and the
new real-data routes. Keeping them together makes the project easier to explain
in a TFG and avoids circular imports between services.
"""

import re
import unicodedata
from typing import Dict, List, Optional, TypedDict, cast

from pydantic import BaseModel, Field, field_validator


def _normalize_public_text(value: str) -> str:
    compact = " ".join(str(value or "").strip().split())
    if not compact:
        return ""
    normalized = unicodedata.normalize("NFKD", compact)
    without_accents = "".join(character for character in normalized if not unicodedata.combining(character))
    return without_accents.upper()


def _normalize_street_type(value: str) -> str:
    normalized = _normalize_public_text(value)
    aliases = {
        "CALLE": "CL",
        "C/": "CL",
        "CL.": "CL",
        "AVENIDA": "AV",
        "AV.": "AV",
        "AVDA": "AV",
        "AVDA.": "AV",
        "PASEO": "PS",
        "PLAZA": "PZ",
        "CARRETERA": "CR",
    }
    return aliases.get(normalized, normalized)


def _normalize_street_name(value: str) -> str:
    normalized = _normalize_public_text(value)
    return re.sub(r"^(CALLE|CL|C/|AVENIDA|AVDA|AV\.|AV|PASEO|PS|PLAZA|PZ|CARRETERA|CR)\s+", "", normalized)


class DistrictData(TypedDict):
    name: str
    population: int
    density: float
    children_share: float
    young_adults_share: float
    adults_share: float
    seniors_share: float
    main_profiles: List[str]
    existing_facilities: Dict[str, int]


class BuildingData(TypedDict):
    name: str
    total_area: float
    plot_area: float
    floors: int
    average_height: float
    structure_flexibility: int
    outdoor_space: int
    roof_usable: int
    heritage_constraint: int
    condition: int


class DistrictInput(BaseModel):
    name: str
    population: int
    density: float
    children_share: float
    young_adults_share: float
    adults_share: float
    seniors_share: float
    main_profiles: List[str]
    existing_facilities: Dict[str, int]
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Centro",
                "population": 135000,
                "density": 24500.0,
                "children_share": 0.08,
                "young_adults_share": 0.23,
                "adults_share": 0.54,
                "seniors_share": 0.15,
                "main_profiles": ["international student", "teenager", "retired couple"],
                "existing_facilities": {
                    "green": 2,
                    "sport": 1,
                    "cultural": 3,
                    "learning": 2,
                    "community": 2,
                    "care": 2,
                },
            }
        }
    }

    def to_data(self) -> DistrictData:
        return cast(DistrictData, self.model_dump())


class BuildingInput(BaseModel):
    name: str
    total_area: float
    plot_area: float
    floors: int
    average_height: float
    structure_flexibility: int
    outdoor_space: int
    roof_usable: int
    heritage_constraint: int
    condition: int
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Factory A",
                "total_area": 12000.0,
                "plot_area": 5000.0,
                "floors": 4,
                "average_height": 4.2,
                "structure_flexibility": 4,
                "outdoor_space": 1,
                "roof_usable": 1,
                "heritage_constraint": 3,
                "condition": 3,
            }
        }
    }

    def to_data(self) -> BuildingData:
        return cast(BuildingData, self.model_dump())


class AnalysisInput(BaseModel):
    district: DistrictInput
    building: BuildingInput
    model_config = {
        "json_schema_extra": {
            "example": {
                "district": DistrictInput.model_config["json_schema_extra"]["example"],
                "building": BuildingInput.model_config["json_schema_extra"]["example"],
            }
        }
    }


class MadridSourceMetadata(BaseModel):
    dataset_id: str
    dataset_title: str
    resource_url: str
    data_period_start: str
    data_period_end: str


class MadridAgeGroups(BaseModel):
    children: int
    young_adults: int
    adults: int
    seniors: int


class MadridAgeShares(BaseModel):
    children_share: float
    young_adults_share: float
    adults_share: float
    seniors_share: float


class MadridNationalityBreakdown(BaseModel):
    spanish: int
    foreign: int


class MadridGenderBreakdown(BaseModel):
    male: int
    female: int


class MadridDistrictDemographicsResponse(BaseModel):
    district: str
    population_total: int
    age_groups: MadridAgeGroups
    age_shares: MadridAgeShares
    nationality_breakdown: MadridNationalityBreakdown
    gender_breakdown: MadridGenderBreakdown
    source: MadridSourceMetadata


class OfficialAddressInput(BaseModel):
    """Structured address input for the public Catastro services."""

    province: str = "MADRID"
    municipality: str = "MADRID"
    street_type: str = Field(default="CL", description="Catastro street type code, e.g. CL")
    street_name: str
    street_number: str
    block: str = ""
    stair: str = ""
    floor: str = ""
    door: str = ""
    model_config = {
        "json_schema_extra": {
            "example": {
                "province": "MADRID",
                "municipality": "MADRID",
                "street_type": "CL",
                "street_name": "ALCALA",
                "street_number": "45",
                "block": "",
                "stair": "",
                "floor": "",
                "door": "",
            }
        }
    }

    @field_validator("province", "municipality", "block", "stair", "floor", "door", mode="before")
    @classmethod
    def normalize_public_fields(cls, value: str) -> str:
        return _normalize_public_text(str(value or ""))

    @field_validator("street_type", mode="before")
    @classmethod
    def normalize_street_type_field(cls, value: str) -> str:
        return _normalize_street_type(str(value or "CL")) or "CL"

    @field_validator("street_name", mode="before")
    @classmethod
    def normalize_street_name_field(cls, value: str) -> str:
        normalized = _normalize_street_name(str(value or ""))
        if not normalized:
            raise ValueError("street_name cannot be empty")
        return normalized

    @field_validator("street_number", mode="before")
    @classmethod
    def normalize_street_number_field(cls, value: str) -> str:
        normalized = _normalize_public_text(str(value or ""))
        if not normalized:
            raise ValueError("street_number cannot be empty")
        return normalized


class BuildingOverridesInput(BaseModel):
    """Optional manual corrections for values Catastro does not expose directly."""

    structure_flexibility: Optional[int] = None
    outdoor_space: Optional[int] = None
    roof_usable: Optional[int] = None
    heritage_constraint: Optional[int] = None
    condition: Optional[int] = None
    average_height: Optional[float] = None
    plot_area: Optional[float] = None
    floors: Optional[int] = None
    model_config = {
        "json_schema_extra": {
            "example": {
                "roof_usable": 1,
                "outdoor_space": 0,
                "condition": 3,
            }
        }
    }


class RealAnalyzeRequest(BaseModel):
    district_name: str
    building_address: Optional[OfficialAddressInput] = None
    building_overrides: Optional[BuildingOverridesInput] = None
    refresh: bool = False
    model_config = {
        "json_schema_extra": {
            "example": {
                "district_name": "Centro",
                "building_address": OfficialAddressInput.model_config["json_schema_extra"]["example"],
                "building_overrides": BuildingOverridesInput.model_config["json_schema_extra"]["example"],
                "refresh": False,
            }
        }
    }
