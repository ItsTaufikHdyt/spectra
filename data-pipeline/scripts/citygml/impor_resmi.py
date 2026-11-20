#!/usr/bin/env python3
"""IMPOR RESMI seluruh CityGML (15 kelurahan) ke PostGIS, bertahap, dengan penerbitan ID resmi SATU KALI (ADR-003/004).

  staging           parse + bersihkan semua berkas aktif -> staging.bangunan_impor (belum ada ID)
  analisis          jumlah vs inventaris, duplikat dalam batch, posisi vs batas kelurahan, Z dasar, Berebas Tengah, qc_flag
  keputusan         terapkan config/keputusan_duplikat.yaml (ADR-007) + isi kelurahan_administratif di staging (belum ada ID)
  terbit            [setelah disetujui] terbitkan ID resmi (urut slug, gml_id, koordinat pusat), salin ke core.bangunan
  ekspor-registri   tulis config/registri_id.csv + .sha256 dari core.registri_id
  qc-ulang          terapkan aturan QC baru (footprint_mikro) pada data yang sudah ada; hanya qc_flag, ID/registri/tile tidak berubah
  stabilitas        impor kedua terhadap registri resmi, HANYA BACA (tidak mengubah registri); lapor jumlah per kategori

  data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/impor_resmi.py staging
  ... analisis [--batch N]
  ... terbit --batch N --ya-terbitkan-id-resmi [--keputusan config/keputusan_duplikat.yaml]

`terbit` menolak berjalan bila registri tidak kosong: ID resmi tidak pernah diterbitkan ulang. Bila ada masalah SETELAH terbit,
berhenti dan laporkan; jangan reset/terbitkan ulang diam-diam.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import sys
import time
from pathlib import Path

import yaml
from shapely import wkb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from muat import CONFIG, DP, EPSG, baca_dan_bersihkan, baca_sumber, bbox_dari, ewkt_permukaan, pusat_dari  # noqa: E402
from citygml.bangunan import AMBANG_TAPAK_MIKRO  # noqa: E402
from citygml.registri import Baru, Lama, cocokkan  # noqa: E402
from koneksi import buka_koneksi  # noqa: E402

LAPORAN = DP / "reports"
KEPUTUSAN_DEFAULT = DP / "config" / "keputusan_duplikat.yaml"
GEOJSON_KELURAHAN = DP / "processed" / "geojson" / "batas-kelurahan.norm.geojson"

SQL_STAGING = """INSERT INTO staging.bangunan_impor (batch_id, urut, slug, sumber_file, sumber_part, gml_id, nomor_deskripsi, footprint,
    pusat_x, pusat_y, geometri_lod2, jenis_permukaan, tinggi, jumlah_lantai, luas_tapak, z_dasar_sumber, epsg_sumber, epsg_dikoreksi,
    measured_height_sumber, qc_flag, stat)
    VALUES (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromWKB(%s, 32650), %s, %s, ST_GeomFromEWKT(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)"""


def daftar_slug() -> list[str]:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    return sorted({s["slug"] for s in cfg["sumber"] if s.get("aktif")})


def batch_staging(cur, batch: int | None) -> int:
    if batch is not None:
        return batch
    cur.execute("SELECT max(id) FROM staging.import_batch WHERE jenis = 'resmi'")
    b = cur.fetchone()[0]
    if b is None:
        raise SystemExit("Belum ada batch resmi; jalankan 'staging' dulu")
    return b


def simpan_laporan(nama: str, data: dict) -> Path:
    LAPORAN.mkdir(exist_ok=True)
    p = LAPORAN / nama
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    return p


# ------------------------------------------------------------------------------------------------------ staging
def cmd_staging(a) -> int:
    t0 = time.time()
    slugs = daftar_slug()
    with buka_koneksi() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM staging.bangunan_impor")
        if cur.fetchone()[0]:
            raise SystemExit("staging.bangunan_impor tidak kosong; kosongkan/reset dulu (tidak menimpa diam-diam)")
        cur.execute("INSERT INTO staging.import_batch (jenis, sumber, catatan, ringkasan) VALUES ('resmi', %s, %s, %s::jsonb) RETURNING id",
                    (f"raw/citygml ({len(slugs)} kelurahan)", "IMPOR RESMI tahap staging; ID belum diterbitkan", json.dumps({"tahap": "staging"})))
        batch_id = cur.fetchone()[0]
        urut, per_berkas, per_slug, qc = 0, [], {}, collections.Counter()
        for slug in slugs:
            print(f"== {slug}", flush=True)
            sumber = baca_sumber(slug)
            bangunan, nomor, pb = baca_dan_bersihkan(sumber)
            rows = []
            for b, n in zip(bangunan, nomor):
                px, py = pusat_dari(b)
                rows.append((batch_id, urut, b.slug, b.sumber_file, b.sumber_part, b.gml_id, n,
                             b.footprint.wkb if b.footprint is not None else None, px, py, ewkt_permukaan(b), b.jenis_permukaan,
                             b.tinggi, b.jumlah_lantai, b.luas_tapak, b.z_dasar_sumber, b.epsg_sumber, b.epsg_dikoreksi,
                             b.measured_height_sumber, sorted(b.qc_flag), json.dumps(b.stat)))
                urut += 1
            cur.executemany(SQL_STAGING, rows)
            for s, p in zip(sumber, pb):
                p.update(slug=slug, inventaris=s.get("bangunan_inventaris"), selisih=p["bangunan"] - (s.get("bangunan_inventaris") or 0))
            per_berkas += pb
            per_slug[slug] = len(bangunan)
            qc.update(f for b in bangunan for f in b.qc_flag)
        ringkasan = {"tahap": "staging", "bangunan": urut, "per_slug": per_slug, "per_berkas": per_berkas, "qc_flag": dict(sorted(qc.items())),
                     "selisih_inventaris": [p for p in per_berkas if p["selisih"]], "detik": round(time.time() - t0, 1)}
        cur.execute("UPDATE staging.import_batch SET ringkasan = %s::jsonb WHERE id = %s", (json.dumps(ringkasan), batch_id))
        conn.commit()
    p = simpan_laporan(f"impor_resmi_staging_batch{batch_id}.json", ringkasan)
    print(f"Batch {batch_id}: {urut} bangunan di staging ({ringkasan['detik']} s); selisih vs inventaris: {len(ringkasan['selisih_inventaris'])} berkas. Laporan: {p.name}")
    return 0


# ------------------------------------------------------------------------------------------------------ analisis
SQL_DUP_FOOTPRINT = """
SELECT a.urut, b.urut, a.slug, b.slug, a.sumber_file, b.sumber_file, a.sumber_part, b.sumber_part, a.gml_id, b.gml_id,
       ST_Distance(ST_Centroid(a.footprint), ST_Centroid(b.footprint)),
       ST_Area(ST_Intersection(a.footprint, b.footprint)) / NULLIF(ST_Area(ST_Union(a.footprint, b.footprint)), 0),
       a.tinggi, b.tinggi, a.luas_tapak, b.luas_tapak, ST_Equals(a.footprint, b.footprint), a.jenis_permukaan = b.jenis_permukaan,
       a.jumlah_lantai, b.jumlah_lantai
FROM staging.bangunan_impor a JOIN staging.bangunan_impor b
  ON b.batch_id = a.batch_id AND a.urut < b.urut AND a.footprint && b.footprint
 AND ST_DWithin(ST_Centroid(a.footprint), ST_Centroid(b.footprint), 2) AND ST_Intersects(a.footprint, b.footprint)
WHERE a.batch_id = %s"""

SQL_DUP_GML = """
SELECT a.urut, b.urut, a.slug, b.slug, a.sumber_file, b.sumber_file, a.sumber_part, b.sumber_part, a.gml_id,
       sqrt((a.pusat_x - b.pusat_x)^2 + (a.pusat_y - b.pusat_y)^2), a.tinggi, b.tinggi
FROM staging.bangunan_impor a JOIN staging.bangunan_impor b
  ON b.batch_id = a.batch_id AND a.urut < b.urut AND a.gml_id = b.gml_id AND a.gml_id IS NOT NULL
 AND sqrt((a.pusat_x - b.pusat_x)^2 + (a.pusat_y - b.pusat_y)^2) <= 2
WHERE a.batch_id = %s"""


def cmd_analisis(a) -> int:
    import numpy as np
    import shapely
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform

    with buka_koneksi() as conn, conn.cursor() as cur:
        batch = batch_staging(cur, a.batch)
        out: dict = {"batch": batch}
        # a) jumlah vs inventaris
        cur.execute("SELECT sumber_file, slug, count(*) FROM staging.bangunan_impor WHERE batch_id=%s GROUP BY 1,2 ORDER BY 2,1", (batch,))
        per_berkas = cur.fetchall()
        cfg = {Path(s["path"]).name: s for s in yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["sumber"]}
        out["per_berkas"] = [{"berkas": f, "slug": s, "staging": n, "inventaris": cfg[f]["bangunan_inventaris"], "selisih": n - cfg[f]["bangunan_inventaris"]} for f, s, n in per_berkas]
        out["total_staging"] = sum(n for *_, n in per_berkas)

        # b) duplikat dalam batch
        kasus = []
        cur.execute(SQL_DUP_FOOTPRINT, (batch,))
        for r in cur.fetchall():
            if r[11] is not None and r[11] >= 0.5:
                kasus.append({"dasar": "footprint (pusat<=2 m, IoU>=0,5)", "urut": [r[0], r[1]], "slug": [r[2], r[3]], "berkas": [r[4], r[5]],
                              "part": [r[6], r[7]], "gml_id": [r[8], r[9]], "jarak_pusat_m": round(r[10], 3), "iou": round(r[11], 3),
                              "tinggi": [float(r[12]), float(r[13])], "luas_tapak": [float(r[14]), float(r[15])],
                              "footprint_identik": r[16], "urutan_permukaan_sama": r[17], "jumlah_lantai": [r[18], r[19]]})
        cur.execute(SQL_DUP_GML, (batch,))
        sudah = {tuple(k["urut"]) for k in kasus}
        for r in cur.fetchall():
            if (r[0], r[1]) not in sudah:
                kasus.append({"dasar": "gml_id sama + pusat<=2 m (IoU<0,5)", "urut": [r[0], r[1]], "slug": [r[2], r[3]], "berkas": [r[4], r[5]],
                              "part": [r[6], r[7]], "gml_id": [r[8], r[8]], "jarak_pusat_m": round(r[9], 3), "tinggi": [float(r[10]), float(r[11])]})
        for k in kasus:
            k["kategori"] = ("berkas sama" if k["berkas"][0] == k["berkas"][1] else "satu kelurahan, berkas/part berbeda" if k["slug"][0] == k["slug"][1] else "antar kelurahan")
        out["duplikat_dalam_batch"] = kasus
        cur.execute("SELECT count(*) FROM staging.bangunan_impor WHERE batch_id=%s AND footprint IS NULL", (batch,))
        out["tanpa_footprint"] = cur.fetchone()[0]
        cur.execute("SELECT gml_id, count(*) FROM staging.bangunan_impor WHERE batch_id=%s AND gml_id IS NOT NULL GROUP BY 1 HAVING count(*)>1", (batch,))
        gml_ganda = cur.fetchall()
        out["gml_id_ganda"] = {"jumlah_gml_id": len(gml_ganda), "bangunan_terlibat": sum(n for _, n in gml_ganda)}

        # c) posisi vs batas kelurahan, per berkas
        tr = Transformer.from_crs(4326, EPSG, always_xy=True).transform
        batas = {f["properties"]["slug"]: transform(tr, shape(f["geometry"])) for f in json.loads(GEOJSON_KELURAHAN.read_text())["features"]}
        cur.execute("SELECT sumber_file, slug, pusat_x, pusat_y FROM staging.bangunan_impor WHERE batch_id=%s", (batch,))
        arr = collections.defaultdict(list)
        for f, s, x, y in cur.fetchall():
            arr[(f, s)].append((x, y))
        per_f, per_k = {}, collections.defaultdict(lambda: [0, 0])
        for (f, s), pts in arr.items():
            p = np.array(pts)
            ok = int(shapely.contains_xy(batas[s], p[:, 0], p[:, 1]).sum())
            per_f[f] = [ok, len(pts)]
            per_k[s][0] += ok
            per_k[s][1] += len(pts)
        out["posisi_di_dalam_kelurahan"] = {"per_berkas": {f: {"di_dalam": v[0], "total": v[1], "persen": round(100 * v[0] / v[1], 2)} for f, v in sorted(per_f.items())},
                                            "per_kelurahan": {s: {"di_dalam": v[0], "total": v[1], "persen": round(100 * v[0] / v[1], 2)} for s, v in sorted(per_k.items())},
                                            "total_persen": round(100 * sum(v[0] for v in per_k.values()) / sum(v[1] for v in per_k.values()), 2)}

        # d) Z dasar per berkas
        cur.execute("""SELECT sumber_file, count(*), count(*) FILTER (WHERE 'z_dasar_tidak_nol_di_sumber' = ANY(qc_flag)),
                       min(z_dasar_sumber), percentile_cont(0.5) WITHIN GROUP (ORDER BY z_dasar_sumber), max(z_dasar_sumber),
                       count(*) FILTER (WHERE geometri_lod2 IS NOT NULL AND ST_ZMin(geometri_lod2) = 0),
                       count(*) FILTER (WHERE geometri_lod2 IS NOT NULL AND ST_ZMin(geometri_lod2) <> 0),
                       count(*) FILTER (WHERE z_dasar_sumber IS NULL)
                       FROM staging.bangunan_impor WHERE batch_id=%s GROUP BY 1 ORDER BY 1""", (batch,))
        out["z_dasar"] = [{"berkas": r[0], "bangunan": r[1], "flag_z_tidak_nol": r[2], "z_sumber_min": float(r[3]) if r[3] is not None else None,
                           "z_sumber_median": round(float(r[4]), 3) if r[4] is not None else None, "z_sumber_maks": float(r[5]) if r[5] is not None else None,
                           "zmin_tile_nol": r[6], "zmin_tile_bukan_nol": r[7], "z_sumber_kosong": r[8]} for r in cur.fetchall()]

        # e) Berebas Tengah dan EPSG terkoreksi
        cur.execute("""SELECT count(*), count(*) FILTER (WHERE jumlah_lantai IS NULL), count(*) FILTER (WHERE jumlah_lantai = 0),
                       count(*) FILTER (WHERE tinggi IS NULL), min(tinggi), max(tinggi)
                       FROM staging.bangunan_impor WHERE batch_id=%s AND slug='berebas_tengah'""", (batch,))
        r = cur.fetchone()
        out["berebas_tengah"] = {"bangunan": r[0], "lantai_null": r[1], "lantai_nol": r[2], "tinggi_null": r[3], "tinggi_min": float(r[4]), "tinggi_maks": float(r[5])}
        cur.execute("""SELECT sumber_file, count(*), count(*) FILTER (WHERE epsg_dikoreksi = 32650 AND 'epsg_dikoreksi' = ANY(qc_flag))
                       FROM staging.bangunan_impor WHERE batch_id=%s AND epsg_sumber <> 32650 GROUP BY 1""", (batch,))
        out["epsg_terkoreksi"] = [{"berkas": f, "bangunan": n, "berflag": k} for f, n, k in cur.fetchall()]

        # f) qc_flag per kelurahan
        cur.execute("SELECT slug, f, count(*) FROM staging.bangunan_impor, unnest(qc_flag) f WHERE batch_id=%s GROUP BY 1,2 ORDER BY 1,2", (batch,))
        qc: dict = collections.defaultdict(dict)
        for s, f, n in cur.fetchall():
            qc[s][f] = n
        out["qc_per_kelurahan"] = qc
        cur.execute("SELECT count(*) FROM staging.bangunan_impor WHERE batch_id=%s AND tinggi < 0.1", (batch,))
        out["tinggi_kurang_0_1m"] = cur.fetchone()[0]
    p = simpan_laporan(f"impor_resmi_analisis_batch{batch}.json", out)
    print(f"Laporan analisis: {p}")
    print(f"total staging {out['total_staging']}; berkas dengan selisih inventaris: {[x for x in out['per_berkas'] if x['selisih']]}")
    print(f"duplikat dalam batch: {len(kasus)}; tanpa footprint: {out['tanpa_footprint']}; gml_id ganda: {out['gml_id_ganda']}")
    print(f"posisi di dalam kelurahan: {out['posisi_di_dalam_kelurahan']['total_persen']}%")
    return 0


# ------------------------------------------------------------------------------------------------------ keputusan
def baca_keputusan(path: Path) -> dict:
    """config/keputusan_duplikat.yaml (ADR-007): kecualikan, tandai, atribut_dari_duplikat, pertahankan_keduanya."""
    if not path.exists():
        return {"kecualikan": [], "tandai": [], "atribut_dari_duplikat": [], "pertahankan_keduanya": []}
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {k: d.get(k) or [] for k in ("kecualikan", "tandai", "atribut_dari_duplikat", "pertahankan_keduanya")}


def kunci_cocok(k: dict, slug, sumber_file, gml_id, px, py) -> bool:
    return (k["slug"] == slug and k["sumber_file"] == sumber_file and k.get("gml_id") == gml_id
            and abs(k["pusat"][0] - px) < 0.01 and abs(k["pusat"][1] - py) < 0.01)


def dikecualikan(keputusan: dict, slug, sumber_file, gml_id, px, py) -> bool:
    return any(kunci_cocok(e["dikecualikan"], slug, sumber_file, gml_id, px, py) for e in keputusan["kecualikan"])


def cari_urut(cur, batch: int, k: dict) -> int:
    cur.execute("SELECT urut FROM staging.bangunan_impor WHERE batch_id=%s AND slug=%s AND sumber_file=%s AND gml_id IS NOT DISTINCT FROM %s "
                "AND abs(pusat_x-%s) < 0.01 AND abs(pusat_y-%s) < 0.01", (batch, k["slug"], k["sumber_file"], k.get("gml_id"), k["pusat"][0], k["pusat"][1]))
    r = cur.fetchall()
    if len(r) != 1:
        raise SystemExit(f"Kunci keputusan harus cocok tepat 1 baris (cocok {len(r)}): {k}")
    return r[0][0]


def cmd_keputusan(a) -> int:
    """Terapkan keputusan duplikat + isi kelurahan_administratif di staging (sebelum ID terbit). Satu kali per batch."""
    import numpy as np
    import shapely
    from pyproj import Transformer
    from shapely.geometry import shape

    kep = baca_keputusan(Path(a.keputusan))
    with buka_koneksi() as conn, conn.cursor() as cur:
        batch = batch_staging(cur, a.batch)
        cur.execute("SELECT ringkasan FROM staging.import_batch WHERE id=%s AND jenis='resmi'", (batch,))
        ring = cur.fetchone()[0]
        if ring.get("tahap") != "staging" or ring.get("keputusan_diterapkan"):
            raise SystemExit(f"Batch {batch}: tahap {ring.get('tahap')!r}, keputusan_diterapkan={ring.get('keputusan_diterapkan')}; tidak diterapkan ulang")
        for e in kep["kecualikan"]:
            u, ur = cari_urut(cur, batch, e["dikecualikan"]), cari_urut(cur, batch, e["dipertahankan"])
            cur.execute("UPDATE staging.bangunan_impor SET keputusan='kecualikan', rujukan_urut=%s, alasan_keputusan=%s WHERE batch_id=%s AND urut=%s", (ur, e["alasan"], batch, u))
        for t in kep["tandai"]:
            cur.execute("UPDATE staging.bangunan_impor SET qc_flag = array_append(qc_flag, %s) WHERE batch_id=%s AND urut=%s AND NOT %s = ANY(qc_flag)",
                        (t["flag"], batch, cari_urut(cur, batch, t["bangunan"]), t["flag"]))
        for t in kep["atribut_dari_duplikat"]:
            if t["atribut"] != ["jumlah_lantai"]:
                raise SystemExit(f"Hanya jumlah_lantai yang didukung: {t}")
            ut, us = cari_urut(cur, batch, t["tujuan"]), cari_urut(cur, batch, t["sumber"])
            cur.execute("UPDATE staging.bangunan_impor d SET jumlah_lantai = s.jumlah_lantai, qc_flag = CASE WHEN 'atribut_dari_duplikat' = ANY(d.qc_flag) THEN d.qc_flag ELSE array_append(d.qc_flag, 'atribut_dari_duplikat') END, "
                        "alasan_keputusan = 'jumlah_lantai diisi dari salinan ' || s.gml_id FROM staging.bangunan_impor s "
                        "WHERE d.batch_id=%s AND d.urut=%s AND s.batch_id=d.batch_id AND s.urut=%s AND d.jumlah_lantai IS NULL AND s.jumlah_lantai IS NOT NULL", (batch, ut, us))
            if cur.rowcount != 1:
                raise SystemExit(f"Pengisian atribut tidak berlaku tepat 1 baris: {t}")

        # kelurahan_administratif: pusat footprint (atau pusat bbox bila tanpa footprint) vs batas administratif
        tr = Transformer.from_crs(4326, EPSG, always_xy=True)
        batas = {f["properties"]["slug"]: shapely.transform(shape(f["geometry"]), lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))
                 for f in json.loads(GEOJSON_KELURAHAN.read_text())["features"]}
        cur.execute("SELECT urut, pusat_x, pusat_y FROM staging.bangunan_impor WHERE batch_id=%s ORDER BY urut", (batch,))
        rows = cur.fetchall()
        xs, ys = np.array([r[1] for r in rows]), np.array([r[2] for r in rows])
        nama = sorted(batas)
        mask = np.array([shapely.contains_xy(batas[n], xs, ys) for n in nama])
        tumpang = int((mask.sum(axis=0) > 1).sum())
        kel = [nama[int(mask[:, i].argmax())] if mask[:, i].any() else None for i in range(len(rows))]
        cur.executemany("UPDATE staging.bangunan_impor SET kelurahan_administratif=%s WHERE batch_id=%s AND urut=%s", [(k, batch, r[0]) for k, r in zip(kel, rows)])
        cur.execute("UPDATE staging.bangunan_impor SET qc_flag = array_append(qc_flag, 'kelurahan_beda_dengan_sumber') "
                    "WHERE batch_id=%s AND kelurahan_administratif IS NOT NULL AND kelurahan_administratif <> slug", (batch,))
        cur.execute("""SELECT (keputusan IS NULL) AS dipertahankan, (footprint IS NULL) AS tanpa_footprint,
                       CASE WHEN kelurahan_administratif IS NULL THEN 'di_luar_batas' WHEN kelurahan_administratif = slug THEN 'sama' ELSE 'beda' END, count(*)
                       FROM staging.bangunan_impor WHERE batch_id=%s GROUP BY 1,2,3 ORDER BY 1 DESC,2,3""", (batch,))
        kombinasi = [{"dipertahankan": r[0], "tanpa_footprint": r[1], "kategori": r[2], "jumlah": r[3]} for r in cur.fetchall()]
        cur.execute("""SELECT slug, kelurahan_administratif, count(*) FROM staging.bangunan_impor WHERE batch_id=%s AND keputusan IS NULL
                       AND kelurahan_administratif IS NOT NULL AND kelurahan_administratif <> slug GROUP BY 1,2 ORDER BY 3 DESC""", (batch,))
        beda = [{"slug_sumber": r[0], "kelurahan_administratif": r[1], "jumlah": r[2]} for r in cur.fetchall()]
        cur.execute("SELECT count(*) FROM staging.bangunan_impor WHERE batch_id=%s AND keputusan='kecualikan'", (batch,))
        n_kec = cur.fetchone()[0]
        if n_kec != len(kep["kecualikan"]):
            raise SystemExit(f"Jumlah pengecualian {n_kec} != keputusan {len(kep['kecualikan'])}")
        hasil = {"batch": batch, "dikecualikan": n_kec, "diharapkan_diterbitkan": len(rows) - n_kec, "tandai": len(kep["tandai"]),
                 "atribut_dari_duplikat": len(kep["atribut_dari_duplikat"]), "dipertahankan_keduanya": len(kep["pertahankan_keduanya"]),
                 "kelurahan_administratif_tumpang_tindih_batas": tumpang, "kombinasi_kelurahan": kombinasi, "beda_per_pasangan": beda}
        cur.execute("UPDATE staging.import_batch SET ringkasan = ringkasan || %s::jsonb WHERE id=%s", (json.dumps({"keputusan_diterapkan": True, "keputusan_ringkas": hasil}), batch))
        conn.commit()
    p = simpan_laporan(f"impor_resmi_keputusan_batch{batch}.json", hasil)
    print(f"Keputusan diterapkan: {n_kec} dikecualikan, diharapkan {hasil['diharapkan_diterbitkan']} ID. Tumpang tindih batas: {tumpang}. Laporan: {p.name}")
    for k in kombinasi:
        print("  ", k)
    return 0


# ------------------------------------------------------------------------------------------------------ terbit
def cmd_terbit(a) -> int:
    if not a.ya_terbitkan_id_resmi:
        raise SystemExit("Penerbitan ID resmi hanya SATU KALI. Tambahkan --ya-terbitkan-id-resmi bila sudah disetujui.")
    kep = baca_keputusan(Path(a.keputusan))
    t0 = time.time()
    with buka_koneksi() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM core.registri_id")
        if cur.fetchone()[0]:
            raise SystemExit("core.registri_id TIDAK kosong: ID resmi tidak boleh diterbitkan ulang. Berhenti.")
        cur.execute("SELECT ringkasan FROM staging.import_batch WHERE id = %s AND jenis = 'resmi'", (a.batch,))
        r = cur.fetchone()
        if not r or r[0].get("tahap") != "staging" or not r[0].get("keputusan_diterapkan"):
            raise SystemExit(f"Batch {a.batch} harus berstatus 'staging' dengan keputusan diterapkan (jalankan 'keputusan' dulu)")
        cur.execute("SELECT count(*) FROM staging.bangunan_impor WHERE batch_id=%s AND keputusan='kecualikan'", (a.batch,))
        if cur.fetchone()[0] != len(kep["kecualikan"]):
            raise SystemExit("Pengecualian di staging tidak sama dengan config/keputusan_duplikat.yaml")
        cur.execute("SELECT urut, slug, gml_id, pusat_x, pusat_y FROM staging.bangunan_impor WHERE batch_id=%s AND keputusan IS NULL", (a.batch,))
        urut = sorted(cur.fetchall(), key=lambda r: (r[1], r[2] is None, r[2] or "", r[3], r[4], r[0]))  # ADR-003: slug sumber, gml_id, koordinat pusat
        print(f"Menerbitkan {len(urut)} ID resmi (dikecualikan oleh keputusan: {len(kep['kecualikan'])}) ...", flush=True)
        for u, slug, gml_id, px, py in urut:
            cur.execute("INSERT INTO core.registri_id (gml_id, slug, pusat_footprint, batch_id, status) "
                        "VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 32650), %s, 'aktif') RETURNING id", (gml_id, slug, px, py, a.batch))
            cur.execute("UPDATE staging.bangunan_impor SET id = %s WHERE batch_id=%s AND urut=%s", (cur.fetchone()[0], a.batch, u))
        cur.execute("""INSERT INTO core.bangunan (id, gml_id, slug, sumber_file, sumber_part, footprint, geometri_lod2, jenis_permukaan, tinggi,
                       jumlah_lantai, luas_tapak, z_dasar_sumber, epsg_sumber, epsg_dikoreksi, measured_height_sumber, qc_flag, batch_id, kelurahan_administratif)
                       SELECT id, gml_id, slug, sumber_file, sumber_part, footprint, geometri_lod2, jenis_permukaan, tinggi, jumlah_lantai,
                       luas_tapak, z_dasar_sumber, epsg_sumber, epsg_dikoreksi, measured_height_sumber, qc_flag, batch_id, kelurahan_administratif
                       FROM staging.bangunan_impor WHERE batch_id=%s AND id IS NOT NULL""", (a.batch,))
        cur.execute("UPDATE staging.bangunan_impor s SET rujukan_id = k.id FROM staging.bangunan_impor k "
                    "WHERE s.batch_id=%s AND k.batch_id=s.batch_id AND k.urut=s.rujukan_urut AND s.keputusan='kecualikan'", (a.batch,))
        if cur.rowcount != len(kep["kecualikan"]):
            raise SystemExit(f"Rujukan salinan yang dikecualikan tidak lengkap ({cur.rowcount}); transaksi dibatalkan")
        cur.execute("SELECT count(*), min(nomor), max(nomor), min(id), max(id) FROM core.registri_id WHERE status='aktif'")
        n, n0, n1, i0, i1 = cur.fetchone()
        cur.execute("SELECT count(*) FROM core.bangunan WHERE batch_id=%s", (a.batch,))
        nb = cur.fetchone()[0]
        if not (n == nb == len(urut) and n0 == 1 and n1 == n):
            raise SystemExit(f"Verifikasi gagal (registri {n}, bangunan {nb}, diharapkan {len(urut)}; nomor {n0}..{n1}); transaksi dibatalkan")
        ring = {"tahap": "terbit", "tanggal_penerbitan": datetime.date.today().isoformat(), "id_diterbitkan": n, "id_pertama": i0, "id_terakhir": i1,
                "dikecualikan_keputusan": len(kep["kecualikan"]), "detik_terbit": round(time.time() - t0, 1)}
        cur.execute("UPDATE staging.import_batch SET ringkasan = ringkasan || %s::jsonb, catatan = %s WHERE id = %s",
                    (json.dumps(ring, default=str), "IMPOR RESMI: ID resmi diterbitkan", a.batch))
        conn.commit()
    simpan_laporan(f"impor_resmi_terbit_batch{a.batch}.json", ring)
    print(f"SELESAI: {n} ID resmi ({i0} .. {i1}), batch {a.batch}. JANGAN terbitkan ulang; lanjutkan ekspor-registri.")
    return 0


# ------------------------------------------------------------------------------------------------------ ekspor registri
def cmd_ekspor_registri(a) -> int:
    import csv
    import io

    tujuan = DP / "config" / "registri_id.csv"
    with buka_koneksi() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, gml_id, slug, ST_X(pusat_footprint), ST_Y(pusat_footprint), status, diterbitkan_pada, batch_id FROM core.registri_id ORDER BY nomor")
        rows = cur.fetchall()
        cur.execute("SELECT id, jenis, ringkasan->>'tanggal_penerbitan' FROM staging.import_batch WHERE id = (SELECT min(batch_id) FROM core.registri_id)")
        b = cur.fetchone()
    if not rows or b[1] != "resmi":
        raise SystemExit("Registri kosong atau bukan batch resmi; tidak diekspor")
    buf = io.StringIO()
    buf.write(f"# Registri ID bangunan RESMI spectra (ADR-003). Batch {b[0]} (jenis {b[1]}), tanggal penerbitan {b[2]} (waktu lokal; kolom diterbitkan_pada dalam UTC), {len(rows)} ID.\n")
    buf.write("# Dibuat dari core.registri_id oleh scripts/citygml/impor_resmi.py ekspor-registri. JANGAN dibuat ulang atau diedit;\n")
    buf.write("# ID tidak pernah dipakai ulang. Checksum SHA-256 berkas ini ada di registri_id.csv.sha256. Baca dengan comment='#'.\n")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "gml_id", "slug", "pusat_x_epsg32650", "pusat_y_epsg32650", "status", "diterbitkan_pada", "batch_id"])
    for r in rows:
        w.writerow([r[0], r[1] or "", r[2], f"{r[3]:.3f}", f"{r[4]:.3f}", r[5], r[6].astimezone(datetime.timezone.utc).isoformat(timespec="seconds"), r[7]])
    tujuan.write_text(buf.getvalue(), encoding="utf-8")
    h = hashlib.sha256(tujuan.read_bytes()).hexdigest()
    tujuan.with_name(tujuan.name + ".sha256").write_text(f"{h}  {tujuan.name}\n", encoding="utf-8")
    print(f"Ditulis {tujuan} ({len(rows)} ID), sha256 {h}")
    return 0


# ------------------------------------------------------------------------------------------------------ qc ulang
def cmd_qc_ulang(a) -> int:
    """Terapkan aturan QC yang dapat dihitung dari data tersimpan pada data yang SUDAH ada (staging dan core).
    Saat ini: footprint_mikro (luas footprint < AMBANG_TAPAK_MIKRO, sama dengan aturan di citygml/bangunan.py).
    Hanya mengubah kolom qc_flag; ID, registri, geometri, dan tile tidak berubah. Idempoten."""
    with buka_koneksi() as conn, conn.cursor() as cur:
        hasil = {"ambang_m2": AMBANG_TAPAK_MIKRO}
        for tabel, kunci in (("staging.bangunan_impor", "WHERE batch_id = 1 AND "), ("core.bangunan", "WHERE ")):
            cur.execute(f"UPDATE {tabel} SET qc_flag = ARRAY(SELECT DISTINCT unnest(array_append(qc_flag, 'footprint_mikro')) ORDER BY 1) "
                        f"{kunci}footprint IS NOT NULL AND ST_Area(footprint) < %s AND NOT 'footprint_mikro' = ANY(qc_flag)", (AMBANG_TAPAK_MIKRO,))
            hasil[tabel] = cur.rowcount
        cur.execute("SELECT count(*), count(*) FILTER (WHERE tinggi >= 0.1) FROM core.bangunan WHERE 'footprint_mikro' = ANY(qc_flag)")
        hasil["core_total_berflag"], hasil["core_masuk_tile"] = cur.fetchone()
        cur.execute("SELECT slug, count(*) FROM core.bangunan WHERE 'footprint_mikro' = ANY(qc_flag) GROUP BY 1 ORDER BY 1")
        hasil["per_kelurahan"] = dict(cur.fetchall())
        cur.execute("SELECT count(*) FROM core.bangunan WHERE luas_tapak = 0 AND tinggi >= 0.1 AND NOT 'footprint_mikro' = ANY(qc_flag)")
        hasil["luas_nol_tanpa_flag"] = cur.fetchone()[0]
        conn.commit()
    p = simpan_laporan("impor_resmi_qc_footprint_mikro.json", hasil)
    print(f"footprint_mikro (< {AMBANG_TAPAK_MIKRO} m2): {hasil}. Laporan: {p.name}")
    return 0


# ------------------------------------------------------------------------------------------------------ stabilitas
def cmd_stabilitas(a) -> int:
    keputusan = baca_keputusan(Path(a.keputusan))
    cek_sql = "SELECT count(*), md5(string_agg(id || '|' || coalesce(gml_id,'') || '|' || slug || '|' || status, ',' ORDER BY nomor)) FROM core.registri_id"
    total: collections.Counter = collections.Counter()
    per_slug, tinjauan_all = {}, []
    with buka_koneksi() as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute(cek_sql)
            sebelum = cur.fetchone()
            for slug in daftar_slug():
                bangunan, _, _ = baca_dan_bersihkan(baca_sumber(slug))
                pusat = [pusat_dari(b) for b in bangunan]
                kept = [i for i, b in enumerate(bangunan) if not dikecualikan(keputusan, slug, b.sumber_file, b.gml_id, *pusat[i])]
                hitung = collections.Counter(bangunan[i].gml_id for i in kept if bangunan[i].gml_id)
                baru = [Baru(j, bangunan[i].gml_id, bool(bangunan[i].gml_id) and hitung[bangunan[i].gml_id] == 1, pusat[i], bangunan[i].footprint,
                             bbox_dari(bangunan[i]), bangunan[i].tinggi) for j, i in enumerate(kept)]
                cur.execute("SELECT r.id, r.gml_id, ST_X(r.pusat_footprint), ST_Y(r.pusat_footprint), ST_AsBinary(b.footprint), ST_XMin(b.geometri_lod2), "
                            "ST_YMin(b.geometri_lod2), ST_ZMin(b.geometri_lod2), ST_XMax(b.geometri_lod2), ST_YMax(b.geometri_lod2), ST_ZMax(b.geometri_lod2), b.tinggi "
                            "FROM core.registri_id r JOIN core.bangunan b ON b.id = r.id WHERE r.slug=%s AND r.status='aktif'", (slug,))
                lama = [Lama(r[0], r[1], (r[2], r[3]), wkb.loads(bytes(r[4])) if r[4] is not None else None,
                             tuple(float(v) for v in r[5:11]) if r[5] is not None else None, float(r[11]) if r[11] is not None else None) for r in cur.fetchall()]
                cocok, tinjauan, id_baru = cocokkan(baru, lama)
                jenis = collections.Counter(j for _, _, j in cocok)
                hilang = len(lama) - len({c[1] for c in cocok}) - len({i for _, d in tinjauan for i, _ in d})
                tf = {b.idx for b in baru if b.footprint is None}
                per_slug[slug] = {"dibaca": len(bangunan), "dikecualikan": len(bangunan) - len(kept), "cocok_gml_id": jenis.get("gml_id", 0),
                                  "cocok_posisi": jenis.get("posisi", 0), "id_baru": len(id_baru), "tinjauan_manual": len(tinjauan), "id_tidak_ditemukan": hilang,
                                  "tf_total": len(tf), "tf_cocok_gml_id": sum(1 for i, _, j in cocok if i in tf and j == "gml_id"),
                                  "tf_cocok_posisi": sum(1 for i, _, j in cocok if i in tf and j == "posisi"),
                                  "tf_id_baru": sum(1 for i in id_baru if i in tf), "tf_tinjauan": sum(1 for i, _ in tinjauan if i in tf)}
                tinjauan_all += [{"slug": slug, "gml_id": baru[i].gml_id, "pusat": baru[i].pusat, "kandidat": d} for i, d in tinjauan]
                total.update(per_slug[slug])
                print(f"  {slug}: {per_slug[slug]}", flush=True)
            cur.execute(cek_sql)
            sesudah = cur.fetchone()
    hasil = {"total": dict(total), "per_kelurahan": per_slug, "tinjauan_manual": tinjauan_all, "registri_sebelum": list(sebelum), "registri_sesudah": list(sesudah),
             "registri_tidak_berubah": sebelum == sesudah}
    hasil["tanpa_footprint"] = {k[3:]: v for k, v in total.items() if k.startswith("tf_")}
    p = simpan_laporan("impor_resmi_stabilitas.json", hasil)
    print(f"STABILITAS: {dict(total)}; registri tidak berubah: {sebelum == sesudah}. Laporan: {p.name}")
    return 0 if sebelum == sesudah else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("staging")
    p = sp.add_parser("keputusan")
    p.add_argument("--batch", type=int)
    p.add_argument("--keputusan", default=str(KEPUTUSAN_DEFAULT))
    p = sp.add_parser("analisis")
    p.add_argument("--batch", type=int)
    p = sp.add_parser("terbit")
    p.add_argument("--batch", type=int, required=True)
    p.add_argument("--ya-terbitkan-id-resmi", action="store_true")
    p.add_argument("--keputusan", default=str(KEPUTUSAN_DEFAULT))
    sp.add_parser("ekspor-registri")
    sp.add_parser("qc-ulang")
    p = sp.add_parser("stabilitas")
    p.add_argument("--keputusan", default=str(KEPUTUSAN_DEFAULT))
    a = ap.parse_args(argv)
    return {"staging": cmd_staging, "analisis": cmd_analisis, "keputusan": cmd_keputusan, "terbit": cmd_terbit, "ekspor-registri": cmd_ekspor_registri, "qc-ulang": cmd_qc_ulang, "stabilitas": cmd_stabilitas}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
