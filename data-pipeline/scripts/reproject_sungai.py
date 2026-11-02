#!/usr/bin/env python3
"""
reproject_sungai.py — Proyeksi sungai EPSG:32650 (UTM 50N) -> EPSG:4326 + QC panjang.

Input (read-only) : raw/geojson/sungai_ln_5k.json, raw/geojson/batas-kelurahan.json (validasi)
Output            : processed/geojson/sungai_ln.wgs84.geojson   (GeoJSON RFC 7946, lon/lat)
                    reports/sungai_reproject.json, reports/sungai_reproject.md

Konversi CRS dilakukan di sini (ETL), bukan di browser (AGENTS.md §3.3).
Nama & kategori fitur TIDAK diubah; temuan hanya ditandai di `qc_catatan`.

Jalankan (dari root repo):
    data-pipeline/.venv/bin/python data-pipeline/scripts/reproject_sungai.py
"""

from __future__ import annotations

import sys

from pyproj import Transformer
from shapely import unary_union
from shapely.geometry import Point, shape

from geo_common import (
    GEOD,
    KELURAHAN_FILE,
    OUT_GEOJSON,
    REPORTS,
    SUNGAI_FILE,
    UTM50N,
    WGS84,
    geom,
    r,
    read_geojson,
    valid_or_fixed,
    write_json,
)

SOURCE_CRS_NAMES = {"urn:ogc:def:crs:EPSG::32650", "EPSG:32650"}
# Extent tile/kota yang diharapkan (derajat), sesuai batas kelurahan.
EXPECTED_BBOX = (117.39, 0.02, 117.57, 0.21)  # (min lon, min lat, max lon, max lat)
BBOX_TOLERANCE_DEG = 0.01  # ±~1,1 km
LENGTH_TOLERANCE_PCT = 0.1
# Alur hampir lurus + banyak di luar batas kota -> perlu dicek (garis bantu/kanal/alur laut?).
SINUOSITY_FLAG = 1.15
OUTSIDE_CITY_FLAG_PCT = 10.0
DECIMALS = 8  # ~1 mm; pembulatan stabil agar output deterministik

# Penanda manual (TIDAK mengubah data). Kunci = (id, nama) agar tidak salah sasaran.
FEATURE_FLAGS = {
    (0, "Drainase Dahllia"): [
        "Kandidat koreksi ejaan: 'Dahllia' kemungkinan 'Dahlia' (belum diputuskan).",
        "Kandidat koreksi kategori: drainase, bukan sungai (belum diputuskan).",
        "id = 0, berbeda dari pola id 1–4 fitur lain.",
    ]
}

_to_wgs84 = Transformer.from_crs(UTM50N, WGS84, always_xy=True)


def reproject_coords(coords):
    """Proyeksikan koordinat bersarang (MultiLineString/LineString) dan bulatkan."""
    if isinstance(coords[0], (int, float)):
        lon, lat = _to_wgs84.transform(coords[0], coords[1])
        return [round(lon, DECIMALS), round(lat, DECIMALS)]
    return [reproject_coords(c) for c in coords]


def bbox_of(geoms) -> tuple[float, float, float, float]:
    b = unary_union(geoms).bounds
    return tuple(r(x, 6) for x in b)


