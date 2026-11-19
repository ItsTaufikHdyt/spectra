#!/usr/bin/env python3
"""Uji mandiri pipeline CityGML (tanpa basis data, tanpa jaringan).

Jalankan (dari root repo):  data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/test_citygml.py
Uji berbasis berkas sumber (raw/citygml/, read-only) dilewati bila berkasnya tidak ada.
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from citygml import geometri as g  # noqa: E402
from citygml.bangunan import bersihkan  # noqa: E402
from citygml.parser import BangunanMentah, Poligon, baca_header, epsg_dari_srs, iter_bangunan  # noqa: E402

DP = Path(__file__).resolve().parents[2]
UMUM = dict(slug="uji", sumber_file="x.gml", sumber_part=None, epsg_sumber=32650, epsg_dipakai=32650)


def kotak(z0=0.0, tinggi=5.0, lebar=10.0):
    """Kotak lebar x lebar x tinggi, setiap permukaan DUA kali (searah dan kebalikannya).
    Label lantai/atap sengaja TERTUKAR seperti pada data sumber."""
    L, z1 = lebar, z0 + tinggi
    lantai = [(0, 0, z0), (L, 0, z0), (L, L, z0), (0, L, z0)]
    atap = [(0, 0, z1), (L, 0, z1), (L, L, z1), (0, L, z1)]
    dinding = [
        [(0, 0, z0), (L, 0, z0), (L, 0, z1), (0, 0, z1)], [(L, 0, z0), (L, L, z0), (L, L, z1), (L, 0, z1)],
        [(L, L, z0), (0, L, z0), (0, L, z1), (L, L, z1)], [(0, L, z0), (0, 0, z0), (0, 0, z1), (0, L, z1)],
    ]
    pol = [Poligon(lantai, [], "RoofSurface", "lod2MultiSurface"), Poligon(atap, [], "GroundSurface", "lod2MultiSurface")]
    pol += [Poligon(d, [], "WallSurface", "lod2MultiSurface") for d in dinding]
    return pol + [Poligon(p.luar[::-1], [], p.label, p.lod) for p in pol]  # salinan terbalik


def mentah(poligon, atribut=None):
    return BangunanMentah("X-1", atribut or {}, poligon, 0)


def uji_pasangan_terbalik_dan_duplikat_searah():
    pol = kotak()
    unik, terbalik, searah = g.buang_salinan(pol)
    assert (len(pol), len(unik), terbalik, searah) == (12, 6, 6, 0), (len(unik), terbalik, searah)
    p0 = pol[0]  # titik awal berbeda tetap dikenali sebagai poligon yang sama (searah)
    putar = Poligon(p0.luar[1:] + p0.luar[:1], [], p0.label, p0.lod)
    unik, terbalik, searah = g.buang_salinan(pol[:6] + [putar])
    assert (len(unik), terbalik, searah) == (6, 0, 1)
    q = Poligon([(x + 1e-6, y, z) for x, y, z in p0.luar[::-1]], [], p0.label, p0.lod)  # selisih < 0,1 mm = sama
    assert g.buang_salinan([p0, q])[1] == 1


def uji_klasifikasi_permukaan():
    zmin = 3.2
    lantai = [(0, 0, 3.201), (10, 0, 3.201), (10, 10, 3.201), (0, 10, 3.201)]
    atap_datar = [(0, 0, 8.2), (10, 0, 8.2), (10, 10, 8.2), (0, 10, 8.2)]
    atap_miring = [(0, 0, 8.2), (10, 0, 8.2), (10, 5, 10.9), (0, 5, 10.9)]
    dinding = [(0, 0, 3.2), (10, 0, 3.2), (10, 0, 8.2), (0, 0, 8.2)]
    hampir_tegak = [(0, 0, 3.2), (10, 0, 3.2), (10, 0.5, 8.2), (0, 0.5, 8.2)]
    assert g.klasifikasi(lantai, zmin) == "G"
    assert g.klasifikasi(atap_datar, zmin) == "R" and g.klasifikasi(atap_miring, zmin) == "R"
    assert g.klasifikasi(dinding, zmin) == "W" and g.klasifikasi(hampir_tegak, zmin) == "W"
    assert g.klasifikasi(lantai[::-1], zmin) == "G" and g.klasifikasi(atap_miring[::-1], zmin) == "R"  # arah tak berpengaruh


def uji_normalisasi_z():
    ring = [(0, 0, 3.201), (1, 0, 3.2), (1, 1, 8.2), (0, 1, 8.2)]
    r = g.normalkan_z(ring, 3.2)
    assert [p[2] for p in r] == [0.0, 0.0, 5.0, 5.0], r
    assert [(p[0], p[1]) for p in r] == [(p[0], p[1]) for p in ring]


def uji_footprint():
    p = Poligon([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)], [], None, None)
    fp, tak_valid = g.footprint([p, Poligon(p.luar[::-1], [], None, None)])
    assert fp.geom_type == "MultiPolygon" and abs(fp.area - 100) < 1e-9 and tak_valid == 0
    berlubang = Poligon(p.luar, [[(4, 4, 0), (6, 4, 0), (6, 6, 0), (4, 6, 0)]], None, None)
    assert abs(g.footprint([berlubang])[0].area - 96) < 1e-9
    dasi = Poligon([(0, 0, 0), (10, 10, 0), (10, 0, 0), (0, 10, 0)], [], None, None)
    fp, tak_valid = g.footprint([dasi])
    assert tak_valid == 1 and fp is not None and fp.is_valid
    assert g.footprint([]) == (None, 0)


def uji_bersihkan_kotak_berelevasi_absolut():
    b = bersihkan(mentah(kotak(z0=3.2), {"bldg:storeysAboveGround": ("2", None), "bldg:measuredHeight": ("5.00", "m")}),
                  slug="uji", sumber_file="x.gml", sumber_part="I", epsg_sumber=32748, epsg_dipakai=32650)
    assert b.stat["n_poligon_sumber"] == 12 and b.stat["n_poligon_bersih"] == 6 and b.stat["n_salinan_terbalik"] == 6
    assert b.stat["jenis"] == {"G": 1, "R": 1, "W": 4}, b.stat["jenis"]
    assert b.stat["n_label_sumber_beda"] == 2
    assert b.z_dasar_sumber == 3.2 and b.tinggi == 5.0 and b.luas_tapak == 100.0 and b.jumlah_lantai == 2
    assert min(t[2] for _, luar, _ in b.permukaan for t in luar) == 0.0
    assert {"z_dasar_tidak_nol_di_sumber", "epsg_dikoreksi"} <= set(b.qc_flag) and b.epsg_dikoreksi == 32650
    assert "tinggi_sumber_beda" not in b.qc_flag
    for jenis, luar, _ in b.permukaan:  # normal menghadap keluar
        nx, ny, nz = g.newell(luar)
        if jenis == "G":
            assert nz < 0
        elif jenis == "R":
            assert nz > 0
        else:
            cx, cy = sum(t[0] for t in luar) / 4, sum(t[1] for t in luar) / 4
            assert (cx - 5) * nx + (cy - 5) * ny > 0


def uji_bersihkan_atap_pelana_dan_flag():
    lantai = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
    atap1 = [(0, 0, 3), (10, 0, 3), (10, 5, 5.7), (0, 5, 5.7)]
    atap2 = [(0, 10, 3), (10, 10, 3), (10, 5, 5.7), (0, 5, 5.7)]
    dinding = [[(0, 0, 0), (10, 0, 0), (10, 0, 3), (0, 0, 3)], [(0, 10, 0), (10, 10, 0), (10, 10, 3), (0, 10, 3)],
               [(0, 0, 0), (0, 10, 0), (0, 10, 3), (0, 5, 5.7), (0, 0, 3)], [(10, 0, 0), (10, 10, 0), (10, 10, 3), (10, 5, 5.7), (10, 0, 3)]]
    pol = [Poligon(lantai, [], "GroundSurface", None), Poligon(atap1, [], "RoofSurface", None), Poligon(atap2, [], "RoofSurface", None)]
    pol += [Poligon(d, [], "WallSurface", None) for d in dinding]
    b = bersihkan(mentah(pol, {"bldg:measuredHeight": ("5.70", "m")}), **UMUM)
    assert b.stat["jenis"] == {"G": 1, "R": 2, "W": 4} and b.tinggi == 5.7 and b.qc_flag == [], (b.stat, b.qc_flag)
    kecil = bersihkan(mentah(kotak(tinggi=0.05, lebar=1.0)), **UMUM)
    assert {"tinggi_kurang_0_1m", "footprint_kurang_2m2"} <= set(kecil.qc_flag), kecil.qc_flag
    tanpa = bersihkan(mentah([Poligon(atap1, [], "RoofSurface", None)]), **UMUM)
    assert tanpa.footprint is None and "tanpa_footprint" in tanpa.qc_flag and tanpa.luas_tapak is None
    assert bersihkan(mentah([]), **UMUM).qc_flag == ["tanpa_geometri"]
    assert bersihkan(mentah(kotak()), **UMUM).jumlah_lantai is None  # tidak ditebak


def uji_epsg_dari_srs():
    assert epsg_dari_srs("http://www.opengis.net/def/crs/EPSG/0/32650") == 32650
    assert epsg_dari_srs("http://www.opengis.net/def/crs/EPSG/0/32748") == 32748 and epsg_dari_srs(None) is None


def uji_sampel_bontang_lestari_part_iii():
    path = DP / "raw" / "citygml" / "Kelurahan Bontang Lestari" / "Model 3D - Kelurahan Bontang Lestari - Part III.gml"
    if not path.exists():
        print("  (dilewati: berkas sampel tidak ada)")
        return
    h = baca_header(path)
    assert h.versi == "2.0" and epsg_dari_srs(h.srs_name) == 32650 and h.srs_dimensi == "3"
    semua = list(iter_bangunan(path))
    assert len(semua) == 5 and semua[0].gml_id == "BS_02092025-AAAA-00001-GeoAI01-05629B4"
    kw = dict(slug="bontang_lestari", sumber_file=path.name, sumber_part="III", epsg_sumber=32650, epsg_dipakai=32650)
    b = bersihkan(semua[0], **kw)
    assert b.stat["n_poligon_sumber"] == 12 and b.stat["n_poligon_bersih"] == 6, b.stat
    assert b.stat["jenis"] == {"G": 1, "R": 1, "W": 4}, b.stat["jenis"]
    assert abs(b.tinggi - 3.21) <= 0.005 and b.measured_height_sumber == 3.21 and b.jumlah_lantai == 1 and abs(b.luas_tapak - 65.8) < 0.1  # tinggi = Zmaks - Zmin (dasar sumber 0,001)
    assert b.z_dasar_sumber == 0.001 and b.qc_flag == [], b.qc_flag
    b4 = bersihkan(semua[3], **kw)
    assert b4.jumlah_lantai == 3 and abs(b4.tinggi - 19.44) < 0.01 and b4.stat["n_poligon_bersih"] < b4.stat["n_poligon_sumber"]
    assert [x.gml_id.split("-")[2] for x in semua] == ["00001", "00002", "00003", "00004", "00006"]  # nomor 00005 tidak ada


def uji_citygml_30_berebas_tengah():
    path = DP / "raw" / "citygml" / "Kelurahan Berebas Tengah" / "Model 3D - Kelurahan Berebas Tengah.gml"
    if not path.exists():
        print("  (dilewati: berkas sampel tidak ada)")
        return
    assert baca_header(path).versi == "3.0"
    pertama = next(iter_bangunan(path))
    assert pertama.gml_id == "BT_27052025-AAAA-00001-GeoAI01-6D7C802" and pertama.atribut == {}, pertama.atribut
    b = bersihkan(pertama, slug="berebas_tengah", sumber_file=path.name, sumber_part=None, epsg_sumber=32650, epsg_dipakai=32650)
    assert b.stat["n_salinan_terbalik"] > 0 and b.footprint is not None and b.jumlah_lantai is None and b.tinggi > 0


def main():
    gagal = 0
    for nama, fn in sorted((n, f) for n, f in globals().items() if n.startswith("uji_") and callable(f)):
        try:
            fn()
            print(f"LULUS  {nama}")
        except Exception:  # noqa: BLE001
            gagal += 1
            print(f"GAGAL  {nama}")
            traceback.print_exc()
    print("test_citygml:", "semua uji lulus" if not gagal else f"{gagal} uji gagal")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
