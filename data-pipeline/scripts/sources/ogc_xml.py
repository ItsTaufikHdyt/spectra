"""
ogc_xml.py — Parser XML OGC (WFS 2.0 Capabilities/DescribeFeatureType/hits, CSW 2.0.2, ISO 19139).

Hanya stdlib (xml.etree). Respons berasal dari server luar: diperlakukan sebagai data, dan
field yang hilang menjadi None, bukan error.
Data kontak (nama orang, email, telepon) di ISO 19139 sengaja TIDAK diambil.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

NS = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "ows": "http://www.opengis.net/ows/1.1",
    "xs": "http://www.w3.org/2001/XMLSchema",
    "csw": "http://www.opengis.net/cat/csw/2.0.2",
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "srv": "http://www.isotc211.org/2005/srv",
}
LAYER_PROTOCOLS = ("OGC:WMS", "OGC:WFS")


def _text(el, path: str):
    found = el.find(path, NS) if el is not None else None
    return found.text.strip() if found is not None and found.text else None


def _code(el, path: str):
    found = el.find(path, NS)
    return found.get("codeListValue") if found is not None else None


def parse_wfs_capabilities(body: bytes) -> dict:
    root = ET.fromstring(body)
    ops = [o.get("name") for o in root.iterfind(".//ows:OperationsMetadata/ows:Operation", NS)]
    constraints = {}
    for c in root.iterfind(".//ows:OperationsMetadata//ows:Constraint", NS):  # termasuk constraint per operasi
        constraints.setdefault(c.get("name"), _text(c, "ows:DefaultValue"))
    fts = []
    for ft in root.iterfind(".//wfs:FeatureTypeList/wfs:FeatureType", NS):
        lower = (_text(ft, "ows:WGS84BoundingBox/ows:LowerCorner") or "").split()
        upper = (_text(ft, "ows:WGS84BoundingBox/ows:UpperCorner") or "").split()
        fts.append(
            {
                "name": _text(ft, "wfs:Name"),
                "title": _text(ft, "wfs:Title"),
                "default_crs": _text(ft, "wfs:DefaultCRS"),
                "other_crs": [e.text for e in ft.iterfind("wfs:OtherCRS", NS)],
                "wgs84_bbox": [float(v) for v in lower + upper] if len(lower + upper) == 4 else None,
                "keywords": [e.text for e in ft.iterfind("ows:Keywords/ows:Keyword", NS)],
            }
        )
    return {
        "versions": [e.text for e in root.iterfind(".//ows:ServiceIdentification/ows:ServiceTypeVersion", NS)] or [root.get("version")],
        "operations": ops,
        "constraints": constraints,
        "feature_types": fts,
    }


def parse_describe_feature_type(body: bytes) -> list[dict]:
    """Atribut (nama, tipe XSD) dari complexType pertama."""
    root = ET.fromstring(body)
    return [
        {"name": e.get("name"), "type": e.get("type"), "nillable": e.get("nillable") == "true"}
        for e in root.iterfind(".//xs:complexType//xs:sequence/xs:element", NS)
    ]


def parse_wfs_hits(body: bytes) -> int | None:
    v = ET.fromstring(body).get("numberMatched")
    return int(v) if v and v.isdigit() else None


def parse_csw_search(body: bytes) -> dict:
    """GetRecords: jumlah total, jumlah di halaman ini, nextRecord, dan elemen record mentah."""
    root = ET.fromstring(body)
    sr = root.find("csw:SearchResults", NS)
    if sr is None:
        raise ValueError("Respons GetRecords tanpa csw:SearchResults")
    return {
        "matched": int(sr.get("numberOfRecordsMatched", 0)),
        "returned": int(sr.get("numberOfRecordsReturned", 0)),
        "next": int(sr.get("nextRecord", 0)),
        "records": list(sr.iterfind("gmd:MD_Metadata", NS)),
    }


def parse_iso_record(md) -> dict:
    """gmd:MD_Metadata -> ringkasan: id, judul, abstrak, tipe, bbox WGS84, link layer."""
    ident = md.find(".//gmd:identificationInfo/*", NS)
    bbox_el = md.find(".//gmd:EX_GeographicBoundingBox", NS)
    bbox = None
    if bbox_el is not None:
        vals = [_text(bbox_el, f"gmd:{k}/gco:Decimal") for k in ("westBoundLongitude", "southBoundLatitude", "eastBoundLongitude", "northBoundLatitude")]
        bbox = [float(v) for v in vals] if all(vals) else None
    links = []
    for o in md.iterfind(".//gmd:distributionInfo//gmd:CI_OnlineResource", NS):
        links.append(
            {
                "protocol": _text(o, "gmd:protocol/gco:CharacterString"),
                "name": _text(o, "gmd:name/gco:CharacterString"),
                "url": _text(o, "gmd:linkage/gmd:URL"),
            }
        )
    layer_links = [x for x in links if x["protocol"] in LAYER_PROTOCOLS]
    return {
        "id": _text(md, "gmd:fileIdentifier/gco:CharacterString"),
        "judul": _text(ident, ".//gmd:citation//gmd:title/gco:CharacterString"),
        "abstrak": _text(ident, "gmd:abstract/gco:CharacterString"),
        "tipe": _code(md, "gmd:hierarchyLevel/gmd:MD_ScopeCode"),
        "representasi": _code(md, ".//gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode"),
        "status": _code(md, ".//gmd:status/gmd:MD_ProgressCode"),
        "bbox_wgs84": bbox,
        "layer": sorted({x["name"] for x in layer_links if x["name"]}),
        "link_layer": sorted(layer_links, key=lambda x: (x["protocol"], x["name"] or "")),
        "jumlah_link": len(links),
    }


def parse_iso_by_id(body: bytes) -> dict | None:
    md = ET.fromstring(body).find("gmd:MD_Metadata", NS)
    return parse_iso_record(md) if md is not None else None
