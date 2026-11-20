#!/usr/bin/env python3
"""CityJSONSeq -> 3D Tiles lewat tyler (Docker). Dapat diulang; tidak memakai /tmp.

  data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/buat_tile.py --slug bontang_lestari

Masukan : processed/buildings/<slug>.city.jsonl           (dari ekspor.py)
Kerja   : processed/tyler_work/<slug>/                    (salinan masukan; tyler menulis indeks sqlite di sini; di-ignore git)
Keluaran: processed/3dtiles/<slug>/                       (dikosongkan dulu; lalu 04_build_master.py [--sync])
Asal-usul (perintah, image, status) dicatat di tileset.json -> asset.extras.spectra.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

DP = Path(__file__).resolve().parents[2]
IMAGE = "3dgi/tyler:latest"
ATRIBUT = "id:string,gml_id:string,nama:string,tinggi:float,jumlah_lantai:int,luas_tapak:float"
CONFIG = DP / "config" / "citygml_sources.yaml"
KELAS = "bangunan"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    a = ap.parse_args(argv)

    sumber = DP / "processed" / "buildings" / f"{a.slug}.city.jsonl"
    if not sumber.exists():
        raise SystemExit(f"Belum ada {sumber}; jalankan ekspor.py dulu.")
    kerja = DP / "processed" / "tyler_work" / a.slug
    keluar = DP / "processed" / "3dtiles" / a.slug
    for d in (kerja, keluar):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    shutil.copy2(sumber, kerja / sumber.name)

    warna = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["umum"]["warna_bangunan_tyler"]  # alasan #B1BAC2: lihat config
    cmd = ["tyler", "--object-type", "Building", "--object-attributes", ATRIBUT, "--color-building", warna,
           "--3dtiles-metadata-class", KELAS, "-o", "/out", "/in"]
    docker = ["docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{kerja}:/in", "-v", f"{keluar}:/out", IMAGE, *cmd]
    subprocess.run(docker, check=True)

    image_id = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], capture_output=True, text=True, check=True).stdout.strip()
    versi = subprocess.run(["docker", "run", "--rm", IMAGE, "tyler", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    p = keluar / "tileset.json"
    ts = json.loads(p.read_text())
    ts["asset"]["extras"] = {"spectra": {
        "sumber": f"PostGIS core.bangunan (registri UJI COBA) -> CityJSONSeq processed/buildings/{a.slug}.city.jsonl",
        "alat": versi, "image": f"{IMAGE} {image_id}", "perintah": " ".join(cmd), "status": "uji_coba", "crs_sumber": "EPSG:32650", "z_dasar": 0}}
    p.write_text(json.dumps(ts, separators=(",", ":")))
    n = len(list(keluar.rglob("*.glb")))
    print(f"Selesai: {n} berkas .glb di {keluar}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
