#!/usr/bin/env python3
"""Muat CityGML satu kelurahan ke PostGIS dan terbitkan ID (ADR-003/004). UJI COBA, bukan impor resmi.

  data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/muat.py --slug bontang_lestari

Alur: baca berkas aktif di config/citygml_sources.yaml (read-only, streaming) -> bersihkan tiap bangunan (geometri.py)
-> cocokkan dengan registri (registri.py) -> terbitkan ID baru berurutan deterministik -> tulis staging.import_batch,
core.registri_id, core.bangunan dalam SATU transaksi. Menjalankan ulang impor yang sama tidak boleh menerbitkan ID baru.

Batch bertipe 'uji_coba': ID berstatus 'uji_coba', basis data pengembangan boleh di-reset (db.sh reset --ya),
dan registri TIDAK diekspor ke config/ sebagai registri resmi.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import statistics
import sys
import time
from pathlib import Path

import yaml
from shapely import wkb

DP = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DP / "scripts"))
sys.path.insert(0, str(DP / "db"))

from citygml.bangunan import bersihkan, nomor_deskripsi  # noqa: E402
from citygml.parser import baca_header, epsg_dari_srs, iter_bangunan  # noqa: E402
from citygml.registri import Baru, Lama, cocokkan  # noqa: E402
from koneksi import buka_koneksi  # noqa: E402

CONFIG = DP / "config" / "citygml_sources.yaml"
LAPORAN = DP / "reports"
EPSG = 32650


def baca_sumber(slug: str) -> list[dict]:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    sumber = [s for s in cfg["sumber"] if s["slug"] == slug and s.get("aktif")]
    if not sumber:
        raise SystemExit(f"Tidak ada sumber aktif untuk slug {slug!r} di {CONFIG.name}")
    for s in sumber:
        if s["epsg_dipakai"] != s["epsg_tercantum"] and not s.get("alasan_koreksi"):
            raise SystemExit(f"{s['path']}: koreksi EPSG tanpa alasan_koreksi")
    return sumber


def baca_dan_bersihkan(sumber: list[dict]):
    """Hasilkan (bangunan_bersih, desk_nomor, statistik_per_berkas). Berkas dibaca streaming dan read-only."""
    hasil, nomor, per_berkas = [], [], []
    for s in sumber:
        path = DP / s["path"]
        h = baca_header(path)
        if h.versi != s["versi_citygml"] or epsg_dari_srs(h.srs_name) != s["epsg_tercantum"]:
            raise SystemExit(f"{path.name}: header (versi {h.versi}, EPSG {epsg_dari_srs(h.srs_name)}) tidak sama dengan konfigurasi")
        n0 = len(hasil)
        for m in iter_bangunan(path):
            hasil.append(bersihkan(m, slug=s["slug"], sumber_file=path.name, sumber_part=s.get("part"),
                                   epsg_sumber=s["epsg_tercantum"], epsg_dipakai=s["epsg_dipakai"]))
            nomor.append(nomor_deskripsi(m))
        per_berkas.append({"berkas": path.name, "part": s.get("part"), "versi": h.versi, "bangunan": len(hasil) - n0})
        print(f"  dibaca {path.name}: {len(hasil) - n0} bangunan", flush=True)
    # gml_id bentrok di dalam batch (kelurahan yang sama)
    hitung = collections.Counter(b.gml_id for b in hasil if b.gml_id)
    for b in hasil:
        if b.gml_id and hitung[b.gml_id] > 1:
            b.qc_flag.append("gml_id_bentrok")
    return hasil, nomor, per_berkas


def pusat_dari(b) -> tuple[float, float]:
    """Pusat footprint (centroid); bila tanpa footprint, pusat bounding box geometri (dicatat lewat qc_flag tanpa_footprint)."""
    if b.footprint is not None:
        c = b.footprint.centroid
        return (round(c.x, 3), round(c.y, 3))
    xs = [t[0] for _, luar, _ in b.permukaan for t in luar] or [0.0]
    ys = [t[1] for _, luar, _ in b.permukaan for t in luar] or [0.0]
    return (round((min(xs) + max(xs)) / 2, 3), round((min(ys) + max(ys)) / 2, 3))


def bbox_dari(b):
    """Bounding box 3D (xmin, ymin, zmin, xmax, ymax, zmax) dari permukaan bersih; None bila tanpa permukaan."""
    t = [p for _, luar, _ in b.permukaan for p in luar]
    if not t:
        return None
    return (min(p[0] for p in t), min(p[1] for p in t), min(p[2] for p in t), max(p[0] for p in t), max(p[1] for p in t), max(p[2] for p in t))


def ewkt_permukaan(b) -> str | None:
    """POLYHEDRALSURFACE Z dari permukaan bersih (Z dasar = 0); None bila tanpa permukaan."""
    if not b.permukaan:
        return None
    def cincin(r):
        r = list(r) + [r[0]]
        return "(" + ", ".join(f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in r) + ")"
    patch = ["(" + ", ".join([cincin(luar)] + [cincin(h) for h in dalam]) + ")" for _, luar, dalam in b.permukaan]
    return f"SRID={EPSG};POLYHEDRALSURFACE Z (" + ", ".join(patch) + ")"


def nilai_baris(b, batch_id: int, id_: str):
    return (
        id_, b.gml_id, b.slug, b.sumber_file, b.sumber_part,
        b.footprint.wkb if b.footprint is not None else None, ewkt_permukaan(b), b.jenis_permukaan,
        b.tinggi, b.jumlah_lantai, b.luas_tapak, b.z_dasar_sumber, b.epsg_sumber, b.epsg_dikoreksi,
        b.measured_height_sumber, sorted(b.qc_flag), batch_id,
    )


SQL_INSERT = """INSERT INTO core.bangunan (id, gml_id, slug, sumber_file, sumber_part, footprint, geometri_lod2, jenis_permukaan,
    tinggi, jumlah_lantai, luas_tapak, z_dasar_sumber, epsg_sumber, epsg_dikoreksi, measured_height_sumber, qc_flag, batch_id)
    VALUES (%s, %s, %s, %s, %s, ST_GeomFromWKB(%s, 32650), ST_GeomFromEWKT(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
SQL_UPDATE = """UPDATE core.bangunan SET gml_id=%s, sumber_file=%s, sumber_part=%s, footprint=ST_GeomFromWKB(%s, 32650),
    geometri_lod2=ST_GeomFromEWKT(%s), jenis_permukaan=%s, tinggi=%s, jumlah_lantai=%s, luas_tapak=%s, z_dasar_sumber=%s,
    epsg_sumber=%s, epsg_dikoreksi=%s, measured_height_sumber=%s, qc_flag=%s, batch_id=%s WHERE id=%s"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--jenis", choices=["uji_coba"], default="uji_coba", help="hanya uji_coba pada tahap ini (impor resmi belum dibuka)")
    ap.add_argument("--catatan", default="")
    a = ap.parse_args(argv)

    t0 = time.time()
    print(f"Membaca sumber {a.slug} ...", flush=True)
    sumber = baca_sumber(a.slug)
    bangunan, nomor_desk, per_berkas = baca_dan_bersihkan(sumber)
    print(f"Total {len(bangunan)} bangunan dibaca dan dibersihkan ({time.time() - t0:.0f} s).", flush=True)

    pusat = [pusat_dari(b) for b in bangunan]
    gml_hitung = collections.Counter(b.gml_id for b in bangunan if b.gml_id)
    baru = [Baru(i, b.gml_id, bool(b.gml_id) and gml_hitung[b.gml_id] == 1, pusat[i], b.footprint, bbox_dari(b), b.tinggi)
            for i, b in enumerate(bangunan)]

    with buka_koneksi() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO staging.import_batch (jenis, sumber, catatan) VALUES (%s, %s, %s) RETURNING id",
                        (a.jenis, f"raw/citygml ({a.slug}, {len(sumber)} berkas)", a.catatan or None))
            batch_id = cur.fetchone()[0]

            cur.execute(
                "SELECT r.id, r.gml_id, ST_X(r.pusat_footprint), ST_Y(r.pusat_footprint), ST_AsBinary(b.footprint), "
                "ST_XMin(b.geometri_lod2), ST_YMin(b.geometri_lod2), ST_ZMin(b.geometri_lod2), "
                "ST_XMax(b.geometri_lod2), ST_YMax(b.geometri_lod2), ST_ZMax(b.geometri_lod2), b.tinggi "
                "FROM core.registri_id r JOIN core.bangunan b ON b.id = r.id WHERE r.slug = %s AND r.status IN ('aktif', 'uji_coba')",
                (a.slug,))
            lama = [Lama(r[0], r[1], (r[2], r[3]), wkb.loads(bytes(r[4])) if r[4] is not None else None,
                         tuple(float(v) for v in r[5:11]) if r[5] is not None else None, float(r[11]) if r[11] is not None else None)
                    for r in cur.fetchall()]

            cocok, tinjauan, id_baru = cocokkan(baru, lama)
            per_jenis = collections.Counter(j for _, _, j in cocok)

            # --- ID baru: urutan deterministik (slug, gml_id, koordinat pusat) ---
            urut = sorted(id_baru, key=lambda i: (bangunan[i].gml_id is None, bangunan[i].gml_id or "", pusat[i][0], pusat[i][1]))
            id_untuk: dict[int, str] = {}
            for i in urut:
                cur.execute("INSERT INTO core.registri_id (gml_id, slug, pusat_footprint, batch_id, status) "
                            "VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 32650), %s, 'uji_coba') RETURNING id",
                            (bangunan[i].gml_id, a.slug, pusat[i][0], pusat[i][1], batch_id))
                id_untuk[i] = cur.fetchone()[0]
            for i in urut:
                cur.execute(SQL_INSERT, nilai_baris(bangunan[i], batch_id, id_untuk[i]))

            # --- Bangunan yang cocok: perbarui bila berubah ---
            berubah = tidak_berubah = 0
            for i, id_lama, _ in cocok:
                b = bangunan[i]
                cur.execute("SELECT gml_id, sumber_file, sumber_part, encode(ST_AsBinary(footprint), 'hex'), "
                            "ST_AsEWKT(geometri_lod2), jenis_permukaan, tinggi, jumlah_lantai, luas_tapak, qc_flag FROM core.bangunan WHERE id=%s",
                            (id_lama,))
                r = cur.fetchone()
                # Perbandingan skalar + footprint; geometri LOD2 dianggap sama bila urutan jenis permukaan dan tinggi sama
                # (cukup untuk menilai idempotensi pada uji coba).
                sama = (
                    r[0] == b.gml_id and r[1] == b.sumber_file and r[2] == b.sumber_part
                    and (r[3] or "").upper() == (b.footprint.wkb_hex if b.footprint is not None else "").upper()
                    and list(r[5]) == b.jenis_permukaan and (float(r[6]) if r[6] is not None else None) == (float(b.tinggi) if b.tinggi is not None else None)
                    and r[7] == b.jumlah_lantai and (float(r[8]) if r[8] is not None else None) == (float(b.luas_tapak) if b.luas_tapak is not None else None)
                    and sorted(r[9]) == sorted(b.qc_flag)
                )
                if sama:
                    tidak_berubah += 1
                    continue
                cur.execute(SQL_UPDATE, (b.gml_id, b.sumber_file, b.sumber_part, b.footprint.wkb if b.footprint is not None else None,
                                         ewkt_permukaan(b), b.jenis_permukaan, b.tinggi, b.jumlah_lantai, b.luas_tapak, b.z_dasar_sumber,
                                         b.epsg_sumber, b.epsg_dikoreksi, b.measured_height_sumber, sorted(b.qc_flag), batch_id, id_lama))
                berubah += 1  # riwayat versi: DIRENCANAKAN (core.bangunan_riwayat belum diisi)

            # --- Nonaktif: ID lama yang tidak ditemukan lagi di impor ini (bukan kandidat tinjauan) ---
            dipakai = {x[1] for x in cocok} | {i for _, daftar in tinjauan for i, _ in daftar}
            hilang = [l.id for l in lama if l.id not in dipakai]
            for id_ in hilang:
                cur.execute("UPDATE core.registri_id SET status='nonaktif', berlaku_sampai=%s WHERE id=%s", (datetime.date.today(), id_))

            # --- Statistik ---
            tinggi_beda = [abs(b.tinggi - b.measured_height_sumber) for b in bangunan if b.tinggi is not None and b.measured_height_sumber is not None]
            qc = collections.Counter(f for b in bangunan for f in b.qc_flag)
            ringkasan = {
                "slug": a.slug, "batch_id": batch_id, "jenis": a.jenis, "bangunan_dibaca": len(bangunan), "per_berkas": per_berkas,
                "poligon_sumber": sum(b.stat.get("n_poligon_sumber", 0) for b in bangunan),
                "poligon_bersih": sum(b.stat.get("n_poligon_bersih", 0) for b in bangunan),
                "salinan_terbalik_dibuang": sum(b.stat.get("n_salinan_terbalik", 0) for b in bangunan),
                "duplikat_searah_dibuang": sum(b.stat.get("n_duplikat_searah", 0) for b in bangunan),
                "label_sumber_beda_dari_klasifikasi": sum(b.stat.get("n_label_sumber_beda", 0) for b in bangunan),
                "cocok_gml_id": per_jenis.get("gml_id", 0), "cocok_posisi": per_jenis.get("posisi", 0), "id_baru": len(id_baru),
                "nonaktif": len(hilang), "tinjauan_manual": len(tinjauan), "diperbarui": berubah, "tidak_berubah": tidak_berubah,
                "tinjauan_manual_detail": [{"gml_id": bangunan[i].gml_id, "pusat": pusat[i], "kandidat": [(k, round(n, 3)) for k, n in d]} for i, d in tinjauan],
                "qc_flag": dict(sorted(qc.items())),
                "tinggi_hitung_vs_measuredHeight": {
                    "n": len(tinggi_beda), "median_selisih_abs": round(statistics.median(tinggi_beda), 4) if tinggi_beda else None,
                    "maks_selisih_abs": round(max(tinggi_beda), 4) if tinggi_beda else None, "lebih_0_05m": sum(1 for x in tinggi_beda if x > 0.05)},
                "nomor_deskripsi_unik": len(set(n for n in nomor_desk if n is not None)),
                "detik": round(time.time() - t0, 1),
            }
            cur.execute("UPDATE staging.import_batch SET ringkasan = %s::jsonb WHERE id = %s", (json.dumps(ringkasan, ensure_ascii=False), batch_id))
        conn.commit()

    LAPORAN.mkdir(exist_ok=True)
    (LAPORAN / f"impor_{a.slug}_batch{batch_id}.json").write_text(json.dumps(ringkasan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ringkas = {k: ringkasan[k] for k in ("bangunan_dibaca", "cocok_gml_id", "cocok_posisi", "id_baru", "nonaktif", "tinjauan_manual", "diperbarui", "tidak_berubah")}
    print(f"Batch {batch_id} ({a.jenis}) selesai: {ringkas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
