from fastapi import APIRouter, Body, HTTPException, Query

from ..data.catalog import BUILDING_DATA, DISTRICT_DATA, MADRID_DISTRICT_NAMES
from ..models.schemas import (
    AnalysisInput,
    BuildingData,
    BuildingOverridesInput,
    DistrictData,
    MadridDistrictDemographicsResponse,
    OfficialAddressInput,
    RealAnalyzeRequest,
)
from ..services.analysis import (
    build_profile_programs,
    calculate_architectural_capacity_index,
    calculate_demographic_pressure_index,
    calculate_urban_deficit_index,
    run_full_analysis,
)
from ..services.madrid_open_data import (
    MadridOpenDataError,
    get_madrid_district_demographics,
)
from ..services.real_data_service import (
    RealDataServiceError,
    get_real_building_payload,
    get_real_district_payload,
    get_real_proposal_payload,
)

router = APIRouter()


def get_district_or_404(district_name: str) -> DistrictData:
    district = DISTRICT_DATA.get(district_name)
    if district is None:
        raise HTTPException(status_code=404, detail="District not found")
    return district


def get_building_or_404(building_name: str) -> BuildingData:
    building = BUILDING_DATA.get(building_name)
    if building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@router.get(
    "/",
    tags=["System"],
    summary="Health check",
    description="Simple endpoint to confirm that the HOST backend is running.",
    response_description="Basic service status message.",
)
def home():
    return {"message": "HOST is running"}


def _build_address_input(
    *,
    province: str = "MADRID",
    municipality: str = "MADRID",
    street_type: str = "CL",
    street_name: str,
    street_number: str,
    block: str = "",
    stair: str = "",
    floor: str = "",
    door: str = "",
) -> OfficialAddressInput:
    return OfficialAddressInput(
        province=province,
        municipality=municipality,
        street_type=street_type,
        street_name=street_name,
        street_number=street_number,
        block=block,
        stair=stair,
        floor=floor,
        door=door,
    )


@router.get(
    "/district/{district_name}",
    tags=["Demo Data"],
    summary="Analyze a demo district",
    description="Returns the district-level indices and profile programs using local sample data stored in the project.",
    response_description="District profile based on demo data.",
)
def district_profile(district_name: str):
    district = get_district_or_404(district_name)

    return {
        "district": district_name,
        "raw_data": district,
        "urban_deficit_index": calculate_urban_deficit_index(district),
        "demographic_pressure_index": calculate_demographic_pressure_index(district),
        "profile_programs": build_profile_programs(district),
    }


@router.get(
    "/building/{building_name}",
    tags=["Demo Data"],
    summary="Analyze a demo building",
    description="Calculates the Architectural Capacity Index using local sample building data.",
    response_description="Building profile based on demo data.",
)
def building_profile(building_name: str):
    building = get_building_or_404(building_name)

    return {
        "building": building_name,
        "raw_data": building,
        "architectural_capacity_index": calculate_architectural_capacity_index(building),
    }


@router.get(
    "/proposal/{district_name}/{building_name}",
    tags=["Demo Data"],
    summary="Generate a demo proposal",
    description="Combines a sample district and a sample building to generate a full HOST adaptive reuse proposal.",
    response_description="Full proposal based on demo data.",
)
def project_proposal(district_name: str, building_name: str):
    district = get_district_or_404(district_name)
    building = get_building_or_404(building_name)
    return run_full_analysis(district, building)


@router.post(
    "/analyze",
    tags=["Demo Data"],
    summary="Analyze a custom demo payload",
    description="Runs the HOST scoring engine on a custom district and building payload without calling any external source.",
    response_description="Full proposal based on the submitted custom payload.",
)
def analyze_custom_case(
    payload: AnalysisInput = Body(
        ...,
        description="Custom district and building values for a fully manual HOST analysis.",
    )
):
    return run_full_analysis(payload.district.to_data(), payload.building.to_data())


