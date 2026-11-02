#!/usr/bin/env python3
"""
sync_geojson.py — Salin GeoJSON hasil ETL ke frontend/public/geojson/ untuk dev.

Sumber kebenaran tetap data-pipeline/processed/geojson/ (hasil normalize_names.py dan
reproject_sungai.py); frontend/public/geojson/ hanya salinan dan di-ignore git — pola sama
dengan 04_build_master.py --sync untuk 3D Tiles. Hanya library standar.

Jalankan ulang setiap kali output GeoJSON berubah:
    python3 data-pipeline/scripts/sync_geojson.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

DP = Path(__file__).resolve().parents[1]
SRC = DP / "processed" / "geojson"
DEST = DP.parent / "frontend" / "public" / "geojson"

# Hanya file yang dipakai frontend (composables/useVectorLayers.js).
FILES = (
    "batas-kelurahan.norm.geojson",
    "batas-rt.norm.geojson",
    "sungai_ln.wgs84.geojson",
)


def needs_copy(src: Path, dst: Path) -> bool:
    if not dst.is_file():
        return True
    s, d = src.stat(), dst.stat()
    return s.st_size != d.st_size or int(s.st_mtime) != int(d.st_mtime)


def main() -> int:
    missing = [name for name in FILES if not (SRC / name).is_file()]
    if missing:
        print(
            f"ERROR: belum ada di {SRC}: {', '.join(missing)}\n"
            "Jalankan normalize_names.py dan reproject_sungai.py terlebih dahulu.",
            file=sys.stderr,
        )
        return 1
    DEST.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in FILES:
        if needs_copy(SRC / name, DEST / name):
            shutil.copy2(SRC / name, DEST / name)  # copy2 menjaga mtime -> sync inkremental
            copied += 1
    print(f"Sync -> {DEST}: {copied} file disalin, {len(FILES) - copied} sudah terbaru")
    return 0


if __name__ == "__main__":
    sys.exit(main())
