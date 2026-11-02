"""
geojson_lokal.py — Adapter GeoJSON lokal (raw/geojson/*.json), jalur yang sudah ada.

Membaca file read-only. Geometri tidak diubah kecuali proyeksi bila srs sumber bukan
EPSG:4326 (sungai: EPSG:32650 -> 4326, dibulatkan 8 desimal seperti reproject_sungai.py),
sehingga hasilnya identik dengan processed/geojson/*.geojson dari jalur lama.
"""

from __future__ import annotations

import json

from .base import DP, OUTPUT_CRS, Source, log, round_geometry


class GeoJsonLokal(Source):
    tipe = "geojson_lokal"

    def fetch(self) -> dict:
        path = DP / self.cfg["url"]
        with open(path, "rb") as f:  # read-only
            data = json.loads(f.read().decode("utf-8"))
        declared = ((data.get("crs") or {}).get("properties") or {}).get("name")
        expected = self.cfg["srs"]
        # File tanpa anggota crs dianggap sesuai config (RFC 7946 = WGS84); bila ada, harus cocok.
        if declared and declared.replace("urn:ogc:def:crs:", "").replace("::", ":") != expected:
            raise ValueError(f"{self.id}: CRS file {declared!r} != srs config {expected!r}")
        self.info.update(file=self.cfg["url"], crs_file=declared, fitur=len(data["features"]))
        log.info("%s: %d fitur dari %s", self.id, len(data["features"]), self.cfg["url"])
        return data

    def normalize(self, raw: dict):
        gdf = self.standardize(raw["features"], self.cfg["srs"])
        return gdf if self.cfg["srs"] == OUTPUT_CRS else round_geometry(gdf)