@router.get(
    "/madrid/demographics/{district_name}",
    response_model=MadridDistrictDemographicsResponse,
    tags=["Official Madrid Data"],
    summary="Get official Madrid district demographics",
    description="Fetches district demographic aggregates from the official Madrid Open Data padrón dataset.",
    response_description="District demographics aggregated from the official Madrid padrón dataset.",
)
def madrid_district_demographics(
    district_name: str,
    refresh: bool = Query(
        default=False,
        description="When true, clears the in-memory cache and refetches the latest official dataset.",
    ),
):
    try:
        demographics = get_madrid_district_demographics(district_name, refresh=refresh)
    except MadridOpenDataError as exc:
        raise HTTPException(
            status_code=502,
            detail="Madrid open data service is currently unavailable",
        ) from exc

    if demographics is None:
        raise HTTPException(
            status_code=404,
            detail="District not found in Madrid open data",
        )

    return demographics


@router.get(
    "/real/district/{district_name}",
    tags=["Official Madrid Data"],
    summary="Build a real district profile",
    description=(
        "Builds a HOST-ready district profile from official Madrid Open Data and INE public statistics. "
        "This route is useful when you want to explain how raw public data is normalized before scoring."
    ),
    response_description="Normalized district payload and district-level score preview.",
)
def real_district_profile(
    district_name: str,
    refresh: bool = Query(
        default=False,
        description="When true, clears the in-memory cache and refetches the latest official data.",
    ),
):
    try:
        payload = get_real_district_payload(district_name, refresh=refresh)
    except RealDataServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not payload:
        raise HTTPException(status_code=404, detail="District not found in official Madrid data")

    return payload


@router.get(
    "/real/districts",
    tags=["Official Madrid Data"],
    summary="List Madrid districts",
    description="Returns the 21 Madrid districts available in the official-data interface.",
    response_description="List of Madrid district names.",
)
def real_district_names():
    return {
        "districts": MADRID_DISTRICT_NAMES,
        "count": len(MADRID_DISTRICT_NAMES),
        "notes": [
            "These names are intended for the official-data routes.",
            "The demo mode keeps a smaller handcrafted sample dataset.",
        ],
    }


@router.get(
    "/real/building/by-address",
    tags=["Official Madrid Data"],
    summary="Lookup a real building by address",
    description=(
        "Queries the public Catastro service with a structured Madrid address and normalizes the result "
        "into HOST building variables for the Architectural Capacity Index."
    ),
    response_description="Catastro lookup result plus normalized building data when a single property match is found.",
)
def real_building_by_address(
    street_name: str = Query(..., description="Street name as expected by Catastro, for example ALCALA."),
    street_number: str = Query(..., description="Street number as expected by Catastro."),
    province: str = Query(default="MADRID", description="Province name for the Catastro lookup."),
    municipality: str = Query(default="MADRID", description="Municipality name for the Catastro lookup."),
    street_type: str = Query(default="CL", description="Catastro street type code, for example CL for calle."),
    block: str = Query(default="", description="Optional Catastro block value for more precise lookups."),
    stair: str = Query(default="", description="Optional Catastro stair value for more precise lookups."),
    floor: str = Query(default="", description="Optional floor value to disambiguate multi-unit buildings."),
    door: str = Query(default="", description="Optional door value to disambiguate multi-unit buildings."),
):
    address = _build_address_input(
        province=province,
        municipality=municipality,
        street_type=street_type,
        street_name=street_name,
        street_number=street_number,
        block=block,
        stair=stair,
        floor=floor,
        door=door,
    )

    try:
        return get_real_building_payload(address)
    except RealDataServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/real/proposal/{district_name}",
    tags=["Official Madrid Data"],
    summary="Generate a real-data HOST proposal",
    description=(
        "Combines official district data with an optional Catastro address lookup. "
        "If no address is provided, the result stays at district level and is marked as partial."
    ),
    response_description="Real-data proposal or partial district-level result.",
)
def real_proposal(
    district_name: str,
    refresh: bool = Query(
        default=False,
        description="When true, clears the in-memory cache and refetches the latest official district data.",
    ),
    province: str = Query(default="MADRID", description="Province name for the optional Catastro lookup."),
    municipality: str = Query(default="MADRID", description="Municipality name for the optional Catastro lookup."),
    street_type: str = Query(default="CL", description="Catastro street type code, for example CL."),
    street_name: str | None = Query(
        default=None,
        description="Optional street name for the Catastro building lookup.",
    ),
    street_number: str | None = Query(
        default=None,
        description="Optional street number for the Catastro building lookup.",
    ),
    block: str = Query(default="", description="Optional Catastro block value."),
    stair: str = Query(default="", description="Optional Catastro stair value."),
    floor: str = Query(default="", description="Optional floor value."),
    door: str = Query(default="", description="Optional door value."),
):
    address = None
    if street_name and street_number:
        address = _build_address_input(
            province=province,
            municipality=municipality,
            street_type=street_type,
            street_name=street_name,
            street_number=street_number,
            block=block,
            stair=stair,
            floor=floor,
            door=door,
        )

    try:
        payload = get_real_proposal_payload(
            district_name,
            address=address,
            refresh=refresh,
        )
    except RealDataServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not payload:
        raise HTTPException(status_code=404, detail="District not found in official Madrid data")

    return payload


