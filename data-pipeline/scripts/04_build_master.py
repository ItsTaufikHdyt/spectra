#!/usr/bin/env python3
"""
04_build_master.py — Bangun master-tileset.json untuk 15 kelurahan Kota Bontang.

Membaca setiap subfolder di data-pipeline/processed/3dtiles/<kelurahan>/tileset.json
(hasil pipeline CityGML -> PostGIS -> tyler; lihat scripts/citygml/buat_tile.py), memvalidasi (bounding region + keberadaan file konten .glb), lalu menulis satu
master-tileset.json hierarkis. Setiap kelurahan menjadi tile anak yang mereferensikan
tileset.json kelurahan sebagai *external tileset* (content.uri relatif).

Hanya library standar Python (>= 3.8). Contoh pemakaian:

    # Bangun master saja
    python3 data-pipeline/scripts/04_build_master.py

    # Bangun master + salin/sinkronkan ke frontend/public/tiles/
    python3 data-pipeline/scripts/04_build_master.py --sync

    # --sync tidak menyalin tileset_unpruned.json (file perantara tyler, tidak dipakai saat runtime).

Catatan teknis:
  * Semua tileset kelurahan memakai boundingVolume.region (radian: W, S, E, N, minH, maxH).
    Region master = gabungan (union) seluruh region kelurahan. Tipe box/sphere belum
    didukung karena butuh transform; skrip berhenti dengan pesan jelas.
  * Asumsi region tidak melintasi antimeridian (west <= east) — benar untuk Bontang.
  * geometricError root master sengaja besar (default 4x error terbesar kelurahan).
    Root master tidak punya konten; Cesium hanya menelusuri anaknya bila SSE root
    melebihi batas. Error kecil membuat seluruh kota "hilang" saat kamera menjauh.
  * Root tileset ke-15 kelurahan TIDAK punya konten (refine REPLACE); Cesium baru memuat anaknya
    bila SSE root > maximumScreenSpaceError, jadi dari jauh bangunan tidak dirender. Frontend
    menampilkan kotak ikhtisar per kelurahan (use3DTiles.js: buildKelurahanOverview). Perbaikan
    permanen (direncanakan) ada di tahap tyler, bukan di skrip ini: mesh kasar per kelurahan sebagai
    root.content (< 1-2 MB), lalu jalankan ulang skrip ini (+ --sync).
  * Tile yang kontennya tileset eksternal SELALU ditelusuri Cesium, jadi refine pada
    root master ("ADD") tidak mengubah tampilan (root tanpa konten); disediakan
    sesuai spesifikasi dan dapat diganti lewat --refine.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SRC = REPO_ROOT / "data-pipeline" / "processed" / "3dtiles"
DEFAULT_DEST = REPO_ROOT / "frontend" / "public" / "tiles"
MASTER_NAME = "master-tileset.json"
# File perantara tyler yang tidak dipakai saat runtime — tidak ikut disalin.
SKIP_ON_SYNC = {"tileset_unpruned.json"}
LARGE_TILE_BYTES = 3 * 1024 * 1024  # peringatan jika satu .glb > 3 MB


class BuildError(Exception):
    """Kesalahan data yang membuat master tidak bisa dibangun dengan benar."""


# --------------------------------------------------------------------------- #
# Pembacaan & validasi tileset kelurahan
# --------------------------------------------------------------------------- #
def iter_tiles(root: dict):
    """Telusuri seluruh tile (iteratif, aman untuk pohon dalam)."""
    stack = [root]
    while stack:
        tile = stack.pop()
        yield tile
        stack.extend(tile.get("children", []))


def tile_content_uris(tile: dict) -> list[str]:
    """Kumpulkan URI konten dari format 1.1 (content/contents) dan 1.0 (url)."""
    uris = []
    contents = list(tile.get("contents", []))
    if "content" in tile:
        contents.append(tile["content"])
    for c in contents:
        uri = c.get("uri") or c.get("url")
        if uri:
            uris.append(uri)
    return uris


def inspect_kelurahan(folder: Path) -> dict:
    """Validasi satu folder kelurahan dan kembalikan ringkasannya."""
    slug = folder.name
    tileset_path = folder / "tileset.json"
    if not tileset_path.is_file():
        raise BuildError(f"[{slug}] tileset.json tidak ditemukan")

    with tileset_path.open(encoding="utf-8") as f:
        tileset = json.load(f)

    root = tileset.get("root")
    if not root:
        raise BuildError(f"[{slug}] tileset.json tidak punya 'root'")

    bv = root.get("boundingVolume", {})
    region = bv.get("region")
    if not region or len(region) != 6:
        kinds = ", ".join(bv.keys()) or "tidak ada"
        raise BuildError(
            f"[{slug}] root.boundingVolume harus 'region' (6 angka); ditemukan: {kinds}"
        )
    west, south, east, north, min_h, max_h = region
    if not (west <= east and south <= north and min_h <= max_h):
        raise BuildError(f"[{slug}] region tidak valid (urutan min/max salah): {region}")

    tiles = contents = total_bytes = 0
    missing: list[str] = []
    large: list[tuple[str, int]] = []
    for tile in iter_tiles(root):
        tiles += 1
        for uri in tile_content_uris(tile):
            contents += 1
            target = folder / uri
            if not target.is_file():
                missing.append(uri)
                continue
            size = target.stat().st_size
            total_bytes += size
            if size > LARGE_TILE_BYTES:
                large.append((uri, size))

    if missing:
        sample = ", ".join(missing[:3]) + (" ..." if len(missing) > 3 else "")
        raise BuildError(f"[{slug}] {len(missing)} file konten hilang: {sample}")

    return {
        "slug": slug,
        "folder": folder,
        "name": slug.replace("_", " ").title(),
        "region": [float(v) for v in region],
        "geometricError": float(tileset.get("geometricError", root.get("geometricError", 0))),
        "extensionsUsed": tileset.get("extensionsUsed", []),
        "extensionsRequired": tileset.get("extensionsRequired", []),
        "extensions": tileset.get("extensions", {}),
        "tiles": tiles,
        "contents": contents,
        "bytes": total_bytes,
        "large": large,
    }


# --------------------------------------------------------------------------- #
# Penyusunan master
# --------------------------------------------------------------------------- #
def union_region(regions: list[list[float]]) -> list[float]:
    """Gabungan region: [min W, min S, max E, max N, min H, max H]."""
    return [
        min(r[0] for r in regions),
        min(r[1] for r in regions),
        max(r[2] for r in regions),
        max(r[3] for r in regions),
        min(r[4] for r in regions),
        max(r[5] for r in regions),
    ]


def ordered_union(lists: list[list[str]]) -> list[str]:
    seen: dict[str, None] = {}
    for items in lists:
        for item in items:
            seen.setdefault(item, None)
    return list(seen)


def build_master(entries: list[dict], refine: str, root_error: float | None) -> dict:
    master_region = union_region([e["region"] for e in entries])
    max_child_error = max(e["geometricError"] for e in entries)
    error = root_error if root_error is not None else max_child_error * 4

    master: dict = {"asset": {"version": "1.1"}, "geometricError": error}

    # Cesium membaca extensionsUsed/extensions dari tileset utama (master),
    # jadi deklarasi child ditiru agar konten glTF diperlakukan sama.
    used = ordered_union([e["extensionsUsed"] for e in entries])
    required = ordered_union([e["extensionsRequired"] for e in entries])
    extensions: dict = {}
    for e in entries:
        for key, value in e["extensions"].items():
            extensions.setdefault(key, value)
    if used:
        master["extensionsUsed"] = used
    if required:
        master["extensionsRequired"] = required
    if extensions:
        master["extensions"] = extensions

    master["root"] = {
        "boundingVolume": {"region": master_region},
        "geometricError": error,
        "refine": refine,
        "children": [
            {
                "boundingVolume": {"region": e["region"]},
                "geometricError": e["geometricError"],
                "content": {"uri": f"{e['slug']}/tileset.json"},
            }
            for e in entries
        ],
    }
    master["extras"] = {
        "generator": "data-pipeline/scripts/04_build_master.py",
        "kelurahanCount": len(entries),
        "kelurahan": [e["slug"] for e in entries],
    }
    return master


# --------------------------------------------------------------------------- #
# Sinkronisasi ke frontend/public/tiles
# --------------------------------------------------------------------------- #
def _needs_copy(src: Path, dst: Path) -> bool:
    if not dst.is_file():
        return True
    s, d = src.stat(), dst.stat()
    return s.st_size != d.st_size or int(s.st_mtime) != int(d.st_mtime)


def sync_folder(src_dir: Path, dst_dir: Path) -> tuple[int, int]:
    """Salin hanya file yang berubah, hapus file basi di dst. Return (disalin, dihapus)."""
    copied = removed = 0
    wanted: set[Path] = set()
    for dirpath, _dirs, files in os.walk(src_dir):
        for name in files:
            if name in SKIP_ON_SYNC:
                continue
            src = Path(dirpath) / name
            rel = src.relative_to(src_dir)
            dst = dst_dir / rel
            wanted.add(rel)
            if _needs_copy(src, dst):
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)  # copy2 menjaga mtime -> sync inkremental
                copied += 1
    if dst_dir.is_dir():
        for dirpath, _dirs, files in os.walk(dst_dir, topdown=False):
            for name in files:
                path = Path(dirpath) / name
                if path.relative_to(dst_dir) not in wanted:
                    path.unlink()
                    removed += 1
            try:
                Path(dirpath).rmdir()  # hapus folder kosong; gagal diam bila masih berisi
            except OSError:
                pass
    return copied, removed


def sync_to_frontend(master_file: Path, dest: Path, entries: list[dict]) -> None:
    """Hanya menyentuh folder kelurahan yang dikenal + master; file lain di dest dibiarkan."""
    dest.mkdir(parents=True, exist_ok=True)
    total_copied = total_removed = 0
    for e in entries:
        copied, removed = sync_folder(e["folder"], dest / e["slug"])
        total_copied += copied
        total_removed += removed
    shutil.copy2(master_file, dest / MASTER_NAME)
    print(
        f"\nSync -> {dest}\n"
        f"  file disalin: {total_copied}, file basi dihapus: {total_removed}, "
        f"{MASTER_NAME} diperbarui"
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def mb(n: int) -> str:
    return f"{n / 1024 / 1024:7.1f} MB"


def main() -> int:
    ap = argparse.ArgumentParser(description="Bangun master-tileset.json 15 kelurahan Bontang.")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC, help=f"folder 3dtiles (default: {DEFAULT_SRC})")
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST, help=f"tujuan sync (default: {DEFAULT_DEST})")
    ap.add_argument("--sync", action="store_true", help="salin hasil ke --dest (frontend/public/tiles)")
    ap.add_argument("--refine", choices=["ADD", "REPLACE"], default="ADD", help="refine root master (default: ADD)")
    ap.add_argument("--root-error", type=float, default=None, help="geometricError root master (default: 4x error terbesar)")
    args = ap.parse_args()

    src: Path = args.src.resolve()
    if not src.is_dir():
        print(f"ERROR: folder sumber tidak ada: {src}", file=sys.stderr)
        return 1

    folders = sorted(p for p in src.iterdir() if p.is_dir() and (p / "tileset.json").is_file())
    if not folders:
        print(f"ERROR: tidak ada subfolder ber-tileset.json di {src}", file=sys.stderr)
        return 1

    try:
        entries = [inspect_kelurahan(f) for f in folders]
        master = build_master(entries, args.refine, args.root_error)
    except BuildError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1

    out = src / MASTER_NAME
    out.write_text(json.dumps(master, indent=2) + "\n", encoding="utf-8")

    print(f"{'kelurahan':<20}{'tile':>6}{'konten':>8}{'ukuran':>12}   geometricError")
    for e in entries:
        print(f"{e['slug']:<20}{e['tiles']:>6}{e['contents']:>8}{mb(e['bytes']):>12}   {e['geometricError']:g}")
    total = sum(e["bytes"] for e in entries)
    print(f"{'TOTAL':<20}{sum(e['tiles'] for e in entries):>6}{sum(e['contents'] for e in entries):>8}{mb(total):>12}")

    for e in entries:
        for uri, size in e["large"]:
            print(f"PERINGATAN: {e['slug']}/{uri} berukuran {mb(size).strip()} (> 3 MB)")

    deg = 180 / 3.141592653589793
    r = master["root"]["boundingVolume"]["region"]
    print(
        f"\nRegion master (derajat): lon {r[0]*deg:.5f}..{r[2]*deg:.5f}, "
        f"lat {r[1]*deg:.5f}..{r[3]*deg:.5f}, tinggi {r[4]:.1f}..{r[5]:.1f} m"
    )
    print(f"geometricError root master: {master['geometricError']:g}  |  refine root: {args.refine}")
    print(f"Ditulis: {out}")

    if args.sync:
        sync_to_frontend(out, args.dest.resolve(), entries)
    else:
        print("\nUntuk menyalin ke frontend: tambahkan --sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
