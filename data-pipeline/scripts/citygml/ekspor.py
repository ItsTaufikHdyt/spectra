#!/usr/bin/env python3
"""Ekspor bangunan satu kelurahan dari PostGIS ke CityJSONSeq (CityJSON 2.0, EPSG:32650).

  data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/ekspor.py --slug bontang_lestari

Keluaran: data-pipeline/processed/buildings/<slug>.city.jsonl
  baris 1 : metadata CityJSON (transform, referenceSystem, extent), tanpa CityObjects
  baris 2+: satu CityJSONFeature per bangunan (urut id; deterministik), vertex bilangan bulat
Hanya bangunan bertinggi >= 0,1 m (ADR-002); sisanya tetap di basis data dengan qc_flag.
Atribut: id, gml_id, nama ("Bangunan <id>"), tinggi, jumlah_lantai (dihilangkan bila kosong), luas_tapak.
Geometri: MultiSurface LOD 2 dengan semantik hasil klasifikasi ulang (lantai/atap/dinding). Z dasar = 0.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DP = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DP / "db"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from koneksi import buka_koneksi  # noqa: E402

SKALA = 0.001                # presisi 1 mm
TINGGI_MIN = 0.1             # m
JENIS = {"G": "GroundSurface", "R": "RoofSurface", "W": "WallSurface"}
KELUAR = DP / "processed" / "buildings"


def urai_polyhedral(ewkt: str) -> list[list[list[tuple[float, float, float]]]]:
    """'SRID=...;POLYHEDRALSURFACE(((x y z, ...)),((...),(lubang)))' -> [patch][cincin][titik]."""
    badan = ewkt.split("POLYHEDRALSURFACE", 1)[1].strip()
    if badan.startswith("Z"):
        badan = badan[1:].strip()
    patch, kedalaman, awal = [], 0, 0
    for i, ch in enumerate(badan):
        if ch == "(":
            kedalaman += 1
            if kedalaman == 2:
                awal = i
        elif ch == ")":
            if kedalaman == 2:
                patch.append(badan[awal:i + 1])
            kedalaman -= 1
    hasil = []
    for p in patch:
        cincin = []
        for c in re.findall(r"\(([^()]*)\)", p):
            cincin.append([tuple(float(v) for v in t.split()) for t in c.split(",")])
        hasil.append(cincin)
    return hasil


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--validasi", action="store_true", help="setelah ekspor, validasi skema CityJSON (validasi_cityjson.py; ~50 s per 2.000 bangunan)")
    a = ap.parse_args(argv)

    with buka_koneksi() as conn:
        baris = conn.execute(
            "SELECT id, gml_id, tinggi, jumlah_lantai, luas_tapak, jenis_permukaan, ST_AsEWKT(geometri_lod2) "
            "FROM core.bangunan WHERE slug = %s AND tinggi >= %s AND geometri_lod2 IS NOT NULL ORDER BY id",
            (a.slug, TINGGI_MIN),
        ).fetchall()
        n_semua = conn.execute("SELECT count(*) FROM core.bangunan WHERE slug = %s", (a.slug,)).fetchone()[0]
    if not baris:
        raise SystemExit(f"Tidak ada bangunan untuk {a.slug!r}")

    bangunan = [(r, urai_polyhedral(r[6])) for r in baris]
    semua = [t for _, patch in bangunan for p in patch for c in p for t in c]
    tx, ty = min(t[0] for t in semua), min(t[1] for t in semua)
    ext = [tx, ty, min(t[2] for t in semua), max(t[0] for t in semua), max(t[1] for t in semua), max(t[2] for t in semua)]

    KELUAR.mkdir(parents=True, exist_ok=True)
    tujuan = KELUAR / f"{a.slug}.city.jsonl"
    kepala = {
        "type": "CityJSON", "version": "2.0",
        "transform": {"scale": [SKALA, SKALA, SKALA], "translate": [round(tx, 3), round(ty, 3), 0.0]},
        "metadata": {"referenceSystem": "https://www.opengis.net/def/crs/EPSG/0/32650",
                     "geographicalExtent": [round(v, 3) for v in ext],
                     "title": f"Bangunan {a.slug} (CityGML -> PostGIS -> CityJSONSeq)"},
        "CityObjects": {}, "vertices": [],
    }
    with open(tujuan, "w", encoding="utf-8") as f:
        f.write(json.dumps(kepala, separators=(",", ":")) + "\n")
        for (id_, gml_id, tinggi, lantai, luas, jenis, _), patch in bangunan:
            indeks: dict[tuple[int, int, int], int] = {}
            vertices: list[list[int]] = []

            def v(t):
                k = (round((t[0] - tx) / SKALA), round((t[1] - ty) / SKALA), round(t[2] / SKALA))
                if k not in indeks:
                    indeks[k] = len(vertices)
                    vertices.append(list(k))
                return indeks[k]

            batas = [[[v(t) for t in cincin[:-1]] for cincin in p] for p in patch]  # titik penutup dibuang (cincin CityJSON terbuka)
            urut = ("G", "R", "W")
            semantik = {"surfaces": [{"type": JENIS[k]} for k in urut], "values": [urut.index(j) for j in jenis]}
            atribut = {"id": id_, "gml_id": gml_id, "nama": f"Bangunan {id_}", "tinggi": float(tinggi),
                       "jumlah_lantai": int(lantai) if lantai is not None else None,
                       "luas_tapak": float(luas) if luas is not None else None}
            atribut = {k: x for k, x in atribut.items() if x is not None}
            fitur = {
                "type": "CityJSONFeature", "id": id_,
                "CityObjects": {id_: {"type": "Building", "attributes": atribut,
                                      "geometry": [{"type": "MultiSurface", "lod": "2", "boundaries": batas, "semantics": semantik}]}},
                "vertices": vertices,
            }
            f.write(json.dumps(fitur, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"Ditulis {tujuan} ({tujuan.stat().st_size / 1048576:.1f} MB): {len(bangunan)} dari {n_semua} bangunan "
          f"(dikeluarkan karena tinggi < {TINGGI_MIN} m: {n_semua - len(bangunan)})")
    if a.validasi:
        from validasi_cityjson import main as validasi  # noqa: E402
        return validasi([str(tujuan)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