def main() -> int:
    src = read_geojson(SUNGAI_FILE)
    crs_name = (src.get("crs") or {}).get("properties", {}).get("name")
    if crs_name not in SOURCE_CRS_NAMES:
        print(f"ERROR: CRS sumber bukan EPSG:32650 (ditemukan: {crs_name!r}); proyeksi dibatalkan.", file=sys.stderr)
        return 1

    city = unary_union([valid_or_fixed(geom(f)) for f in read_geojson(KELURAHAN_FILE)["features"]])

    out_features, rows = [], []
    for f in src["features"]:
        p = dict(f["properties"])
        g_utm = geom(f)
        length_utm = g_utm.length  # meter, di CRS asli
        new_geometry = {"type": f["geometry"]["type"], "coordinates": reproject_coords(f["geometry"]["coordinates"])}
        g_wgs = shape(new_geometry)
        length_geod = GEOD.geometry_length(g_wgs)
        inside_pct = 100 * GEOD.geometry_length(g_wgs.intersection(city)) / length_geod if length_geod else 0.0

        attr_m = float(p.get("panjang_m") or 0)
        attr_km_m = float(p.get("panjang_km") or 0) * 1000
        attr_panjang_m = float(p.get("panjang") or 0) * 1000  # `panjang` bernilai sama dengan km
        diffs = {
            "selisih_vs_panjang_m_persen": r(100 * (length_utm - attr_m) / attr_m, 4) if attr_m else None,
            "selisih_vs_panjang_km_persen": r(100 * (length_utm - attr_km_m) / attr_km_m, 4) if attr_km_m else None,
            "selisih_vs_panjang_persen": r(100 * (length_utm - attr_panjang_m) / attr_panjang_m, 4) if attr_panjang_m else None,
        }
        main = max(getattr(g_utm, "geoms", [g_utm]), key=lambda line: line.length)
        ends = Point(main.coords[0]).distance(Point(main.coords[-1]))
        sinuosity = main.length / ends if ends else 0.0
        notes = list(FEATURE_FLAGS.get((p.get("id"), p.get("nama")), []))
        if any(v is not None and abs(v) > LENGTH_TOLERANCE_PCT for v in diffs.values()):
            notes.append(f"Panjang hitung ulang berbeda > {str(LENGTH_TOLERANCE_PCT).replace('.', ',')}% dari atribut.")

        if sinuosity and sinuosity < SINUOSITY_FLAG and 100 - inside_pct > OUTSIDE_CITY_FLAG_PCT:
            notes.append(
                f"Alur hampir lurus (sinuositas {str(r(sinuosity, 3)).replace('.', ',')}) dan "
                f"{str(r(100 - inside_pct, 1)).replace('.', ',')}% panjang di luar batas kota: cek apakah alur sungai "
                "sebenarnya atau garis bantu/kanal/alur laut."
            )
        p.update({"panjang_utm_m": r(length_utm, 3), "qc_catatan": notes})
        out_features.append({"type": "Feature", "properties": p, "geometry": new_geometry})
        rows.append(
            {
                "id": p.get("id"),
                "nama": p.get("nama"),
                "panjang_km_atribut": r(float(p.get("panjang_km") or 0), 4),
                "panjang_m_atribut": r(attr_m, 3),
                "panjang_utm_m": r(length_utm, 3),
                "panjang_geodesik_m": r(length_geod, 3),
                **diffs,
                "persen_panjang_di_dalam_batas_kota": r(inside_pct, 2),
                "sinuositas_bagian_utama": r(sinuosity, 3),
                "bbox_wgs84": list(bbox_of([g_wgs])),
                "catatan": notes,
            }
        )

    bbox = bbox_of([shape(f["geometry"]) for f in out_features])
    e = EXPECTED_BBOX
    tol = BBOX_TOLERANCE_DEG
    bbox_ok = bbox[0] >= e[0] - tol and bbox[1] >= e[1] - tol and bbox[2] <= e[2] + tol and bbox[3] <= e[3] + tol
    max_len_km = max(x["panjang_utm_m"] for x in rows) / 1000

    report = {
        "sumber": SUNGAI_FILE.name,
        "crs_sumber": crs_name,
        "crs_output": "EPSG:4326 (GeoJSON RFC 7946, tanpa anggota 'crs')",
        "fitur": rows,
        "extent_output": {
            "bbox_wgs84": list(bbox),
            "diharapkan": list(EXPECTED_BBOX),
            "toleransi_derajat": tol,
            "sesuai": bbox_ok,
        },
        "penanda_file": [
            f"Nama file '{SUNGAI_FILE.name}' memuat '_5k', sedangkan sungai terpanjang {max_len_km:.1f} km. "
            "Bila '_5k' berarti 5 km, nama tidak sesuai isi; bila berarti skala peta 1:5.000 (lazim pada data RBI), "
            "nama sesuai. Belum diputuskan; output memakai nama tanpa '_5k'."
        ],
    }
    write_json(OUT_GEOJSON / "sungai_ln.wgs84.geojson", {"type": "FeatureCollection", "features": out_features}, indent=None)
    write_json(REPORTS / "sungai_reproject.json", report)

    md = [
        "# Laporan proyeksi sungai (EPSG:32650 → EPSG:4326)",
        "",
        f"Sumber: `raw/geojson/{SUNGAI_FILE.name}` (CRS `{crs_name}`). Output: `processed/geojson/sungai_ln.wgs84.geojson`.",
        "",
        "| id | nama | panjang_km atribut | panjang UTM (m) | selisih vs panjang_m (%) | di dalam batas kota (%) | catatan |",
        "|---|---|---|---|---|---|---|",
        *(
            f"| {x['id']} | {x['nama']} | {x['panjang_km_atribut']} | {x['panjang_utm_m']} | {x['selisih_vs_panjang_m_persen']} | "
            f"{x['persen_panjang_di_dalam_batas_kota']} | {'<br>'.join(x['catatan']) or '-'} |"
            for x in rows
        ),
        "",
        f"Extent output: {list(bbox)} — diharapkan {list(EXPECTED_BBOX)} ±{tol}° → **{'sesuai' if bbox_ok else 'TIDAK sesuai'}**.",
        "",
        "Penanda file:",
        "",
        *(f"- {x}" for x in report["penanda_file"]),
    ]
    (REPORTS / "sungai_reproject.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    for x in rows:
        print(f"{x['nama']:<20} UTM={x['panjang_utm_m']:>10.1f} m  atribut={x['panjang_m_atribut']:>10.1f} m  "
              f"selisih={x['selisih_vs_panjang_m_persen']}%  di dalam kota={x['persen_panjang_di_dalam_batas_kota']}%")
    print(f"Extent output: {bbox} -> {'sesuai' if bbox_ok else 'TIDAK sesuai'} dengan {EXPECTED_BBOX} ±{tol}°")
    print(f"Ditulis: {OUT_GEOJSON / 'sungai_ln.wgs84.geojson'}, {REPORTS / 'sungai_reproject.md'} dan .json")
    return 0 if bbox_ok else 1


if __name__ == "__main__":
    sys.exit(main())
