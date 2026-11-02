#!/usr/bin/env python3
"""
normalize_names.py — Pemetaan nama kelurahan GeoJSON ke slug 3D Tiles + normalisasi RT.

Sumber kebenaran slug: processed/3dtiles/master-tileset.json (fallback: folder raw/3d/).
Input (read-only) : raw/geojson/batas-kelurahan.json, raw/geojson/batas-rt.json
Output            : config/kelurahan_map.csv
                    processed/geojson/batas-kelurahan.norm.geojson
                    processed/geojson/batas-rt.norm.geojson

Geometri TIDAK diubah (geometri invalid hanya ditandai lewat geometry_valid).
Field asli tetap ada; nilai sebelum normalisasi disimpan di *_asli.

Jalankan (dari root repo):
    data-pipeline/.venv/bin/python data-pipeline/scripts/normalize_names.py
"""

from __future__ import annotations

import collections
import csv
import io
import json
import sys

from geo_common import (
    CONFIG,
    KELURAHAN_FILE,
    MASTER_TILESET,
    OUT_GEOJSON,
    RAW_3D,
    RT_FILE,
    geom,
    norm_key,
    read_geojson,
    write_json,
)

# Pemetaan EKSPLISIT nama GeoJSON -> nama sesuai slug (bukan penebakan otomatis).
# Tambahkan baris di sini bila ada sumber baru dengan ejaan berbeda.
EXPLICIT_NAME_MAP = {
    "Berbas Pantai": "Berebas Pantai",  # ejaan di GeoJSON vs slug berebas_pantai
    "Api-Api": "Api Api",  # tanda hubung vs slug api_api
}

# Klasifikasi EKSPLISIT nilai `keterangan` RT. Bukti geometri (reports/geometry_check.md,
# bagian "Bukti status pulau"): semua nilai di KETERANGAN_PULAU terpisah dari daratan utama
# (jarak 52 m – 4,9 km), semua nilai di KETERANGAN_DARATAN menyatu (jarak 0).
# Ini HANYA flag is_pulau — keputusan tampil/tidak ada di tangan pengguna.
KETERANGAN_PULAU = frozenset(
    {
        "No Name",
        "Pulau Kedindingan",
        "Pulau Melahing",
        "Melahing",
        "Pulau Agar-Agar",
        "Pulau Badak-Badak Barat",
        "Pulau Badak-Badak Timur",
        "Pulau Beras Basah",
        "Pulau Gusung",
        "Gusung",
        "Pulau Karangkiampau",
        "Pulau Panjang",
        "Pulau Segajah",
        "Pulau Selokia Dalam",
        "Pulau Selokia Luar",
        "Pulau Siacca",
        "Pulau Tihi-Tihi",
        "Tihi-Tihi",
        "Selangan",
    }
)
KETERANGAN_DARATAN = frozenset({None, "Bontang Kuala", "Bontang Lestari", "Guntung", "Satimpo", "Tanjung Laut Indah"})


def load_slugs() -> tuple[list[str], str]:
    """Slug kelurahan dari master-tileset.json; fallback ke nama folder raw/3d/."""
    try:
        master = read_geojson(MASTER_TILESET)  # JSON biasa, dibaca read-only
        slugs = sorted({c["content"]["uri"].split("/")[0] for c in master["root"]["children"]})
        if slugs:
            return slugs, str(MASTER_TILESET.relative_to(MASTER_TILESET.parents[2]))
    except (OSError, KeyError, ValueError) as err:
        print(f"PERINGATAN: master-tileset.json tidak terbaca ({err}); memakai folder raw/3d/", file=sys.stderr)
    slugs = sorted(
        p.name.removeprefix("Kelurahan ").strip().lower().replace(" ", "_")
        for p in RAW_3D.iterdir()
        if p.is_dir() and p.name.startswith("Kelurahan ")
    )
    return slugs, "raw/3d/ (fallback)"


def to_slug(name: str) -> str:
    return "_".join(name.lower().split())


def build_map(kel_names: list[str], slugs: list[str]) -> list[dict]:
    slug_set = set(slugs)
    rows = []
    for name in kel_names:
        normal = EXPLICIT_NAME_MAP.get(name, name)
        slug = to_slug(normal)
        if slug not in slug_set:
            status = "tidak_cocok"
            slug = ""
        elif name in EXPLICIT_NAME_MAP:
            status = "pemetaan_eksplisit"
        else:
            status = "cocok_langsung"
        rows.append({"nama_geojson": name, "nama_normal": normal, "slug": slug, "status_cocok": status})
    return sorted(rows, key=lambda x: (x["slug"] or "~", x["nama_geojson"]))


