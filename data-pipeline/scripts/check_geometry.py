#!/usr/bin/env python3
"""
check_geometry.py — QC geometri batas kelurahan, batas RT, dan sungai (read-only).

Pemeriksaan:
  1. Validitas geometri (is_valid + alasan) dan ring yang tidak tertutup di data mentah.
  2. Tumpang tindih RT dalam kelurahan yang sama (irisan > 0,1 m²).
  3. Tumpang tindih RT antar kelurahan.
  4. RT di dalam poligon kelurahan induknya (proporsi luas di dalam induk).
  5. Pasangan (kelurahan, nomor RT) duplikat: beririsan / berdampingan / terpisah + jarak.
  6. Selisih luas Guntung (luaswh vs geometri): bagian multipolygon, hole, hipotesis.
  + Bukti status pulau: jarak tiap RT ke daratan utama, dikelompokkan per `keterangan`.

Output: data-pipeline/reports/geometry_check.json dan geometry_check.md

Jalankan (dari root repo):
    data-pipeline/.venv/bin/python data-pipeline/scripts/check_geometry.py
"""

from __future__ import annotations

import collections
import sys

from shapely import STRtree, unary_union
from shapely.geometry import MultiPolygon, Polygon
from shapely.validation import explain_validity

from geo_common import (
    KELURAHAN_FILE,
    REPORTS,
    RT_FILE,
    SUNGAI_FILE,
    geodesic_area_m2,
    geom,
    norm_key,
    r,
    read_geojson,
    to_utm,
    valid_or_fixed,
    write_json,
)

MIN_OVERLAP_M2 = 0.1  # ambang irisan yang dilaporkan
ADJACENT_M = 1.0  # jarak <= 1 m dianggap berdampingan (bersinggungan)
INSIDE_FRACTION = 0.99  # RT dianggap "di dalam induk" bila >= 99% luasnya di dalam
REVIEW_KELURAHAN = "GUNTUNG"


# --------------------------------------------------------------------------- #
# 1. Validitas
# --------------------------------------------------------------------------- #
def unclosed_rings(geometry: dict) -> int:
    """Hitung ring yang titik awal != titik akhir di koordinat MENTAH (shapely menutupnya diam-diam)."""
    t, coords = geometry["type"], geometry["coordinates"]
    polys = [coords] if t == "Polygon" else coords if t == "MultiPolygon" else []
    return sum(1 for poly in polys for ring in poly if ring and ring[0] != ring[-1])


def validity(features: list[dict], label_fn) -> dict:
    reasons = collections.Counter()
    invalid = []
    unclosed_total = 0
    for i, f in enumerate(features):
        g = geom(f)
        unclosed = unclosed_rings(f["geometry"]) if f["geometry"]["type"].endswith("Polygon") else 0
        unclosed_total += unclosed
        if not g.is_valid or unclosed:
            why = explain_validity(g) if not g.is_valid else "Valid"
            kind = why.split("[")[0].strip()
            if unclosed:
                kind = f"{kind}; Ring tidak tertutup ({unclosed})" if kind != "Valid" else f"Ring tidak tertutup ({unclosed})"
            reasons[kind] += 1
            invalid.append({"index": i, "label": label_fn(f), "alasan": why, "jenis": kind})
    return {
        "jumlah": len(features),
        "tidak_valid": len(invalid),
        "ring_tidak_tertutup": unclosed_total,
        "per_jenis": dict(sorted(reasons.items())),
        "daftar": invalid,
    }


# --------------------------------------------------------------------------- #
# 2–3. Tumpang tindih RT
# --------------------------------------------------------------------------- #
def rt_overlaps(rt_utm: list, rt_props: list[dict]) -> tuple[list, list]:
    tree = STRtree(rt_utm)
    left, right = tree.query(rt_utm, predicate="intersects")
    same, cross = [], []
    for i, j in sorted({(int(a), int(b)) for a, b in zip(left, right) if a < b}):
        area = rt_utm[i].intersection(rt_utm[j]).area
        if area <= MIN_OVERLAP_M2:
            continue
        pi, pj = rt_props[i], rt_props[j]
        item = {
            "a": {"index": i, "kelurahan": pi["kelurahan"], "rt": pi["rt"]},
            "b": {"index": j, "kelurahan": pj["kelurahan"], "rt": pj["rt"]},
            "luas_irisan_m2": r(area, 2),
            "persen_dari_rt_terkecil": r(100 * area / min(rt_utm[i].area, rt_utm[j].area), 2),
        }
        (same if norm_key(pi["kelurahan"]) == norm_key(pj["kelurahan"]) else cross).append(item)
    return same, cross


