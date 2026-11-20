#!/usr/bin/env python3
"""Laporan verifikasi tile seluruh kota (Langkah 6 impor resmi): PostGIS vs tile vs tile lama (riwayat).

Prasyarat (hasil perintah lain; keluaran antara di processed/analisis/, tidak di-commit):
  node scripts/citygml/verifikasi_tile.cjs processed/3dtiles/<slug> processed/analisis/tile/<slug>.json
  node scripts/citygml/fitur_glb.cjs processed/3dtiles/<slug> processed/analisis/fitur/v2_<slug>.json   (segitiga + pusat ECEF per fitur)
  processed/analisis/fitur/lama_<slug>.json = data tile lama CityJSON yang disimpan 2026-11-20 sebelum tile lama dihapus (riwayat; tidak bisa dibuat ulang).
Keluaran: reports/impor_resmi_verifikasi.json dan .md.
"""

from __future__ import annotations

import collections
import json
import math
import statistics
import sys
from pathlib import Path

DP = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DP / "db"))
from koneksi import buka_koneksi  # noqa: E402

A = DP / "processed" / "analisis"
PROPERTI = ["id", "gml_id", "nama", "tinggi", "jumlah_lantai", "luas_tapak"]
MAKS_BYTE = 3 * 1024 * 1024


