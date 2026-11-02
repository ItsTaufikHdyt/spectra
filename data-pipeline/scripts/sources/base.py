"""
base.py — Kontrak adapter sumber data + skema standar layer vektor.

Setiap adapter:
  fetch()          -> payload mentah (dict GeoJSON, atau list halaman untuk WFS)
  normalize(raw)   -> GeoDataFrame EPSG:4326 dengan kolom STANDARD_COLUMNS + geometry
  run()            -> normalize(fetch())

Skema standar (sama untuk semua sumber, agar bisa dibandingkan dan saling menggantikan):
  layer       kelurahan | rt | sungai
  sumber      id sumber dari config/sources.yaml
  fid_sumber  id fitur di sumber (properti `fid`, atau indeks bila tidak ada)
  nama        nama tampilan: nama kelurahan / "RT <rt>" / nama sungai
  kelurahan   nama kelurahan ternormalisasi (sesuai slug 3D Tiles) atau None
  kecamatan   nama kecamatan seperti di sumber (kapitalisasi dirapikan) atau None
  slug        slug folder 3D Tiles (config/kelurahan_map.csv) atau None
  rt          nomor RT (string) atau None
  atribut     dict atribut asli sumber, tidak diubah
Normalisasi nama memakai config/kelurahan_map.csv (hasil normalize_names.py), tidak menebak.

Mode generik (cfg["generik"] = True): untuk layer apa pun di luar LAYERS (mis. layer geoportal
yang ditambahkan dari website). `nama` diambil dari cfg["field_nama"], atau ditebak dari
NAME_FIELDS; kolom kelurahan/kecamatan/slug/rt dibiarkan None. Tiga layer bawaan tidak terpengaruh.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

import geopandas as gpd

DP = Path(__file__).resolve().parents[2]  # data-pipeline/
STANDARD_COLUMNS = ["layer", "sumber", "fid_sumber", "nama", "kelurahan", "kecamatan", "slug", "rt", "atribut"]
LAYERS = ("kelurahan", "rt", "sungai")
OUTPUT_CRS = "EPSG:4326"
DECIMALS = 8  # pembulatan koordinat output (~1 mm), sama dengan reproject_sungai.py
NAME_FIELDS = ("nama", "name", "judul", "keterangan")

log = logging.getLogger("sources")


def _key(name) -> str:
    return " ".join(str(name).upper().split())


def guess_name_field(keys) -> str | None:
    """Field nama: cocok persis dengan NAME_FIELDS (urut prioritas, tanpa peduli kapital), lalu
    berawalan salah satunya (mis. `nama_edt`, `namobj`); None bila tidak ada."""
    by_lower = {str(k).lower(): k for k in keys}
    exact = next((by_lower[f] for f in NAME_FIELDS if f in by_lower), None)
    if exact is not None:
        return exact
    return next((by_lower[k] for f in NAME_FIELDS for k in sorted(by_lower) if k.startswith(f[:4])), None)


def load_kelurahan_map(path: Path = DP / "config" / "kelurahan_map.csv") -> dict[str, dict]:
    """norm_key(nama apa pun yang dikenal) -> baris pemetaan {nama_normal, slug}."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    lookup = {}
    for row in rows:
        for name in (row["nama_geojson"], row["nama_normal"]):
            lookup[_key(name)] = row
    return lookup


class Source:
    tipe = "?"

    def __init__(self, cfg: dict, *, kelurahan_map: dict[str, dict] | None = None):
        self.cfg = cfg
        self.id = cfg["id"]
        self.layer = cfg.get("layer")
        self.kel_map = kelurahan_map if kelurahan_map is not None else load_kelurahan_map()
        self.info: dict = {}  # catatan run (jumlah halaman, urutan sumbu, folder raw, ...)

    def fetch(self):
        raise NotImplementedError

    def normalize(self, raw) -> gpd.GeoDataFrame:
        raise NotImplementedError

    def run(self):
        return self.normalize(self.fetch())

    # --- dipakai adapter geometri -------------------------------------------------
    def standardize(self, features: list[dict], crs: str) -> gpd.GeoDataFrame:
        """Fitur GeoJSON (properti asli) -> GeoDataFrame skema standar di EPSG:4326."""
        generic = bool(self.cfg.get("generik"))
        if self.layer not in LAYERS and not generic:
            raise ValueError(f"{self.id}: layer {self.layer!r} tidak dikenal")
        if generic:
            keys = {k for f in features for k in (f.get("properties") or {})}
            self.name_field = self.cfg.get("field_nama") or guess_name_field(sorted(keys))
            self.info["field_nama"] = self.name_field
        rows = []
        for i, f in enumerate(features):
            p = f.get("properties") or {}
            rows.append({**self._fields(p), "fid_sumber": str(p.get("fid", i)), "atribut": p})
        gdf = gpd.GeoDataFrame.from_features(features, crs=crs)[["geometry"]]
        for col in STANDARD_COLUMNS:
            gdf[col] = [r.get(col) for r in rows]
        gdf["layer"], gdf["sumber"] = self.layer, self.id
        if gdf.crs != OUTPUT_CRS:
            gdf = gdf.to_crs(OUTPUT_CRS)
        return gdf[STANDARD_COLUMNS + ["geometry"]]

    def _fields(self, p: dict) -> dict:
        if self.cfg.get("generik"):
            v = p.get(self.name_field) if self.name_field else None
            return {"nama": str(v) if v is not None else None}
        if self.layer == "sungai":
            return {"nama": p.get("nama")}
        kel_raw = p.get("wadmkd") if self.layer == "kelurahan" else p.get("kelurahan")
        kec_raw = p.get("wadmkc") if self.layer == "kelurahan" else p.get("kecamatan")
        m = self.kel_map.get(_key(kel_raw)) if kel_raw else None
        out = {
            "kelurahan": m["nama_normal"] if m else None,
            "slug": (m["slug"] or None) if m else None,
            "kecamatan": str(kec_raw).title() if kec_raw else None,
        }
        if self.layer == "kelurahan":
            out["nama"] = out["kelurahan"] or kel_raw
        else:
            out["rt"] = str(p.get("rt")) if p.get("rt") is not None else None
            out["nama"] = f"RT {out['rt']}"
        return out


def round_geometry(gdf: gpd.GeoDataFrame, decimals: int = DECIMALS) -> gpd.GeoDataFrame:
    import numpy as np
    import shapely

    out = gdf.copy()
    out["geometry"] = shapely.transform(out.geometry.values, lambda c: np.round(c, decimals))
    return out


def write_geojson(gdf: gpd.GeoDataFrame, path: Path) -> None:
    """Tulis GeoJSON RFC 7946 deterministik (tanpa id/crs/timestamp, urutan tetap)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fc = gdf.to_geo_dict(drop_id=True)
    path.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