# --------------------------------------------------------------------------- #
# 4. RT di dalam kelurahan induk
# --------------------------------------------------------------------------- #
def containment(rt_utm, rt_props, kel_utm_by_key) -> dict:
    rows, no_parent = [], []
    for i, (g, p) in enumerate(zip(rt_utm, rt_props)):
        parent = kel_utm_by_key.get(norm_key(p["kelurahan"]))
        if parent is None:
            no_parent.append({"index": i, "kelurahan": p["kelurahan"], "rt": p["rt"]})
            continue
        frac = g.intersection(parent).area / g.area if g.area else 0.0
        rows.append((i, p, frac, g.area))
    outside = [
        {
            "index": i,
            "kelurahan": p["kelurahan"],
            "rt": p["rt"],
            "persen_di_dalam_induk": r(100 * frac, 2),
            "luas_di_luar_m2": r((1 - frac) * area, 1),
        }
        for i, p, frac, area in rows
        if frac < INSIDE_FRACTION
    ]
    return {
        "ambang_persen_di_dalam": INSIDE_FRACTION * 100,
        "jumlah_dicek": len(rows),
        "keluar_induk": len(outside),
        "proporsi_keluar_persen": r(100 * len(outside) / len(rows), 2) if rows else 0.0,
        "tanpa_induk": no_parent,
        "daftar_keluar": sorted(outside, key=lambda x: x["persen_di_dalam_induk"]),
    }


# --------------------------------------------------------------------------- #
# 5. Duplikat (kelurahan, RT)
# --------------------------------------------------------------------------- #
def duplicates(rt_utm, rt_props) -> list[dict]:
    groups = collections.defaultdict(list)
    for i, p in enumerate(rt_props):
        groups[(norm_key(p["kelurahan"]), str(p["rt"]))].append(i)
    out = []
    for (kel, rt), idx in sorted(groups.items()):
        if len(idx) < 2:
            continue
        for a_pos, a in enumerate(idx):
            for b in idx[a_pos + 1 :]:
                ga, gb = rt_utm[a], rt_utm[b]
                inter = ga.intersection(gb).area
                dist = ga.distance(gb)
                if inter > MIN_OVERLAP_M2:
                    status = "beririsan"
                elif dist <= ADJACENT_M:
                    status = "berdampingan"
                else:
                    status = "terpisah"
                out.append(
                    {
                        "kelurahan": rt_props[a]["kelurahan"],
                        "rt": rt,
                        "index_a": a,
                        "index_b": b,
                        "keterangan_a": rt_props[a].get("keterangan"),
                        "keterangan_b": rt_props[b].get("keterangan"),
                        "luas_a_m2": r(ga.area, 1),
                        "luas_b_m2": r(gb.area, 1),
                        "status": status,
                        "luas_irisan_m2": r(inter, 2),
                        "jarak_m": r(dist, 1),
                        "jarak_centroid_m": r(ga.centroid.distance(gb.centroid), 1),
                    }
                )
    return out


def duplicate_groups(pairs: list[dict], rt_props) -> list[dict]:
    """Ringkas pasangan duplikat per grup (kelurahan, RT): satu RT bisa terdiri dari banyak pulau."""
    groups = collections.defaultdict(list)
    for p in pairs:
        groups[(p["kelurahan"], p["rt"])].append(p)
    out = []
    for (kel, rt), ps in sorted(groups.items()):
        idx = sorted({p["index_a"] for p in ps} | {p["index_b"] for p in ps})
        statuses = collections.Counter(p["status"] for p in ps)
        out.append(
            {
                "kelurahan": kel,
                "rt": rt,
                "jumlah_poligon": len(idx),
                "jumlah_pasangan": len(ps),
                "keterangan": " / ".join(rt_props[i].get("keterangan") or "(kosong)" for i in idx),
                "status": ", ".join(f"{k} {v}" for k, v in sorted(statuses.items())),
                "jarak_min_m": min(p["jarak_m"] for p in ps),
                "jarak_maks_m": max(p["jarak_m"] for p in ps),
                "index": idx,
            }
        )
    return out


