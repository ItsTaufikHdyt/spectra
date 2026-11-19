"""Geometri inti pembersihan bangunan LOD2 (ADR-002). Fungsi murni: tanpa berkas, tanpa basis data.

Input: poligon sebagai cincin luar (list titik (x, y, z), tanpa titik penutup) dan cincin dalam.

Ambang yang dipakai (semuanya konstanta di bawah, dapat diuji):
  TOL_Z          = 0,02 m   titik dianggap "di Z minimum" bila z <= zmin + 0,02 (dasar sumber 0,001 m atau 0,000 m).
  SUDUT_DATAR    = 5°       bidang dengan kemiringan <= 5° dari horizontal dianggap horizontal
                            (sama dengan ambang analisis atap pada inventaris CityGML).
  SUDUT_DINDING  = 75°      bidang miring lebih dari 75° dari horizontal dianggap dinding; antara 5° dan 75° = atap miring.
  PRESISI        = 4        desimal (0,1 mm) untuk membandingkan titik saat mencari salinan/duplikat.
Aturan klasifikasi (label sumber TIDAK dipercaya):
  - horizontal DAN semua titik di Z minimum            -> 'G' (lantai/GroundSurface)
  - horizontal di atas Z minimum, atau miring 5°–75°   -> 'R' (atap/RoofSurface; normal mengarah ke atas setelah diorientasi)
  - selebihnya (hampir vertikal, > 75°)                -> 'W' (dinding/WallSurface)
"""

from __future__ import annotations

import math

import shapely
from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

TOL_Z = 0.02
SUDUT_DATAR = 5.0
SUDUT_DINDING = 75.0
PRESISI = 4
COS_DATAR = math.cos(math.radians(SUDUT_DATAR))
COS_DINDING = math.cos(math.radians(SUDUT_DINDING))


def newell(ring) -> tuple[float, float, float]:
    """Vektor normal (tidak dinormalkan) cincin; panjangnya = 2 x luas bidang."""
    nx = ny = nz = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1, z1 = ring[i]
        x2, y2, z2 = ring[(i + 1) % n]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return nx, ny, nz


def rasio_vertikal(ring) -> float:
    """|nz| / |normal| (1 = horizontal, 0 = vertikal); 0 bila cincin merosot (luas nol)."""
    nx, ny, nz = newell(ring)
    mag = math.sqrt(nx * nx + ny * ny + nz * nz)
    return abs(nz) / mag if mag > 1e-12 else 0.0


def kanon(ring) -> tuple:
    """Bentuk kanonik cincin: dibulatkan, diputar agar titik terkecil di awal (urutan tetap, arah dipertahankan)."""
    r = [tuple(round(c, PRESISI) for c in p) for p in ring]
    i = min(range(len(r)), key=lambda k: r[k])
    return tuple(r[i:] + r[:i])


def kunci_simetris(ring) -> tuple:
    """Kunci yang sama untuk cincin dan kebalikannya."""
    return min(kanon(ring), kanon(ring[::-1]))


def buang_salinan(poligon: list) -> tuple[list, int, int]:
    """Buang salinan terbalik dan duplikat searah dalam satu bangunan.

    poligon: daftar objek dengan atribut .luar dan .dalam (cincin). Yang pertama dipertahankan.
    Mengembalikan (poligon_unik, jumlah_salinan_terbalik, jumlah_duplikat_searah).
    """
    terlihat: dict = {}
    unik, terbalik, searah = [], 0, 0
    for p in poligon:
        kunci = (kunci_simetris(p.luar), tuple(sorted(kunci_simetris(h) for h in p.dalam)))
        if kunci not in terlihat:
            terlihat[kunci] = kanon(p.luar)
            unik.append(p)
        elif kanon(p.luar) == terlihat[kunci]:
            searah += 1
        else:
            terbalik += 1
    return unik, terbalik, searah


def klasifikasi(ring, zmin: float) -> str:
    """'G' (lantai), 'R' (atap), atau 'W' (dinding). Lihat aturan di docstring modul."""
    r = rasio_vertikal(ring)
    if r >= COS_DATAR:  # horizontal
        return "G" if max(p[2] for p in ring) <= zmin + TOL_Z else "R"
    return "R" if r >= COS_DINDING else "W"


def orientasi_keluar(ring, jenis: str, pusat_xy: tuple[float, float]) -> list:
    """Putar arah cincin agar normalnya menghadap keluar: lantai ke bawah, atap ke atas, dinding menjauhi pusat."""
    nx, ny, nz = newell(ring)
    if jenis == "G":
        balik = nz > 0
    elif jenis == "R":
        balik = nz < 0
    else:
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        balik = (cx - pusat_xy[0]) * nx + (cy - pusat_xy[1]) * ny < 0
    return list(ring[::-1]) if balik else list(ring)


def normalkan_z(ring, zmin: float) -> list:
    """Kurangi Z dengan zmin; titik dalam toleransi dasar dipaku tepat ke 0."""
    keluar = []
    for x, y, z in ring:
        zz = z - zmin
        keluar.append((x, y, 0.0 if abs(zz) <= TOL_Z else round(zz, 4)))
    return keluar


def footprint(poligon_dasar: list) -> tuple[MultiPolygon | None, int]:
    """Union poligon dasar (xy) -> MultiPolygon valid, atau (None, n) bila tidak ada.

    poligon_dasar: objek dengan .luar dan .dalam. Mengembalikan (footprint, jumlah_poligon_asli_tidak_valid).
    Poligon tak valid diperbaiki dengan make_valid.
    """
    bagian, tidak_valid = [], 0
    for p in poligon_dasar:
        pg = Polygon([(x, y) for x, y, _ in p.luar], [[(x, y) for x, y, _ in h] for h in p.dalam])
        if not pg.is_valid:
            tidak_valid += 1
            pg = make_valid(pg)
        if not pg.is_empty:
            bagian.append(pg)
    if not bagian:
        return None, tidak_valid
    gabungan = unary_union(bagian)
    poli = [g for g in shapely.get_parts(gabungan) if isinstance(g, Polygon) and g.area > 1e-9]
    if not poli:
        return None, tidak_valid
    return MultiPolygon(poli), tidak_valid
