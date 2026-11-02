#!/usr/bin/env python3
"""
fetch_sources.py — Jalankan semua sumber aktif di config/sources.yaml lewat adapter seragam.

Urutan: sumber geojson_lokal dulu (jadi referensi extent dan pembanding), lalu wfs, lalu csw.
Sumber yang gagal dicatat lalu dilewati; sumber lain tetap jalan.

Output (deterministik, tanpa timestamp):
  processed/sources/<id>.geojson     skema standar (sources/base.py), EPSG:4326
  processed/catalog/records.json     katalog CSW (metadata, bukan geometri)
Respons mentah : raw/remote/<id>/<timestamp>/ (folder baru tiap run)
Laporan        : reports/fetch_sources.md, reports/fetch_sources.json (memuat timestamp run)
Pratinjau      : reports/preview_remote_vs_local.png

Jalankan (dari root repo):
    data-pipeline/.venv/bin/python data-pipeline/scripts/fetch_sources.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml  # noqa: E402
from shapely import make_valid, unary_union  # noqa: E402

from geo_common import CONFIG, DP, REPORTS, write_json  # noqa: E402
from sources.base import load_kelurahan_map, write_geojson  # noqa: E402
from sources.csw import Csw  # noqa: E402
from sources.geojson_lokal import GeoJsonLokal  # noqa: E402
from sources.wfs import Wfs  # noqa: E402

OUT_SOURCES = DP / "processed" / "sources"
OUT_CATALOG = DP / "processed" / "catalog" / "records.json"
OLD_PATH = {  # jalur lama (normalize_names.py / reproject_sungai.py) untuk uji identik
    "kelurahan": DP / "processed" / "geojson" / "batas-kelurahan.norm.geojson",
    "rt": DP / "processed" / "geojson" / "batas-rt.norm.geojson",
    "sungai": DP / "processed" / "geojson" / "sungai_ln.wgs84.geojson",
}
METRIC_CRS = "EPSG:32650"
TOL_SAME_PCT = 0.01
TOL_SMALL_PCT = 1.0
ADAPTERS = {"geojson_lokal": GeoJsonLokal, "wfs": Wfs, "csw": Csw}
ORDER = {"geojson_lokal": 0, "wfs": 1, "csw": 2}

log = logging.getLogger("fetch_sources")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pct(a: float, b: float) -> float | None:
    """Selisih b terhadap a dalam persen."""
    return round(100 * (b - a) / a, 4) if a else None


def check_identical(layer: str, path: Path) -> dict:
    """Bandingkan output adapter lokal dengan file jalur lama: jumlah, urutan, geometri, slug, nama."""
    new = json.loads(path.read_text(encoding="utf-8"))["features"]
    old = json.loads(OLD_PATH[layer].read_text(encoding="utf-8"))["features"]
    same_geom = len(new) == len(old) and all(a["geometry"] == b["geometry"] for a, b in zip(new, old))
    if layer == "sungai":
        same_keys = all(a["properties"]["nama"] == b["properties"]["nama"] for a, b in zip(new, old))
    else:
        same_keys = all(
            a["properties"]["slug"] == b["properties"].get("slug") and a["properties"]["kelurahan"] == b["properties"].get("nama_normal")
            for a, b in zip(new, old)
        )
    return {"file_lama": str(OLD_PATH[layer].relative_to(DP)), "jumlah": [len(new), len(old)], "geometri_sama": same_geom,
            "nama_slug_sama": same_keys, "identik": same_geom and same_keys}


def compare(layer: str, local, remote) -> dict:
    """Bandingkan dua GeoDataFrame skema standar (lokal vs WFS) untuk layer yang sama."""
    lm, rm = local.to_crs(METRIC_CRS), remote.to_crs(METRIC_CRS)
    lines = layer == "sungai"
    metric_l = float(lm.length.sum() if lines else lm.area.sum())
    metric_r = float(rm.length.sum() if lines else rm.area.sum())
    # make_valid hanya untuk hitungan (ada RT invalid, lihat geometry_check.md); output tidak diubah
    ul, ur = unary_union(make_valid(lm.geometry.values)), unary_union(make_valid(rm.geometry.values))
    if lines:
        geom_diff = {"hausdorff_m": round(ul.hausdorff_distance(ur), 3)}
    else:
        geom_diff = {"luas_beda_simetris_m2": round(ul.symmetric_difference(ur).area, 1),
                     "beda_simetris_persen": round(100 * ul.symmetric_difference(ur).area / ul.area, 4)}
    bl, br = local.total_bounds, remote.total_bounds
    extent_shift_m = max(abs(a - b) for a, b in zip(lm.total_bounds, rm.total_bounds))

    if layer == "rt":
        kl = Counter(zip(local["kelurahan"], local["rt"]))
        kr = Counter(zip(remote["kelurahan"], remote["rt"]))
    else:
        kl, kr = Counter(local["nama"]), Counter(remote["nama"])
    only_l, only_r = sorted(map(str, (kl - kr).elements())), sorted(map(str, (kr - kl).elements()))

    # Atribut: cocokkan per fid sumber (kedua sumber memakai fid yang sama bila berasal dari ekspor yang sama)
    al = dict(zip(local["fid_sumber"], local["atribut"]))
    ar = dict(zip(remote["fid_sumber"], remote["atribut"]))
    common = sorted(set(al) & set(ar))
    attr_diff, type_diff = Counter(), Counter()
    for fid in common:
        for k in set(al[fid]) | set(ar[fid]):
            a, b = al[fid].get(k), ar[fid].get(k)
            if a != b:
                # "261" vs 261: nilai sama, hanya tipe JSON berbeda
                (type_diff if a is not None and b is not None and str(a) == str(b) else attr_diff)[k] += 1
    unmatched_slug = sorted({str(x) for x in remote["kelurahan"]} - {str(x) for x in local["kelurahan"]}) if layer != "sungai" else []

    d_count = len(remote) - len(local)
    d_metric = pct(metric_l, metric_r)
    geom_pct = geom_diff.get("beda_simetris_persen", 0.0)
    worst = max(abs(d_metric or 0), abs(geom_pct))
    if lines:
        worst = max(worst, 100.0 if geom_diff["hausdorff_m"] > 1.0 else 0.0)
    status = ("sama" if d_count == 0 and worst <= TOL_SAME_PCT and not only_l and not only_r
              else "beda kecil" if d_count == 0 and worst <= TOL_SMALL_PCT else "beda signifikan")
    return {
        "layer": layer,
        "jumlah_lokal": len(local), "jumlah_wfs": len(remote), "selisih_jumlah": d_count,
        "besaran": "panjang total (m)" if lines else "luas total (m², EPSG:32650)",
        "nilai_lokal": round(metric_l, 1), "nilai_wfs": round(metric_r, 1), "selisih_persen": d_metric,
        **geom_diff,
        "extent_lokal": [round(v, 6) for v in bl], "extent_wfs": [round(v, 6) for v in br],
        "geser_extent_maks_m": round(extent_shift_m, 2),
        "kunci_hanya_lokal": only_l, "kunci_hanya_wfs": only_r,
        "kelurahan_wfs_tanpa_padanan": unmatched_slug,
        "fid_cocok": len(common), "atribut_beda_per_kolom": dict(sorted(attr_diff.items())),
        "atribut_beda_tipe_saja": dict(sorted(type_diff.items())),
        "status": status,
    }


def make_sources(cfgs: list[dict], stamp: str) -> list[dict]:
    active = [c for c in cfgs if c.get("aktif")]
    ids = [c["id"] for c in active]
    if len(set(ids)) != len(ids):
        raise ValueError("id sumber duplikat di sources.yaml")
    unknown = [c["id"] for c in active if c["tipe"] not in ADAPTERS]
    if unknown:
        raise ValueError(f"tipe sumber tidak dikenal: {unknown}")
    return sorted(active, key=lambda c: ORDER[c["tipe"]])  # stabil: urutan file dipertahankan per tipe


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cfgs = make_sources(yaml.safe_load((CONFIG / "sources.yaml").read_text(encoding="utf-8"))["sources"], stamp)
    kel_map = load_kelurahan_map()

    results, frames, catalog = [], {}, None
    for cfg in cfgs:
        entry = {"id": cfg["id"], "tipe": cfg["tipe"], "layer": cfg.get("layer"), "prioritas": cfg.get("prioritas")}
        try:
            kw = {"kelurahan_map": kel_map}
            if cfg["tipe"] in ("wfs", "csw"):
                kw["stamp"] = stamp
            if cfg["tipe"] == "wfs":
                ref = frames.get(("geojson_lokal", cfg["layer"]))
                kw["ref_bounds"] = tuple(ref.total_bounds) if ref is not None else None
            src = ADAPTERS[cfg["tipe"]](cfg, **kw)
            out = src.run()
            entry.update(src.info)
            if cfg["tipe"] == "csw":
                catalog = out
                write_json(OUT_CATALOG, {"sumber": cfg["url"], "jumlah": len(out), "records": out})
                entry.update(output=str(OUT_CATALOG.relative_to(DP)), sha256=sha256(OUT_CATALOG))
            else:
                frames[(cfg["tipe"], cfg["layer"])] = out
                path = OUT_SOURCES / f"{cfg['id']}.geojson"
                write_geojson(out, path)
                entry.update(output=str(path.relative_to(DP)), sha256=sha256(path), jumlah=len(out))
                if cfg["tipe"] == "geojson_lokal":
                    entry["uji_identik_jalur_lama"] = check_identical(cfg["layer"], path)
            entry["status"] = "ok"
        except Exception as err:  # noqa: BLE001 — satu sumber gagal tidak boleh menghentikan yang lain
            log.error("%s gagal: %s", cfg["id"], err)
            entry.update(status="gagal", error=f"{type(err).__name__}: {err}")
        results.append(entry)

    comparisons = [
        compare(layer, frames[("geojson_lokal", layer)], frames[("wfs", layer)])
        for layer in ("kelurahan", "rt", "sungai")
        if ("geojson_lokal", layer) in frames and ("wfs", layer) in frames
    ]
    report = {"timestamp_utc": stamp, "sumber": results, "perbandingan": comparisons}
    write_json(REPORTS / "fetch_sources.json", report)

    from report_remote import write_markdown, write_preview  # impor lambat: matplotlib hanya untuk laporan

    write_markdown(report, catalog)
    if ("geojson_lokal", "rt") in frames and ("wfs", "rt") in frames:
        write_preview(frames[("geojson_lokal", "rt")], frames[("wfs", "rt")], "rt", comparisons)

    for e in results:
        print(f"{e['id']:<26} {e['status']:<6} {e.get('jumlah', e.get('record', ''))!s:>5}  {e.get('error', '')}")
    for c in comparisons:
        print(f"{c['layer']:<10} lokal={c['jumlah_lokal']} wfs={c['jumlah_wfs']} selisih={c['selisih_persen']}% -> {c['status']}")
    return 0 if all(e["status"] == "ok" for e in results) else 1


if __name__ == "__main__":
    sys.exit(main())
