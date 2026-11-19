#!/usr/bin/env python3
"""Validasi skema CityJSON 2.0 untuk berkas CityJSONSeq hasil ekspor.py (pengganti `cjio validate`, yang butuh cjvalpy).

  data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/validasi_cityjson.py data-pipeline/processed/buildings/bontang_lestari.city.jsonl

Baris 1 (metadata) divalidasi dengan cityjson.min.schema.json, baris berikutnya (CityJSONFeature) dengan
cityjsonfeature.min.schema.json; keduanya dari data-pipeline/schemas/cityjson-2.0/ (tanpa jaringan).
Selain skema, dihitung PERINGATAN geometri sederhana: cincin < 3 titik, titik berulang berurutan dalam satu cincin,
vertex tidak dipakai, dan vertex kembar dalam satu fitur. Kode keluar 1 bila ada galat skema; peringatan tidak menggagalkan.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

DP = Path(__file__).resolve().parents[2]
SKEMA = DP / "schemas" / "cityjson-2.0"


def muat_skema(nama: str) -> Draft7Validator:
    skema = json.loads((SKEMA / nama).read_text(encoding="utf-8"))
    Draft7Validator.check_schema(skema)
    return Draft7Validator(skema)


def cincin_iter(batas):
    """Telusuri semua cincin (daftar indeks vertex) pada boundaries MultiSurface/Solid dengan kedalaman berapa pun."""
    if batas and isinstance(batas[0], int):
        yield batas
    else:
        for b in batas:
            yield from cincin_iter(b)


def peringatan_fitur(fitur: dict, hitung: collections.Counter) -> None:
    pakai: set[int] = set()
    for obj in fitur.get("CityObjects", {}).values():
        for g in obj.get("geometry", []):
            for c in cincin_iter(g.get("boundaries", [])):
                pakai.update(c)
                if len(c) < 3:
                    hitung["cincin_kurang_3_titik"] += 1
                if any(a == b for a, b in zip(c, c[1:] + c[:1])):
                    hitung["titik_berulang_berurutan"] += 1
    v = fitur.get("vertices", [])
    hitung["vertex_tidak_dipakai"] += sum(1 for i in range(len(v)) if i not in pakai)
    hitung["vertex_kembar_dalam_fitur"] += len(v) - len({tuple(x) for x in v})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("berkas", type=Path)
    ap.add_argument("--contoh", type=int, default=5, help="jumlah jenis galat yang ditampilkan")
    a = ap.parse_args(argv)

    kepala, fitur = muat_skema("cityjson.min.schema.json"), muat_skema("cityjsonfeature.min.schema.json")
    galat: collections.Counter = collections.Counter()
    contoh: dict = {}
    peringatan: collections.Counter = collections.Counter()
    n_fitur = 0
    with open(a.berkas, encoding="utf-8") as f:
        for no, baris in enumerate(f, 1):
            obj = json.loads(baris)
            if no > 1:
                n_fitur += 1
                peringatan_fitur(obj, peringatan)
            for e in (kepala if no == 1 else fitur).iter_errors(obj):
                jalur = "/".join("*" if isinstance(p, int) else str(p) for p in list(e.absolute_path)[:6])
                kunci = (f"baris{'1' if no == 1 else '>1'}", e.validator, jalur, e.message[:140])
                galat[kunci] += 1
                contoh.setdefault(kunci, no)

    judul = json.loads((SKEMA / "cityjson.min.schema.json").read_text())["title"]
    print(f"{a.berkas.name}: 1 baris metadata + {n_fitur} fitur; skema {judul}")
    total = sum(galat.values())
    print(f"GALAT SKEMA: {total} ({len(galat)} jenis)")
    for kunci, n in galat.most_common(a.contoh):
        print(f"  {n}x {kunci[0]} {kunci[1]} @ {kunci[2]}: {kunci[3]} (contoh baris {contoh[kunci]})")
    print("PERINGATAN geometri:", dict(peringatan) if peringatan else "tidak ada")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