@router.post(
    "/real/analyze",
    tags=["Official Madrid Data"],
    summary="Analyze a real district with an optional real building",
    description=(
        "Main end-to-end real-data route for HOST. It takes a district name, an optional Catastro address, "
        "and optional manual building overrides for variables that official sources do not expose directly."
    ),
    response_description="Complete or partial real-data HOST proposal.",
)
def real_analyze(
    payload: RealAnalyzeRequest = Body(
        ...,
        description="Real-data analysis request with an official district name and optional Catastro address.",
    )
):
    try:
        result = get_real_proposal_payload(
            payload.district_name,
            address=payload.building_address,
            overrides=payload.building_overrides,
            refresh=payload.refresh,
        )
    except RealDataServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not result:
        raise HTTPException(status_code=404, detail="District not found in official Madrid data")

    return result


@router.get(
    "/real/examples",
    tags=["Official Madrid Data"],
    summary="Show demo-ready real-data examples",
    description=(
        "Returns example requests you can reuse in Swagger, Postman, or a TFG presentation. "
        "These examples do not call external services; they only document how to use the real-data API."
    ),
    response_description="Curated example requests for the official-data endpoints.",
)
def real_examples():
    return {
        "district_example": {
            "method": "GET",
            "path": "/real/district/Centro",
            "query": {"refresh": False},
            "what_it_shows": "Official Madrid district profile normalized into HOST variables.",
        },
        "building_example": {
            "method": "GET",
            "path": "/real/building/by-address",
            "query": {
                "street_type": "CL",
                "street_name": "ALCALA",
                "street_number": "45",
                "municipality": "MADRID",
                "province": "MADRID",
            },
            "what_it_shows": "Public Catastro lookup and normalized building capacity inputs.",
        },
        "proposal_example": {
            "method": "GET",
            "path": "/real/proposal/Centro",
            "query": {
                "street_type": "CL",
                "street_name": "ALCALA",
                "street_number": "45",
            },
            "what_it_shows": "Combined district and building proposal using official public data.",
        },
        "analyze_example": {
            "method": "POST",
            "path": "/real/analyze",
            "json_body": RealAnalyzeRequest.model_config["json_schema_extra"]["example"],
            "what_it_shows": "End-to-end real-data analysis with optional manual building overrides.",
        },
        "presentation_tip": "Open this endpoint first in `/docs` so the demo flow is easy to follow.",
    }
