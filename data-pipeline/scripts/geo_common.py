"""
geo_common.py — Utilitas bersama skrip GeoJSON (check_geometry, normalize_names,
reproject_sungai, show_data).

Prinsip:
  * File di data-pipeline/raw/ HANYA dibaca (mode 'rb'), tidak pernah ditulis.
  * Hitungan metrik (luas, jarak, irisan) dilakukan di EPSG:32650 (UTM 50N) atau
    geodesik WGS84 — bukan di derajat.
  * Output ditulis deterministik (urutan stabil, tanpa timestamp) agar hash bisa dibandingkan.
"""

from __future__ import annotations

import json
from pathlib import Path

from pyproj import Geod, Transformer
from shapely import make_valid
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from shapely.ops import transform

DP = Path(__file__).resolve().parents[1]  # data-pipeline/
RAW_GEOJSON = DP / "raw" / "geojson"
RAW_CITYGML = DP / "raw" / "citygml"
MASTER_TILESET = DP / "processed" / "3dtiles" / "master-tileset.json"
OUT_GEOJSON = DP / "processed" / "geojson"
REPORTS = DP / "reports"
CONFIG = DP / "config"

KELURAHAN_FILE = RAW_GEOJSON / "batas-kelurahan.json"
RT_FILE = RAW_GEOJSON / "batas-rt.json"
SUNGAI_FILE = RAW_GEOJSON / "sungai_ln_5k.json"

# batas-kelurahan.json & batas-rt.json tidak mencantumkan CRS dan berkoordinat derajat.
# Asumsi: WGS84 lon/lat (default GeoJSON RFC 7946). Atribut srs_id menyebut sumber asalnya
# SRGI2013 UTM 50N; SRGI2013 vs WGS84 berbeda < 1 m — diabaikan untuk QC ini.
WGS84 = "EPSG:4326"
UTM50N = "EPSG:32650"

_to_utm = Transformer.from_crs(WGS84, UTM50N, always_xy=True)
GEOD = Geod(ellps="WGS84")


def read_geojson(path: Path) -> dict:
    """Baca GeoJSON secara read-only."""
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def geom(feature: dict):
    return shape(feature["geometry"])


def to_utm(g):
    """Geometri WGS84 -> UTM 50N (meter)."""
    return transform(_to_utm.transform, g)


def valid_or_fixed(g):
    """Untuk HITUNGAN saja (irisan/luas): geometri invalid diperbaiki sementara di memori.
    Data keluaran tetap memakai geometri asli."""
    return g if g.is_valid else make_valid(g)


def geodesic_area_m2(g_wgs84) -> float:
    """Luas geodesik (m²) pada elipsoid WGS84; hole dikurangkan.

    pyproj menjumlahkan luas BERTANDA (tergantung arah putar ring), sehingga bagian
    multipolygon dengan orientasi berlawanan saling mengurangi. Karena itu tiap poligon
    diorientasikan dulu (exterior berlawanan jarum jam) dan dihitung terpisah.
    """
    polys = list(g_wgs84.geoms) if hasattr(g_wgs84, "geoms") else [g_wgs84]
    return sum(GEOD.geometry_area_perimeter(orient(p, sign=1.0))[0] for p in polys)


def norm_key(name: str) -> str:
    """Kunci pencocokan: huruf besar, spasi rapat. 'Api-Api' & 'API-API' -> 'API-API'."""
    return " ".join(str(name).upper().split())


def write_json(path: Path, obj, *, indent: int | None = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))
    path.write_text(text + "\n", encoding="utf-8")


def r(x: float, nd: int = 3) -> float:
    """Pembulatan stabil untuk laporan (hindari -0.0)."""
    v = round(float(x), nd)
    return 0.0 if v == 0 else v