def cocokkan_posisi(lama: list[dict], baru: list[dict], batas=2.0):
    """Pasangan satu-ke-satu (timbal balik terdekat, jarak <= batas m) antara fitur tile lama dan v2 (pusat ECEF)."""
    sel = 20.0
    grid: dict = collections.defaultdict(list)
    for j, f in enumerate(baru):
        grid[tuple(int(c // sel) for c in f["ecef"])].append(j)

    def terdekat(e, pool_grid, pool):
        k = tuple(int(c // sel) for c in e)
        best = (1e18, None)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in pool_grid.get((k[0] + dx, k[1] + dy, k[2] + dz), []):
                        d = math.dist(e, pool[j]["ecef"])
                        if d < best[0]:
                            best = (d, j)
        return best

    grid_lama: dict = collections.defaultdict(list)
    for i, f in enumerate(lama):
        grid_lama[tuple(int(c // sel) for c in f["ecef"])].append(i)
    pasangan = []
    for i, f in enumerate(lama):
        d, j = terdekat(f["ecef"], grid, baru)
        if j is None or d > batas:
            continue
        d2, i2 = terdekat(baru[j]["ecef"], grid_lama, lama)
        if i2 == i:
            pasangan.append((i, j))
    return pasangan


def main() -> int:
    with buka_koneksi() as conn, conn.cursor() as cur:
        cur.execute("SELECT slug, count(*), count(*) FILTER (WHERE keputusan='kecualikan') FROM staging.bangunan_impor WHERE batch_id=1 GROUP BY 1")
        stg = {s: (n, k) for s, n, k in cur.fetchall()}
        cur.execute("SELECT slug, count(*), count(*) FILTER (WHERE tinggi < 0.1), count(*) FILTER (WHERE tinggi >= 0.1) FROM core.bangunan GROUP BY 1")
        pg = {s: (n, k, m) for s, n, k, m in cur.fetchall()}
        cur.execute("SELECT id, slug, gml_id, tinggi, jumlah_lantai, luas_tapak FROM core.bangunan WHERE tinggi >= 0.1")
        db = {r[0]: r for r in cur.fetchall()}
        cur.execute("SELECT f, count(*) FROM core.bangunan, unnest(qc_flag) f GROUP BY 1 ORDER BY 2 DESC")
        qc_kota = dict(cur.fetchall())
        cur.execute("SELECT slug, f, count(*) FROM core.bangunan, unnest(qc_flag) f GROUP BY 1,2 ORDER BY 1,3 DESC")
        qc_slug: dict = collections.defaultdict(dict)
        for s, f, n in cur.fetchall():
            qc_slug[s][f] = n
        cur.execute("SELECT count(*) FROM core.bangunan")
        n_pg = cur.fetchone()[0]

    slugs = sorted(pg)
    baris, kontrak, semua_id = [], {}, collections.Counter()
    tot = collections.Counter()
    pasangan_tot = [0, 0, 0]  # pasangan, segitiga lama, segitiga v2
    rasio_slug = {}
    for s in slugs:
        t = json.loads((A / "tile" / f"{s}.json").read_text())
        lama = json.loads((A / "fitur" / f"lama_{s}.json").read_text())
        baru = json.loads((A / "fitur" / f"v2_{s}.json").read_text())
        ids = t["ids"]
        semua_id.update(ids)
        db_s = {i for i, r in db.items() if r[1] == s}
        # atribut identik dengan PostGIS (float32 toleran)
        beda = 0
        idx = {i: k for k, i in enumerate(ids)}
        for i in db_s & set(ids):
            r, k = db[i], idx[i]
            kol = t["kolom"]
            if kol["gml_id"][k] != r[2] or kol["nama"][k] != f"Bangunan {i}" or abs(kol["tinggi"][k] - float(r[3])) > 0.005:
                beda += 1
            elif (kol["jumlah_lantai"][k] if kol["jumlah_lantai"][k] is not None else None) != r[4]:
                beda += 1
            elif (r[5] is None) != (kol["luas_tapak"][k] is None) or (r[5] is not None and abs(kol["luas_tapak"][k] - float(r[5])) > max(0.01, float(r[5]) * 1e-6)):
                beda += 1
        pas = cocokkan_posisi(lama, baru)
        tl, tv = sum(lama[i]["tri"] for i, _ in pas), sum(baru[j]["tri"] for _, j in pas)
        pasangan_tot[0] += len(pas); pasangan_tot[1] += tl; pasangan_tot[2] += tv
        rasio_slug[s] = {"pasangan": len(pas), "segitiga_lama": tl, "segitiga_v2": tv, "rasio": round(tl / tv, 3) if tv else None}
        n_stg, n_kec = stg[s]
        n_pg_s, n_rendah, n_tile_dr = pg[s]
        baris.append({"kelurahan": s, "sumber_staging": n_stg, "duplikat_dikecualikan": n_kec, "postgis": n_pg_s, "tinggi_kurang_0_1m": n_rendah,
                      "diharapkan_di_tile": n_tile_dr, "fitur_v2": t["totalFitur"], "fitur_lama": len(lama), "selisih_v2_lama": t["totalFitur"] - len(lama),
                      "segitiga_v2": t["totalSegitiga"], "segitiga_lama": sum(f["tri"] for f in lama)})
        ext_ok = all("EXT_structural_metadata" in (g["extensionsUsed"] or []) and "EXT_mesh_features" in (g["extensionsUsed"] or []) and g["meshFeatures"] for g in t["glb"])
        kontrak[s] = {"versi": t["versi"], "region": len(t["region"]) == 6, "transform": t["transform"], "refine": t["refine"], "glb": len(t["glb"]),
                      "maks_byte": t["maksByte"], "maks_<=3MB": t["maksByte"] <= MAKS_BYTE, "ekstensi_di_semua_glb": ext_ok,
                      "properti_di_kelas": t["propertiDiKelas"], "enam_properti": sorted(t["propertiDiKelas"]) == sorted(PROPERTI),
                      "tile_tanpa_properti": t["tileTanpaProperti"], "id_unik_dalam_kelurahan": t["idUnik"] == t["totalFitur"],
                      "id_sama_dengan_postgis": set(ids) == db_s, "atribut_beda_dengan_postgis": beda,
                      "warna_baseColorFactor": t["glb"][0]["material"], "asset_extras": bool(t["asetExtras"]),
                      "jumlah_lantai_null": t["jumlahLantai"]["null"], "jumlah_lantai_nol": t["jumlahLantai"]["nol"],
                      "luas_tapak_null": t["luasTapak"]["null"], "luas_tapak_nol": t["luasTapak"]["nol"]}
    for b in baris:
        for k in ("sumber_staging", "duplikat_dikecualikan", "postgis", "tinggi_kurang_0_1m", "diharapkan_di_tile", "fitur_v2", "fitur_lama", "selisih_v2_lama", "segitiga_v2", "segitiga_lama"):
            tot[k] += b[k]
    id_ganda = [i for i, n in semua_id.items() if n > 1]
    hasil = {"per_kelurahan": baris, "total": dict(tot), "kontrak_frontend": kontrak, "id_unik_seluruh_kota": {"total_fitur": sum(semua_id.values()), "unik": len(semua_id), "ganda": len(id_ganda)},
             "id_tile_sama_dengan_postgis_seluruh_kota": set(semua_id) == set(db), "postgis_total": n_pg,
             "segitiga": {"v2": tot["segitiga_v2"], "lama": tot["segitiga_lama"], "pasangan_satu_ke_satu": pasangan_tot[0], "segitiga_lama_pada_pasangan": pasangan_tot[1],
                          "segitiga_v2_pada_pasangan": pasangan_tot[2], "rasio_pada_pasangan": round(pasangan_tot[1] / pasangan_tot[2], 3), "per_kelurahan": rasio_slug},
             "qc_flag_kota": qc_kota, "qc_flag_per_kelurahan": qc_slug}
    (DP / "reports" / "impor_resmi_verifikasi.json").write_text(json.dumps(hasil, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    f = lambda n: f"{n:,}".replace(",", ".")
    L = ["# Verifikasi impor resmi dan tile v2 (seluruh kota)", "", "Dihasilkan oleh `scripts/citygml/laporan_verifikasi.py`; angka lengkap di `impor_resmi_verifikasi.json`.", "",
         "## Tabel per kelurahan", "",
         "| Kelurahan | Sumber (staging) | Duplikat dikecualikan | PostGIS | < 0,1 m (tidak masuk tile) | Diharapkan di tile | Fitur v2 | Fitur tile lama | v2 − lama |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for b in baris:
        L.append(f"| {b['kelurahan']} | {f(b['sumber_staging'])} | {b['duplikat_dikecualikan']} | {f(b['postgis'])} | {b['tinggi_kurang_0_1m']} | {f(b['diharapkan_di_tile'])} | {f(b['fitur_v2'])} | {f(b['fitur_lama'])} | {b['selisih_v2_lama']:+,} |".replace(",", "."))
    L.append(f"| **Total** | **{f(tot['sumber_staging'])}** | **{tot['duplikat_dikecualikan']}** | **{f(tot['postgis'])}** | **{tot['tinggi_kurang_0_1m']}** | **{f(tot['diharapkan_di_tile'])}** | **{f(tot['fitur_v2'])}** | **{f(tot['fitur_lama'])}** | **{tot['selisih_v2_lama']:+,}** |".replace(",", "."))
    L += ["", "Alasan dikeluarkan dari tile: `tinggi < 0,1 m` (qc_flag `tinggi_kurang_0_1m`; tetap di PostGIS). Duplikat dikecualikan: ADR-007 (tidak mendapat ID).", "",
          "## Segitiga", "", f"- Total v2 **{f(tot['segitiga_v2'])}**; tile lama **{f(tot['segitiga_lama'])}**.",
          f"- Pada **{f(pasangan_tot[0])}** bangunan yang cocok satu-ke-satu (pusat ≤ 2 m, timbal balik): lama {f(pasangan_tot[1])} vs v2 {f(pasangan_tot[2])} = **{pasangan_tot[1] / pasangan_tot[2]:.2f}×**.", "",
          "## Kontrak frontend", "", "| Kelurahan | 3D Tiles | region | transform | refine | glb | maks glb (MB) | ≤ 3 MB | EXT_* di semua glb | 6 properti | ID unik | ID = PostGIS | atribut beda |", "|---|---|---|---|---|---:|---:|---|---|---|---|---|---:|"]
    for s in slugs:
        k = kontrak[s]
        L.append(f"| {s} | {k['versi']} | {'ya' if k['region'] else 'TIDAK'} | {'ya' if k['transform'] else 'TIDAK'} | {k['refine']} | {k['glb']} | {k['maks_byte'] / 1048576:.2f} | {'ya' if k['maks_<=3MB'] else 'TIDAK'} | "
                 f"{'ya' if k['ekstensi_di_semua_glb'] else 'TIDAK'} | {'ya' if k['enam_properti'] else 'TIDAK'} | {'ya' if k['id_unik_dalam_kelurahan'] else 'TIDAK'} | {'ya' if k['id_sama_dengan_postgis'] else 'TIDAK'} | {k['atribut_beda_dengan_postgis']} |")
    L += ["", f"- ID unik seluruh kota: {f(hasil['id_unik_seluruh_kota']['unik'])} dari {f(hasil['id_unik_seluruh_kota']['total_fitur'])} fitur (ganda {hasil['id_unik_seluruh_kota']['ganda']}); himpunan ID tile = PostGIS (tinggi ≥ 0,1 m): {hasil['id_tile_sama_dengan_postgis_seluruh_kota']}.",
          "- `jumlah_lantai`/`luas_tapak` kosong disimpan sebagai `noData` (bukan 0). tyler menghilangkan kolom dari tile yang tidak punya satu pun nilai (mis. 6 dari 7 tile Berebas Tengah tanpa `jumlah_lantai`).", "",
          "## qc_flag seluruh kota (core.bangunan)", "", "| Flag | Bangunan |", "|---|---:|"]
    for k_, n in qc_kota.items():
        L.append(f"| {k_} | {f(n)} |")
    (DP / "reports" / "impor_resmi_verifikasi.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({"total": dict(tot), "id_unik": hasil["id_unik_seluruh_kota"], "id_sama_pg": hasil["id_tile_sama_dengan_postgis_seluruh_kota"], "segitiga": {k: v for k, v in hasil["segitiga"].items() if k != "per_kelurahan"}}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
