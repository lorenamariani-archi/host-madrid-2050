"""Official public Catastro service helpers."""

from __future__ import annotations

import json
from typing import Any
from xml.etree import ElementTree as ET
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models.schemas import OfficialAddressInput


CAT_NAMESPACE = {"cat": "http://www.catastro.meh.es/"}
CAT_ADDRESS_LOOKUP_URL = (
    "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPLOC"
)
CAT_COORDINATE_LOOKUP_URL = (
    "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCoordenadas.svc/json/Consulta_CPMRC"
)
IGN_PNOA_WMS_URL = "https://www.ign.es/wms-inspire/pnoa-ma"
REQUEST_TIMEOUT_SECONDS = 30


class CatastroApiError(RuntimeError):
    """Raised when the public Catastro service cannot be used successfully."""


def _fetch_xml(url: str, params: dict[str, str]) -> ET.Element:
    try:
        request_url = f"{url}?{urlencode(params)}"
        request = Request(request_url, headers={"User-Agent": "HOST-FastAPI-Backend/0.1.0"})
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return ET.fromstring(response.read())
    except (URLError, ET.ParseError) as exc:
        raise CatastroApiError(f"Unable to fetch Catastro data from {url}") from exc


def _fetch_json(url: str, params: dict[str, str]) -> Any:
    try:
        request_url = f"{url}?{urlencode(params)}"
        request = Request(request_url, headers={"Accept": "application/json", "User-Agent": "HOST-FastAPI-Backend/0.1.0"})
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except (URLError, ValueError) as exc:
        raise CatastroApiError(f"Unable to fetch Catastro data from {url}") from exc


def _text(node: ET.Element | None, path: str) -> str:
    if node is None:
        return ""
    found = node.find(path, CAT_NAMESPACE)
    return found.text.strip() if found is not None and found.text else ""


def _build_rc_from_node(node: ET.Element) -> str:
    return _text(node, "cat:pc1") + _text(node, "cat:pc2") + _text(node, "cat:car") + _text(node, "cat:cc1") + _text(node, "cat:cc2")


def _build_parcel_rc_from_node(node: ET.Element) -> str:
    return _text(node, "cat:pc1") + _text(node, "cat:pc2")


def _floor_rank(label: str) -> int | None:
    label = label.strip().upper()
    if not label or label.startswith("-") or label.startswith("S"):
        return None
    if label in {"00", "0", "BJ", "PB", "PR"}:
        return 1
    if label.isdigit():
        return int(label) + 1
    return None


def lookup_catastro_by_address(address: OfficialAddressInput) -> dict[str, Any]:
    root = _fetch_xml(
        CAT_ADDRESS_LOOKUP_URL,
        {
            "Provincia": address.province,
            "Municipio": address.municipality,
            "Sigla": address.street_type,
            "Calle": address.street_name,
            "Numero": address.street_number,
            "Bloque": address.block,
            "Escalera": address.stair,
            "Planta": address.floor,
            "Puerta": address.door,
        },
    )

    detailed = root.find("cat:bico", CAT_NAMESPACE)
    if detailed is not None:
        return _parse_detailed_property(root, address)

    candidate_nodes = root.findall("cat:lrcdnp/cat:rcdnp", CAT_NAMESPACE)
    candidates = []
    for node in candidate_nodes:
        rc_node = node.find("cat:rc", CAT_NAMESPACE)
        candidates.append(
            {
                "cadastral_reference": _build_rc_from_node(rc_node) if rc_node is not None else "",
                "parcel_cadastral_reference": _build_parcel_rc_from_node(rc_node) if rc_node is not None else "",
                "street_name": _text(node, "cat:dt/cat:locs/cat:lous/cat:lourb/cat:dir/cat:nv"),
                "street_number": _text(node, "cat:dt/cat:locs/cat:lous/cat:lourb/cat:dir/cat:pnp"),
                "postal_code": _text(node, "cat:dt/cat:locs/cat:lous/cat:lourb/cat:dp"),
                "floor": _text(node, "cat:dt/cat:locs/cat:lous/cat:lourb/cat:loint/cat:pt"),
                "door": _text(node, "cat:dt/cat:locs/cat:lous/cat:lourb/cat:loint/cat:pu"),
            }
        )

    return {
        "status": "multiple_candidates",
        "requested_address": address.model_dump(),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "notes": [
            "The public Catastro service returned multiple candidate properties for this address.",
            "Add floor and door information to obtain a more precise non-protected property record.",
        ],
        "source": {"provider": "Catastro", "endpoint": CAT_ADDRESS_LOOKUP_URL},
    }


