"""Aturan pencocokan registri ID bangunan (ADR-003). Fungsi murni: tanpa basis data.

Untuk tiap bangunan hasil impor ("baru") dicari bangunan yang sudah punya ID ("lama"), berurutan:
  1. gml_id sama, kelurahan sama (dijamin pemanggil), gml_id UNIK di batch, dan pusat footprint bergeser <= 2 m;
  2. jika tidak: pusat footprint <= 2 m DAN IoU footprint >= 0,5;
  3. lebih dari satu kandidat (aturan 2): pilih IoU tertinggi; bila selisih dengan peringkat kedua < 0,1,
     bangunan masuk daftar tinjauan manual dan TIDAK diberi ID;
  4. tidak ada kecocokan: ID baru.
Footprint kosong di salah satu sisi (atau keduanya): IoU tidak bisa dihitung, maka aturan 2-3 diganti: dianggap sama bila jarak
pusat bounding box 3D <= 2 m dan selisih tinggi <= 0,5 m; lebih dari satu kandidat -> tinjauan manual tanpa ID (skor = jarak 3D, m).
Satu ID lama hanya boleh dipakai satu bangunan baru per batch. Urutan pemrosesan = urutan daftar (deterministik).
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from shapely.geometry import Point
from shapely.strtree import STRtree

JARAK_MAKS = 2.0     # m
IOU_MIN = 0.5
SELISIH_IOU_MIN = 0.1
SELISIH_TINGGI_MAKS = 0.5  # m, hanya untuk footprint kosong


@dataclass
class Baru:
    idx: int
    gml_id: str | None
    gml_unik: bool            # gml_id unik di dalam batch
    pusat: tuple[float, float]
    footprint: object = None  # shapely (Multi)Polygon atau None
    bbox: tuple | None = None  # (xmin, ymin, zmin, xmax, ymax, zmax)
    tinggi: float | None = None


@dataclass
class Lama:
    id: str
    gml_id: str | None
    pusat: tuple[float, float]
    footprint: object = None
    bbox: tuple | None = None
    tinggi: float | None = None


def kosong(f) -> bool:
    return f is None or f.is_empty


def pusat_bbox(bb) -> tuple[float, float, float]:
    return ((bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2)


def jarak_bbox(a, b) -> float | None:
    """Jarak 3D antar pusat bounding box; None bila salah satu bbox tidak ada."""
    if a.bbox is None or b.bbox is None:
        return None
    return math.dist(pusat_bbox(a.bbox), pusat_bbox(b.bbox))


def jarak(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def iou(a, b) -> float:
    """IoU footprint; salah satu kosong -> 0 (kasus footprint kosong ditangani aturan bbox di cocokkan)."""
    if kosong(a) or kosong(b):
        return 0.0
    inter = a.intersection(b).area
    gabung = a.area + b.area - inter
    return inter / gabung if gabung > 0 else 0.0


def cocokkan(baru: list[Baru], lama: list[Lama]):
    """Kembalikan (cocok, tinjauan, id_baru):
       cocok    = [(idx_baru, id_lama, 'gml_id' | 'posisi')],
       tinjauan = [(idx_baru, [(id_lama, iou), ...])]  (kandidat berurutan menurun),
       id_baru  = [idx_baru, ...] (perlu ID baru, urutan input)."""
    dipakai: set[str] = set()
    cocok: dict[int, tuple[str, str]] = {}

    # --- Aturan 1: gml_id ---
    per_gml: dict[str, list[Lama]] = defaultdict(list)
    for l in lama:
        if l.gml_id:
            per_gml[l.gml_id].append(l)
    for b in baru:
        if not (b.gml_id and b.gml_unik):
            continue
        kand = [l for l in per_gml.get(b.gml_id, []) if l.id not in dipakai and jarak(b.pusat, l.pusat) <= JARAK_MAKS]
        if len(kand) == 1:
            cocok[b.idx] = (kand[0].id, "gml_id")
            dipakai.add(kand[0].id)

    # --- Aturan 2 dan 3: posisi + IoU ---
    pohon = STRtree([Point(l.pusat) for l in lama]) if lama else None
    idx_bbox = [k for k, l in enumerate(lama) if l.bbox is not None]
    pohon_bbox = STRtree([Point(pusat_bbox(lama[k].bbox)[:2]) for k in idx_bbox]) if idx_bbox else None
    tinjauan, id_baru = [], []
    for b in baru:
        if b.idx in cocok:
            continue
        # kandidat: indeks lama dekat (pusat footprint) atau dekat (pusat bbox, untuk kasus footprint kosong)
        dekat = set()
        if pohon is not None:
            dekat |= {int(i) for i in pohon.query(Point(b.pusat).buffer(JARAK_MAKS))}
        if pohon_bbox is not None and b.bbox is not None:
            dekat |= {idx_bbox[int(i)] for i in pohon_bbox.query(Point(pusat_bbox(b.bbox)[:2]).buffer(JARAK_MAKS))}
        kand_iou: list[tuple[float, str]] = []   # (IoU, id)
        kand_bbox: list[tuple[float, str]] = []  # (jarak 3D, id)
        for k in sorted(dekat):
            l = lama[k]
            if l.id in dipakai:
                continue
            if kosong(b.footprint) or kosong(l.footprint):
                d = jarak_bbox(b, l)
                if d is not None and d <= JARAK_MAKS and b.tinggi is not None and l.tinggi is not None \
                        and abs(b.tinggi - l.tinggi) <= SELISIH_TINGGI_MAKS:
                    kand_bbox.append((d, l.id))
            elif jarak(b.pusat, l.pusat) <= JARAK_MAKS:
                nilai = iou(b.footprint, l.footprint)
                if nilai >= IOU_MIN:
                    kand_iou.append((nilai, l.id))
        kand_iou.sort(key=lambda t: (-t[0], t[1]))
        kand_bbox.sort(key=lambda t: (t[0], t[1]))
        if not kand_iou and not kand_bbox:
            id_baru.append(b.idx)  # --- Aturan 4 ---
        elif kand_bbox:  # footprint kosong: satu kandidat total -> cocok; lebih -> tinjauan manual
            if len(kand_bbox) + len(kand_iou) > 1:
                tinjauan.append((b.idx, [(i, n) for n, i in kand_bbox] + [(i, n) for n, i in kand_iou]))
            else:
                cocok[b.idx] = (kand_bbox[0][1], "posisi")
                dipakai.add(kand_bbox[0][1])
        elif len(kand_iou) > 1 and kand_iou[0][0] - kand_iou[1][0] < SELISIH_IOU_MIN:
            tinjauan.append((b.idx, [(i, n) for n, i in kand_iou]))  # --- Aturan 3: tanpa ID ---
        else:
            cocok[b.idx] = (kand_iou[0][1], "posisi")
            dipakai.add(kand_iou[0][1])
    return [(i, v[0], v[1]) for i, v in sorted(cocok.items())], tinjauan, id_baru
