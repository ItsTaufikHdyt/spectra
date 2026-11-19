#!/usr/bin/env python3
"""Uji aturan pencocokan registri (ADR-003), data sintetis, tanpa basis data.

Jalankan (dari root repo):  data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/test_registri.py
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shapely.geometry import MultiPolygon, box  # noqa: E402

from citygml.registri import Baru, Lama, cocokkan  # noqa: E402


def fp(x0, y0, w=10.0, h=10.0):
    return MultiPolygon([box(x0, y0, x0 + w, y0 + h)])


def pusat(f):
    c = f.centroid
    return (c.x, c.y)


def lama(id_, gml, f):
    return Lama(id_, gml, pusat(f), f)


def baru(idx, gml, f, unik=True):
    return Baru(idx, gml, unik, pusat(f), f)


def uji_aturan_1_gml_id_dan_pergeseran_2m():
    a = fp(0, 0)
    assert cocokkan([baru(0, "G1", fp(1.5, 0))], [lama("BTG-BLD-000001", "G1", a)]) == ([(0, "BTG-BLD-000001", "gml_id")], [], [])
    # gml_id sama tetapi bergeser 3 m: aturan 1 gagal, aturan 2 gagal (jarak) -> ID baru
    assert cocokkan([baru(0, "G1", fp(3, 0))], [lama("BTG-BLD-000001", "G1", a)]) == ([], [], [0])


def uji_aturan_1_butuh_gml_id_unik_di_batch():
    a = fp(0, 0)
    # gml_id tidak unik di batch -> aturan 1 dilewati; footprint identik -> cocok lewat posisi (aturan 2)
    assert cocokkan([baru(0, "G1", a, unik=False)], [lama("BTG-BLD-000001", "G1", a)]) == ([(0, "BTG-BLD-000001", "posisi")], [], [])


def uji_aturan_2_posisi_dan_iou():
    a = fp(0, 0)
    assert cocokkan([baru(0, "BEDA", fp(0, 0))], [lama("BTG-BLD-000001", "G1", a)])[0] == [(0, "BTG-BLD-000001", "posisi")]
    assert cocokkan([baru(0, "X", fp(1, 0))], [lama("BTG-BLD-000001", "G1", a)])[0][0][2] == "posisi"  # IoU 9/11
    kecil = fp(2.5, 2.5, 5, 5)  # pusat sama, IoU 25/100 < 0,5 -> ID baru
    assert cocokkan([baru(0, "X", kecil)], [lama("BTG-BLD-000001", "G1", a)]) == ([], [], [0])
    assert cocokkan([baru(0, "X", fp(3, 0))], [lama("BTG-BLD-000001", "G1", a)])[2] == [0]  # pusat > 2 m


def uji_aturan_3_kandidat_ganda():
    b = fp(0, 0)
    l1, l2 = lama("BTG-BLD-000001", "A", fp(0, 0)), lama("BTG-BLD-000002", "B", fp(1, 0))  # IoU 1,0 vs 0,82: selisih >= 0,1
    assert cocokkan([baru(0, "X", b)], [l1, l2]) == ([(0, "BTG-BLD-000001", "posisi")], [], [])
    m1, m2 = lama("BTG-BLD-000001", "A", fp(0.4, 0)), lama("BTG-BLD-000002", "B", fp(-0.5, 0))  # selisih IoU < 0,1
    cocok, tinjauan, id_baru = cocokkan([baru(0, "X", b)], [m1, m2])
    assert cocok == [] and id_baru == [] and len(tinjauan) == 1
    assert {i for i, _ in tinjauan[0][1]} == {"BTG-BLD-000001", "BTG-BLD-000002"}


def uji_satu_id_lama_hanya_satu_bangunan_baru():
    a = fp(0, 0)
    cocok, tinjauan, id_baru = cocokkan([baru(0, "G1", a), baru(1, "G2", a)], [lama("BTG-BLD-000001", "G1", a)])
    assert cocok == [(0, "BTG-BLD-000001", "gml_id")] and id_baru == [1] and tinjauan == []


def bb(cx, cy, tinggi):
    """Bounding box 3D sintetis 10 x 10 m, dasar Z = 0."""
    return (cx - 5, cy - 5, 0.0, cx + 5, cy + 5, tinggi)


def lama_k(id_, gml, cx, cy, tinggi, f=None):
    return Lama(id_, gml, (cx, cy), f, bb(cx, cy, tinggi), tinggi)


def baru_k(idx, gml, cx, cy, tinggi, f=None, unik=True):
    return Baru(idx, gml, unik, (cx, cy), f, bb(cx, cy, tinggi), tinggi)


def uji_footprint_kosong_cocok_lewat_bbox_dan_tinggi():
    l = lama_k("BTG-BLD-000001", "G1", 100, 200, 5.0)
    # kedua footprint kosong; pusat 1 m, tinggi selisih 0,4 m -> cocok
    assert cocokkan([baru_k(0, "X", 101, 200, 5.4)], [l])[0] == [(0, "BTG-BLD-000001", "posisi")]
    # selisih tinggi 0,6 m -> tidak cocok
    assert cocokkan([baru_k(0, "X", 100, 200, 5.6)], [l])[2] == [0]
    # pusat bbox 3D > 2 m (3 m) -> tidak cocok
    assert cocokkan([baru_k(0, "X", 103, 200, 5.0)], [l])[2] == [0]


def uji_footprint_kosong_hanya_satu_sisi():
    # lama tanpa footprint, baru punya footprint (dan sebaliknya): aturan bbox tetap berlaku, bukan IoU
    l = lama_k("BTG-BLD-000001", "G1", 100, 200, 5.0)
    assert cocokkan([baru_k(0, "X", 100.5, 200, 5.2, fp(95.5, 195))], [l])[0] == [(0, "BTG-BLD-000001", "posisi")]
    l2 = lama_k("BTG-BLD-000002", "G2", 100, 200, 5.0, fp(95, 195))
    assert cocokkan([baru_k(0, "X", 100, 200.5, 5.3)], [l2])[0] == [(0, "BTG-BLD-000002", "posisi")]
    assert cocokkan([baru_k(0, "X", 100, 200, 6.0)], [l2])[2] == [0]  # tinggi beda 1 m


def uji_footprint_kosong_kandidat_ganda_masuk_tinjauan():
    l1, l2 = lama_k("BTG-BLD-000001", "A", 100, 200, 5.0), lama_k("BTG-BLD-000002", "B", 101, 200, 5.1)
    cocok, tinjauan, id_baru = cocokkan([baru_k(0, "X", 100.5, 200, 5.0)], [l1, l2])
    assert cocok == [] and id_baru == [] and len(tinjauan) == 1
    assert {i for i, _ in tinjauan[0][1]} == {"BTG-BLD-000001", "BTG-BLD-000002"}


def uji_footprint_kosong_tanpa_tinggi_atau_bbox_tidak_cocok():
    l = Lama("BTG-BLD-000001", "G1", (100.0, 200.0), None)  # tanpa bbox/tinggi: tidak bisa dinilai
    assert cocokkan([Baru(0, "Z", False, (100.0, 200.0), None)], [l])[2] == [0]


def uji_impor_ulang_tidak_menerbitkan_id_baru():
    fps = [fp(20 * i, 0) for i in range(30)]
    lamas = [lama(f"BTG-BLD-{i + 1:06d}", f"G{i}" if i % 5 else None, f) for i, f in enumerate(fps)]
    barus = [baru(i, f"G{i}" if i % 5 else None, f, unik=bool(i % 5)) for i, f in enumerate(fps)]
    cocok, tinjauan, id_baru = cocokkan(barus, lamas)
    assert len(cocok) == 30 and tinjauan == [] and id_baru == []
    assert {j for _, _, j in cocok} == {"gml_id", "posisi"}


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
    print("test_registri:", "semua uji lulus" if not gagal else f"{gagal} uji gagal")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