# --------------------------------------------------------------------------- #
# 6. Investigasi luas kelurahan (khususnya Guntung)
# --------------------------------------------------------------------------- #
def polygons_of(g) -> list[Polygon]:
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def area_review(kel_feats, rt_union_ha: dict[str, float]) -> dict:
    rows = []
    detail = None
    for f in kel_feats:
        p = f["properties"]
        g = geom(f)
        g_utm = to_utm(g)
        geo_ha = geodesic_area_m2(g) / 1e4
        utm_ha = g_utm.area / 1e4
        luaswh = float(p["luaswh"])
        rows.append(
            {
                "kelurahan": p["wadmkd"],
                "luaswh_ha": r(luaswh, 2),
                "luas_geodesik_ha": r(geo_ha, 2),
                "luas_utm_ha": r(utm_ha, 2),
                "selisih_persen_vs_geodesik": r(100 * (luaswh - geo_ha) / geo_ha, 3),
                "luas_gabungan_rt_ha": r(rt_union_ha.get(norm_key(p["wadmkd"]), 0.0), 2),
                "cakupan_rt_persen": r(100 * rt_union_ha.get(norm_key(p["wadmkd"]), 0.0) / utm_ha, 2) if utm_ha else 0.0,
                "jumlah_bagian": len(polygons_of(g)),
                "jumlah_hole": sum(len(pp.interiors) for pp in polygons_of(g)),
            }
        )
        if norm_key(p["wadmkd"]) == REVIEW_KELURAHAN:
            # Hipotesis dihitung PLANAR UTM, karena di kelurahan lain luaswh = luas UTM.
            parts = sorted(
                (
                    {
                        "luas_utm_ha": r(pu.area / 1e4, 3),
                        "luas_geodesik_ha": r(geodesic_area_m2(pp) / 1e4, 3),
                        "jumlah_hole": len(pu.interiors),
                        "luas_hole_ha": r(sum(Polygon(h).area for h in pu.interiors) / 1e4, 3),
                    }
                    for pp, pu in zip(polygons_of(g), polygons_of(g_utm))
                ),
                key=lambda x: -x["luas_utm_ha"],
            )
            total = sum(x["luas_utm_ha"] for x in parts)
            largest = parts[0]["luas_utm_ha"]
            holes = sum(x["luas_hole_ha"] for x in parts)
            candidates = {
                "seluruh_geometri_utm": total,
                "hanya_bagian_terbesar_utm": largest,
                "seluruh_geometri_tanpa_mengurangi_hole_utm": total + holes,
                "seluruh_geometri_geodesik": geo_ha,
                "gabungan_poligon_rt_utm": rt_union_ha.get(REVIEW_KELURAHAN, 0.0),
            }
            ranked = sorted(
                (
                    {"hipotesis": k, "luas_ha": r(v, 3), "selisih_dengan_luaswh_persen": r(100 * (luaswh - v) / v, 3)}
                    for k, v in candidates.items()
                ),
                key=lambda x: abs(x["selisih_dengan_luaswh_persen"]),
            )
            detail = {
                "kelurahan": p["wadmkd"],
                "luaswh_ha": r(luaswh, 3),
                "bagian": parts,
                "luas_bagian_kecil_ha": r(total - largest, 3),
                "hipotesis_urut_terdekat": ranked,
            }
    others = [x["selisih_persen_vs_geodesik"] for x in rows if norm_key(x["kelurahan"]) != REVIEW_KELURAHAN]
    # luaswh dianggap = luas planar UTM bila selisihnya < 0,01%.
    same_as_utm = [x["kelurahan"] for x in rows if abs(x["luaswh_ha"] - x["luas_utm_ha"]) / x["luas_utm_ha"] < 1e-4]
    for x in rows:
        x["selisih_persen_vs_utm"] = r(100 * (x["luaswh_ha"] - x["luas_utm_ha"]) / x["luas_utm_ha"], 3)
    return {
        "per_kelurahan": rows,
        "median_selisih_persen_kelurahan_lain": r(sorted(others)[len(others) // 2], 3) if others else None,
        "luaswh_sama_dengan_utm": same_as_utm,
        "kesimpulan_definisi_luaswh": (
            f"luaswh = luas planar UTM 50N untuk {len(same_as_utm)} dari {len(rows)} kelurahan "
            "(selisih < 0,01%); selisih ~-0,07% terhadap geodesik hanyalah faktor skala UTM."
        ),
        "investigasi": detail,
    }


def rt_area_attribute(rt_utm, rt_props) -> dict:
    """Bandingkan atribut `luas` RT (ha) dengan luas geometri UTM."""
    rows = []
    for i, (g, p) in enumerate(zip(rt_utm, rt_props)):
        geo = g.area / 1e4
        attr = float(p.get("luas") or 0)
        pct = 100 * (attr - geo) / geo if geo else 0.0
        rows.append({"index": i, "kelurahan": p["kelurahan"], "rt": p["rt"], "luas_atribut_ha": r(attr, 3), "luas_geometri_ha": r(geo, 3), "selisih_persen": r(pct, 2)})
    off = [x for x in rows if abs(x["selisih_persen"]) > 1]
    return {
        "ambang_persen": 1,
        "jumlah_beda": len(off),
        "jumlah_dicek": len(rows),
        "selisih_maks_persen": max((abs(x["selisih_persen"]) for x in rows), default=0.0),
        "daftar_beda_terbesar": sorted(off, key=lambda x: -abs(x["selisih_persen"]))[:25],
    }


def rt_union_area_ha(rt_utm, rt_props) -> dict[str, float]:
    """Luas gabungan poligon RT per kelurahan (UTM, ha) — irisan antar-RT tidak dihitung ganda."""
    by_kel = collections.defaultdict(list)
    for g, p in zip(rt_utm, rt_props):
        by_kel[norm_key(p["kelurahan"])].append(g)
    return {k: unary_union(v).area / 1e4 for k, v in by_kel.items()}


# --------------------------------------------------------------------------- #
# Bukti pulau: jarak RT ke daratan utama
# --------------------------------------------------------------------------- #
def island_evidence(rt_utm, rt_props) -> dict:
    union = unary_union(rt_utm)
    mainland = max(polygons_of(union), key=lambda pp: pp.area)
    per_ket = collections.defaultdict(list)
    for g, p in zip(rt_utm, rt_props):
        per_ket[p.get("keterangan") or "(kosong)"].append(g.distance(mainland))
    return {
        "catatan": "Daratan utama = bagian terbesar dari gabungan seluruh RT. Jarak 0 = menyatu dengan daratan.",
        "per_keterangan": [
            {
                "keterangan": k,
                "jumlah_rt": len(v),
                "rt_terpisah_dari_daratan": sum(1 for d in v if d > ADJACENT_M),
                "jarak_min_m": r(min(v), 1),
                "jarak_maks_m": r(max(v), 1),
            }
            for k, v in sorted(per_ket.items())
        ],
    }


# --------------------------------------------------------------------------- #
# Laporan
# --------------------------------------------------------------------------- #
def md_table(rows: list[dict], cols: list[str]) -> str:
    if not rows:
        return "_(tidak ada)_\n"
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |\n" for row in rows)


def to_markdown(rep: dict) -> str:
    v = rep["validitas"]
    lines = [
        "# Laporan QC Geometri — batas kelurahan, batas RT, sungai",
        "",
        "Dibuat oleh `data-pipeline/scripts/check_geometry.py` (read-only terhadap `raw/`).",
        "Hitungan metrik di EPSG:32650 (UTM 50N); luas kelurahan juga geodesik WGS84.",
        "",
        "## 1. Validitas geometri",
        "",
        md_table(
            [
                {"file": k, "fitur": x["jumlah"], "tidak valid": x["tidak_valid"], "ring tidak tertutup": x["ring_tidak_tertutup"], "per jenis": x["per_jenis"] or "-"}
                for k, x in v.items()
            ],
            ["file", "fitur", "tidak valid", "ring tidak tertutup", "per jenis"],
        ),
    ]
    for k, x in v.items():
        if x["daftar"]:
            lines += [f"**{k}** — geometri bermasalah:", "", md_table(x["daftar"], ["index", "label", "jenis", "alasan"])]
    o = rep["tumpang_tindih"]
    lines += [
        f"## 2. Tumpang tindih RT dalam kelurahan yang sama (> {MIN_OVERLAP_M2} m²): {len(o['dalam_kelurahan'])} pasangan",
        "",
        md_table(
            [{**x, "a": f"{x['a']['kelurahan']} RT {x['a']['rt']} (#{x['a']['index']})", "b": f"{x['b']['kelurahan']} RT {x['b']['rt']} (#{x['b']['index']})"} for x in o["dalam_kelurahan"]],
            ["a", "b", "luas_irisan_m2", "persen_dari_rt_terkecil"],
        ),
        f"## 3. Tumpang tindih RT antar kelurahan (> {MIN_OVERLAP_M2} m²): {len(o['antar_kelurahan'])} pasangan",
        "",
        md_table(
            [{**x, "a": f"{x['a']['kelurahan']} RT {x['a']['rt']} (#{x['a']['index']})", "b": f"{x['b']['kelurahan']} RT {x['b']['rt']} (#{x['b']['index']})"} for x in o["antar_kelurahan"]],
            ["a", "b", "luas_irisan_m2", "persen_dari_rt_terkecil"],
        ),
    ]
    c = rep["rt_dalam_induk"]
    lines += [
        "## 4. RT di dalam kelurahan induk",
        "",
        f"- Dicek: {c['jumlah_dicek']} RT; keluar induk (< {c['ambang_persen_di_dalam']:g}% luas di dalam): "
        f"**{c['keluar_induk']} ({c['proporsi_keluar_persen']}%)**; tanpa induk: {len(c['tanpa_induk'])}.",
        "",
        md_table(c["daftar_keluar"], ["index", "kelurahan", "rt", "persen_di_dalam_induk", "luas_di_luar_m2"]),
        f"## 5. RT duplikat: {len(rep['duplikat_grup'])} grup (kelurahan, RT), {len(rep['duplikat'])} pasangan",
        "",
        f"Status per pasangan: beririsan (irisan > {MIN_OVERLAP_M2} m²), berdampingan (jarak ≤ {ADJACENT_M:g} m), terpisah.",
        "",
        "### Ringkasan per grup",
        "",
        md_table(rep["duplikat_grup"], ["kelurahan", "rt", "jumlah_poligon", "jumlah_pasangan", "keterangan", "status", "jarak_min_m", "jarak_maks_m"]),
        "### Rincian per pasangan",
        "",
        md_table(rep["duplikat"], ["kelurahan", "rt", "index_a", "index_b", "keterangan_a", "keterangan_b", "status", "luas_irisan_m2", "jarak_m", "jarak_centroid_m"]),
    ]
    a = rep["luas_kelurahan"]
    inv = a["investigasi"]
    lines += [
        "## 6. Luas kelurahan & investigasi Guntung",
        "",
        md_table(a["per_kelurahan"], ["kelurahan", "luaswh_ha", "luas_utm_ha", "luas_geodesik_ha", "luas_gabungan_rt_ha", "cakupan_rt_persen", "selisih_persen_vs_utm", "selisih_persen_vs_geodesik", "jumlah_bagian", "jumlah_hole"]),
        f"**{a['kesimpulan_definisi_luaswh']}** Tidak sama dengan UTM: "
        f"{sorted(set(x['kelurahan'] for x in a['per_kelurahan']) - set(a['luaswh_sama_dengan_utm'])) or 'tidak ada'}.",
        "",
    ]
    if inv:
        lines += [
            f"### {inv['kelurahan']}: luaswh = {inv['luaswh_ha']} ha, luas bagian kecil (selain bagian terbesar) = {inv['luas_bagian_kecil_ha']} ha",
            "",
            md_table(inv["bagian"], ["luas_utm_ha", "luas_geodesik_ha", "jumlah_hole", "luas_hole_ha"]),
            "Hipotesis (urut dari yang paling dekat dengan luaswh):",
            "",
            md_table(inv["hipotesis_urut_terdekat"], ["hipotesis", "luas_ha", "selisih_dengan_luaswh_persen"]),
        ]
    la = rep["luas_rt_atribut"]
    lines += [
        "## 7. Atribut `luas` RT vs luas geometri (UTM)",
        "",
        f"- {la['jumlah_beda']} dari {la['jumlah_dicek']} RT berbeda > {la['ambang_persen']}%; selisih maksimum {la['selisih_maks_persen']}%.",
        f"- Cakupan gabungan RT terhadap poligon kelurahan: {min(x['cakupan_rt_persen'] for x in a['per_kelurahan'])}–{max(x['cakupan_rt_persen'] for x in a['per_kelurahan'])}% "
        "(lihat bagian 6), jadi poligon kelurahan praktis = gabungan RT. Atribut `luas` RT kemungkinan berasal dari versi batas sebelumnya.",
        "",
        "25 selisih terbesar:",
        "",
        md_table(la["daftar_beda_terbesar"], ["index", "kelurahan", "rt", "luas_atribut_ha", "luas_geometri_ha", "selisih_persen"]),
    ]
    lines += [
        "## Bukti status pulau (jarak RT ke daratan utama)",
        "",
        rep["bukti_pulau"]["catatan"],
        "",
        md_table(rep["bukti_pulau"]["per_keterangan"], ["keterangan", "jumlah_rt", "rt_terpisah_dari_daratan", "jarak_min_m", "jarak_maks_m"]),
    ]
    return "\n".join(lines)


def main() -> int:
    kel = read_geojson(KELURAHAN_FILE)["features"]
    rt = read_geojson(RT_FILE)["features"]
    sungai = read_geojson(SUNGAI_FILE)["features"]

    rt_props = [f["properties"] for f in rt]
    # Hitungan metrik: UTM; geometri invalid diperbaiki SEMENTARA di memori (bukan di data).
    rt_utm = [valid_or_fixed(to_utm(geom(f))) for f in rt]
    kel_utm_by_key = {norm_key(f["properties"]["wadmkd"]): valid_or_fixed(to_utm(geom(f))) for f in kel}

    same, cross = rt_overlaps(rt_utm, rt_props)
    dup_pairs = duplicates(rt_utm, rt_props)
    report = {
        "validitas": {
            "batas-kelurahan.json": validity(kel, lambda f: f["properties"]["wadmkd"]),
            "batas-rt.json": validity(rt, lambda f: f"{f['properties']['kelurahan']} RT {f['properties']['rt']}"),
            "sungai_ln_5k.json": validity(sungai, lambda f: f["properties"]["nama"]),
        },
        "tumpang_tindih": {"dalam_kelurahan": same, "antar_kelurahan": cross},
        "rt_dalam_induk": containment(rt_utm, rt_props, kel_utm_by_key),
        "duplikat_grup": duplicate_groups(dup_pairs, rt_props),
        "duplikat": dup_pairs,
        "luas_kelurahan": area_review(kel, rt_union_area_ha(rt_utm, rt_props)),
        "luas_rt_atribut": rt_area_attribute(rt_utm, rt_props),
        "bukti_pulau": island_evidence(rt_utm, rt_props),
    }

    write_json(REPORTS / "geometry_check.json", report)
    (REPORTS / "geometry_check.md").write_text(to_markdown(report) + "\n", encoding="utf-8")

    v = report["validitas"]
    print("Validitas:", {k: x["tidak_valid"] for k, x in v.items()})
    print(f"Tumpang tindih RT: dalam kelurahan={len(same)}, antar kelurahan={len(cross)}")
    c = report["rt_dalam_induk"]
    print(f"RT keluar induk: {c['keluar_induk']}/{c['jumlah_dicek']} ({c['proporsi_keluar_persen']}%)")
    print(f"RT duplikat: {len(report['duplikat_grup'])} grup, {len(report['duplikat'])} pasangan")
    print(f"Ditulis: {REPORTS / 'geometry_check.md'} dan .json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