def _parse_detailed_property(root: ET.Element, address: OfficialAddressInput) -> dict[str, Any]:
    property_node = root.find("cat:bico/cat:bi", CAT_NAMESPACE)
    if property_node is None:
        raise CatastroApiError("Catastro did not return a detailed property block")

    rc_node = property_node.find("cat:idbi/cat:rc", CAT_NAMESPACE)
    units = []
    observed_floor_ranks: set[int] = set()
    for cons in root.findall("cat:bico/cat:lcons/cat:cons", CAT_NAMESPACE):
        floor_label = _text(cons, "cat:dt/cat:lourb/cat:loint/cat:pt").upper()
        floor_rank = _floor_rank(floor_label)
        if floor_rank is not None:
            observed_floor_ranks.add(floor_rank)
        units.append(
            {
                "use": _text(cons, "cat:lcd"),
                "floor": floor_label,
                "door": _text(cons, "cat:dt/cat:lourb/cat:loint/cat:pu"),
                "surface_m2": int(float(_text(cons, "cat:dfcons/cat:stl") or 0)),
            }
        )

    return {
        "status": "ok",
        "requested_address": address.model_dump(),
        "cadastral_reference": _build_rc_from_node(rc_node) if rc_node is not None else "",
        "parcel_cadastral_reference": _build_parcel_rc_from_node(rc_node) if rc_node is not None else "",
        "property_type": _text(property_node, "cat:idbi/cat:cn"),
        "full_address": _text(property_node, "cat:ldt"),
        "main_use": _text(property_node, "cat:debi/cat:luso"),
        "built_area_m2": int(float(_text(property_node, "cat:debi/cat:sfc") or 0)),
        "participation_coefficient": _text(property_node, "cat:debi/cat:cpt"),
        "construction_year": int(float(_text(property_node, "cat:debi/cat:ant") or 0)),
        "postal_code": _text(property_node, "cat:dt/cat:locs/cat:lous/cat:lourb/cat:dp"),
        "municipality": _text(property_node, "cat:dt/cat:nm"),
        "province": _text(property_node, "cat:dt/cat:np"),
        "street_name": _text(property_node, "cat:dt/cat:locs/cat:lous/cat:lourb/cat:dir/cat:nv"),
        "street_number": _text(property_node, "cat:dt/cat:locs/cat:lous/cat:lourb/cat:dir/cat:pnp"),
        "floor_count_observed": max(observed_floor_ranks) if observed_floor_ranks else 1,
        "units": units,
        "source": {"provider": "Catastro", "endpoint": CAT_ADDRESS_LOOKUP_URL},
    }


def _orthophoto_bbox(longitude: float, latitude: float, span: float = 0.00045) -> str:
    min_lon = longitude - span
    min_lat = latitude - span
    max_lon = longitude + span
    max_lat = latitude + span
    return f"{min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}"


def get_catastro_coordinates(
    *,
    cadastral_reference: str,
    province: str,
    municipality: str,
    srs: str = "EPSG:4326",
) -> dict[str, Any] | None:
    """Resolve public Catastro coordinates for a parcel reference.

    The public coordinate service uses the 14-character parcel reference instead of
    the longer unit reference. Returning ``None`` keeps the map preview optional.
    """

    parcel_reference = (cadastral_reference or "").strip()[:14]
    if len(parcel_reference) != 14:
        return None

    payload = _fetch_json(
        CAT_COORDINATE_LOOKUP_URL,
        {
            "Provincia": province,
            "Municipio": municipality,
            "SRS": srs,
            "RefCat": parcel_reference,
        },
    )
    result = payload.get("Consulta_CPMRCResult", {})
    coordinates = result.get("coordenadas", {}).get("coord", [])
    if not coordinates:
        return None

    first = coordinates[0]
    geo = first.get("geo", {})

    try:
        longitude = float(geo.get("xcen"))
        latitude = float(geo.get("ycen"))
    except (TypeError, ValueError):
        return None

    bbox = _orthophoto_bbox(longitude, latitude)
    orthophoto_image_url = (
        f"{IGN_PNOA_WMS_URL}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS=OI.OrthoimageCoverage&STYLES=&CRS=CRS:84&BBOX={bbox}"
        "&WIDTH=720&HEIGHT=420&FORMAT=image/jpeg"
    )

    return {
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
            "srs": geo.get("srs", srs),
        },
        "label": first.get("ldt", ""),
        "parcel_cadastral_reference": parcel_reference,
        "official_preview": {
            "type": "aerial_orthophoto",
            "provider": "IGN PNOA",
            "image_url": orthophoto_image_url,
            "bbox_crs84": bbox,
            "notes": [
                "Official aerial preview generated from IGN PNOA orthophoto services.",
                "The point location comes from the public Catastro coordinate service.",
            ],
        },
        "source": {
            "catastro_coordinates_endpoint": CAT_COORDINATE_LOOKUP_URL,
            "ign_orthophoto_service": IGN_PNOA_WMS_URL,
        },
    }