def write_csv(path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["nama_geojson", "nama_normal", "slug", "status_cocok"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


def recase(original: str, canonical_by_key: dict[str, str]) -> str:
    """Ganti HANYA kapitalisasi: ambil ejaan kanonik bila hurufnya identik, else title()."""
    candidate = canonical_by_key.get(norm_key(original), str(original).title())
    if candidate.upper() != str(original).upper():  # pengaman: tidak boleh mengubah huruf
        raise ValueError(f"Normalisasi mengubah lebih dari kapitalisasi: {original!r} -> {candidate!r}")
    return candidate


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def main() -> int:
    slugs, slug_source = load_slugs()
    kel = read_geojson(KELURAHAN_FILE)["features"]
    rt = read_geojson(RT_FILE)["features"]

    # --- Pemetaan kelurahan -> slug -------------------------------------------------
    kel_names = [f["properties"]["wadmkd"] for f in kel]
    mapping = build_map(kel_names, slugs)
    write_csv(CONFIG / "kelurahan_map.csv", mapping)
    by_name = {m["nama_geojson"]: m for m in mapping}
    unmatched_kel = [m["nama_geojson"] for m in mapping if m["status_cocok"] == "tidak_cocok"]
    slugs_without_geojson = sorted(set(slugs) - {m["slug"] for m in mapping})

    canonical_kel = {norm_key(n): n for n in kel_names}
    canonical_kec = {norm_key(f["properties"]["wadmkc"]): f["properties"]["wadmkc"] for f in kel}

    out_kel = []
    for f in kel:
        p = dict(f["properties"])
        m = by_name[p["wadmkd"]]
        p.update(
            {
                "slug": m["slug"] or None,
                "nama_normal": m["nama_normal"],
                "kecamatan": p.get("wadmkc"),
                "geometry_valid": geom(f).is_valid,
            }
        )
        out_kel.append({"type": "Feature", "properties": p, "geometry": f["geometry"]})

    # --- RT ------------------------------------------------------------------------
    pair_count = collections.Counter((norm_key(f["properties"]["kelurahan"]), str(f["properties"]["rt"])) for f in rt)
    failed, unknown_ket = [], collections.Counter()
    out_rt = []
    for i, f in enumerate(rt):
        p = dict(f["properties"])
        try:
            kel_name = recase(p["kelurahan"], canonical_kel)
            kec_name = recase(p["kecamatan"], canonical_kec)
        except ValueError as err:
            failed.append({"index": i, "kelurahan": p.get("kelurahan"), "rt": p.get("rt"), "alasan": str(err)})
            kel_name, kec_name = p["kelurahan"], p["kecamatan"]
        m = by_name.get(kel_name)
        if m is None or not m["slug"]:
            failed.append({"index": i, "kelurahan": p.get("kelurahan"), "rt": p.get("rt"), "alasan": "tidak ada di batas-kelurahan / slug"})
        ket = p.get("keterangan")
        if ket not in KETERANGAN_PULAU and ket not in KETERANGAN_DARATAN:
            unknown_ket[ket] += 1
        p.update(
            {
                "kelurahan_asli": p["kelurahan"],
                "kecamatan_asli": p["kecamatan"],
                "kelurahan": kel_name,
                "kecamatan": kec_name,
                "nama_normal": m["nama_normal"] if m else None,
                "slug": (m["slug"] or None) if m else None,
                "is_pulau": ket in KETERANGAN_PULAU,
                "geometry_valid": geom(f).is_valid,
                "rt_duplikat": pair_count[(norm_key(f["properties"]["kelurahan"]), str(f["properties"]["rt"]))] > 1,
            }
        )
        out_rt.append({"type": "Feature", "properties": p, "geometry": f["geometry"]})

    if unknown_ket:
        # Nilai baru belum diklasifikasi: berhenti agar tidak salah flag diam-diam.
        print(f"ERROR: nilai keterangan belum diklasifikasi (tambahkan ke KETERANGAN_*): {dict(unknown_ket)}", file=sys.stderr)
        return 1

    write_json(OUT_GEOJSON / "batas-kelurahan.norm.geojson", feature_collection(out_kel), indent=None)
    write_json(OUT_GEOJSON / "batas-rt.norm.geojson", feature_collection(out_rt), indent=None)

    matched = len(rt) - len({x["index"] for x in failed})
    print(f"Sumber slug: {slug_source} ({len(slugs)} slug)")
    print(f"Kelurahan: {len(kel)} | tidak cocok: {unmatched_kel or 'tidak ada'} | slug tanpa GeoJSON: {slugs_without_geojson or 'tidak ada'}")
    print(f"RT dicocokkan: {matched}/{len(rt)} | gagal: {len(failed)}")
    for x in failed:
        print("  GAGAL:", json.dumps(x, ensure_ascii=False))
    print(f"RT is_pulau: {sum(p['properties']['is_pulau'] for p in out_rt)} | rt_duplikat: {sum(p['properties']['rt_duplikat'] for p in out_rt)} "
          f"| geometry_valid=false: {sum(not p['properties']['geometry_valid'] for p in out_rt)}")
    print(f"Ditulis: {CONFIG / 'kelurahan_map.csv'}")
    print(f"Ditulis: {OUT_GEOJSON / 'batas-kelurahan.norm.geojson'}, {OUT_GEOJSON / 'batas-rt.norm.geojson'}")
    return 1 if failed or unmatched_kel else 0


if __name__ == "__main__":
    sys.exit(main())
