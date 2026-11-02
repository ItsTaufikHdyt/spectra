#!/usr/bin/env python3
"""
show_data.py — Tampilkan data hasil normalisasi: tabel ringkasan + preview peta statis.

Membaca output skrip lain (jalankan dulu check_geometry.py, normalize_names.py,
reproject_sungai.py). Tidak membaca/menulis raw/.

Output: reports/ringkasan_data.md, reports/preview_kelurahan_rt_sungai.png

Jalankan (dari root repo):
    data-pipeline/.venv/bin/python data-pipeline/scripts/show_data.py
"""

from __future__ import annotations

import collections
import csv
import sys

import matplotlib

matplotlib.use("Agg")  # tanpa layar
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
from shapely.geometry import MultiPolygon  # noqa: E402
from tabulate import tabulate  # noqa: E402

from geo_common import CONFIG, OUT_GEOJSON, REPORTS, geom, norm_key, read_geojson, to_utm  # noqa: E402

KECAMATAN_COLORS = {  # warna isi RT per kecamatan (dibedakan juga oleh legenda)
    "Bontang Utara": "#5B9BD5",
    "Bontang Selatan": "#ED9D4A",
    "Bontang Barat": "#8BC27D",
}
RIVER_COLOR = "#0B4F9C"


def fmt(x, nd: int = 2) -> str:
    """Format angka Indonesia: titik ribuan, koma desimal."""
    if x is None:
        return "-"
    s = f"{float(x):,.{nd}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def load_inputs():
    try:
        kel = read_geojson(OUT_GEOJSON / "batas-kelurahan.norm.geojson")["features"]
        rt = read_geojson(OUT_GEOJSON / "batas-rt.norm.geojson")["features"]
        sungai = read_geojson(OUT_GEOJSON / "sungai_ln.wgs84.geojson")["features"]
        check = read_geojson(REPORTS / "geometry_check.json")
        sungai_rep = read_geojson(REPORTS / "sungai_reproject.json")
    except FileNotFoundError as err:
        print(f"ERROR: {err.filename} belum ada. Jalankan check_geometry.py, normalize_names.py, "
              "reproject_sungai.py terlebih dahulu.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG / "kelurahan_map.csv", encoding="utf-8") as f:
        mapping = {row["nama_geojson"]: row for row in csv.DictReader(f)}
    return kel, rt, sungai, check, sungai_rep, mapping


def problem_indices(check: dict) -> dict[str, set[int]]:
    """Indeks RT bermasalah per jenis (indeks = urutan fitur di batas-rt.json)."""
    overlaps = check["tumpang_tindih"]["dalam_kelurahan"] + check["tumpang_tindih"]["antar_kelurahan"]
    return {
        "invalid": {x["index"] for x in check["validitas"]["batas-rt.json"]["daftar"]},
        "tumpang_tindih": {x[s]["index"] for x in overlaps for s in ("a", "b")},
        "duplikat": {i for g in check["duplikat_grup"] for i in g["index"]},
        "keluar_induk": {x["index"] for x in check["rt_dalam_induk"]["daftar_keluar"]},
    }


def tables(kel, rt, check, sungai_rep, mapping) -> list[tuple[str, list[str], list[list]]]:
    area = {norm_key(x["kelurahan"]): x for x in check["luas_kelurahan"]["per_kelurahan"]}
    rt_count = collections.Counter(f["properties"]["slug"] for f in rt)

    t1 = []
    for f in sorted(kel, key=lambda f: f["properties"]["slug"] or ""):
        p = f["properties"]
        a = area[norm_key(p["wadmkd"])]
        t1.append([
            p["wadmkd"], p["nama_normal"], p["slug"], rt_count[p["slug"]],
            fmt(a["luaswh_ha"]), fmt(a["luas_utm_ha"]), fmt(a["selisih_persen_vs_utm"], 3),
            mapping[p["wadmkd"]]["status_cocok"],
        ])

    probs = problem_indices(check)
    any_prob = set().union(*probs.values())
    by_kec = collections.defaultdict(lambda: collections.Counter())
    for i, f in enumerate(rt):
        p = f["properties"]
        c = by_kec[p["kecamatan"]]
        c["rt"] += 1
        c["pulau"] += p["is_pulau"]
        for k, s in probs.items():
            c[k] += i in s
        c["bermasalah"] += i in any_prob
    t2 = [[k, c["rt"], c["pulau"], c["invalid"], c["tumpang_tindih"], c["duplikat"], c["keluar_induk"], c["bermasalah"]]
          for k, c in sorted(by_kec.items())]
    tot = [sum(row[i] for row in t2) for i in range(1, 8)]
    t2.append(["Total", *tot])

    t3 = [
        [g["kelurahan"].title(), g["rt"], g["jumlah_poligon"], g["keterangan"], g["status"],
         fmt(g["jarak_min_m"], 1), fmt(g["jarak_maks_m"], 1)]
        for g in check["duplikat_grup"]
    ]

    t4 = [
        [x["nama"], x["id"], fmt(x["panjang_km_atribut"], 3), fmt(x["panjang_utm_m"] / 1000, 3),
         fmt(x["selisih_vs_panjang_m_persen"], 3), fmt(x["persen_panjang_di_dalam_batas_kota"], 1),
         fmt(x["sinuositas_bagian_utama"], 3),
         "; ".join(x["catatan"]) or "-"]
        for x in sungai_rep["fitur"]
    ]

    return [
        ("Tabel 1 — 15 kelurahan (luas: luaswh vs geometri planar UTM 50N)",
         ["Nama asli", "Nama normal", "Slug", "Jumlah RT", "Luas luaswh (ha)", "Luas geometri (ha)", "Selisih (%)", "Status cocok"], t1),
        ("Tabel 2 — RT per kecamatan (bermasalah = invalid / tumpang tindih > 0,1 m² / duplikat / keluar induk)",
         ["Kecamatan", "RT", "RT pulau", "Invalid", "Tumpang tindih", "Duplikat", "Keluar induk", "RT bermasalah (unik)"], t2),
        ("Tabel 3 — 10 grup RT duplikat (kelurahan, nomor RT)",
         ["Kelurahan", "RT", "Poligon", "Keterangan", "Status pasangan", "Jarak min (m)", "Jarak maks (m)"], t3),
        ("Tabel 4 — 5 fitur sungai (panjang dihitung ulang di UTM 50N)",
         ["Nama", "id", "Panjang atribut (km)", "Panjang hitung (km)", "Selisih (%)", "Di dalam batas kota (%)", "Sinuositas", "Catatan"], t4),
    ]


# --------------------------------------------------------------------------- #
# Preview peta
# --------------------------------------------------------------------------- #
def plot_polygon(ax, g, **kw):
    for part in (g.geoms if isinstance(g, MultiPolygon) else [g]):
        x, y = part.exterior.xy
        ax.fill(x, y, **kw)


def outline(ax, g, **kw):
    for part in (g.geoms if isinstance(g, MultiPolygon) else [g]):
        x, y = part.exterior.xy
        ax.plot(x, y, **kw)
        for h in part.interiors:
            hx, hy = h.xy
            ax.plot(hx, hy, **kw)


def draw_preview(kel, rt, sungai, path):
    fig, ax = plt.subplots(figsize=(11, 12), dpi=150)
    ax.set_facecolor("#EAF2F8")  # laut/latar

    for f in rt:
        p = f["properties"]
        g = geom(f)
        color = KECAMATAN_COLORS.get(p["kecamatan"], "#BBBBBB")
        plot_polygon(ax, g, facecolor=color, edgecolor="white", linewidth=0.25, alpha=0.55,
                     hatch="////" if p["is_pulau"] else None)
    for f in kel:
        outline(ax, geom(f), color="#1E1E1E", linewidth=1.3)

    for f in sungai:
        g = geom(f)
        dashed = str(f["properties"].get("nama", "")).startswith("Drainase")
        for line in getattr(g, "geoms", [g]):
            x, y = line.xy
            ax.plot(x, y, color=RIVER_COLOR, linewidth=1.6, linestyle="--" if dashed else "-", zorder=5)

    halo = [pe.withStroke(linewidth=2.5, foreground="white")]
    for f in kel:
        g = geom(f)
        main = max(getattr(g, "geoms", [g]), key=lambda pp: to_utm(pp).area)
        pt = main.representative_point()
        ax.text(pt.x, pt.y, f["properties"]["nama_normal"], fontsize=7.5, ha="center", va="center",
                weight="bold", color="#1E1E1E", path_effects=halo, zorder=6)

    handles = [Patch(facecolor=c, edgecolor="white", alpha=0.55, label=f"RT — Kec. {k}") for k, c in KECAMATAN_COLORS.items()]
    handles += [
        Patch(facecolor="white", edgecolor="#555555", hatch="////", label="RT pulau (is_pulau)"),
        Line2D([0], [0], color="#1E1E1E", linewidth=1.3, label="Batas kelurahan"),
        Line2D([0], [0], color=RIVER_COLOR, linewidth=1.6, label="Sungai"),
        Line2D([0], [0], color=RIVER_COLOR, linewidth=1.6, linestyle="--", label="Drainase (ditandai)"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=8, framealpha=0.95)
    ax.set_aspect("equal")  # dekat ekuator: 1° bujur ≈ 1° lintang
    comma = FuncFormatter(lambda v, _pos: f"{v:.3f}".replace(".", ","))  # koma desimal
    ax.xaxis.set_major_formatter(comma)
    ax.yaxis.set_major_formatter(comma)
    ax.set_xlabel("Bujur (°BT)")
    ax.set_ylabel("Lintang (°LU)")
    ax.set_title("Kota Bontang — batas kelurahan, RT, dan sungai (WGS84)\n"
                 "Sumber: data-pipeline/processed/geojson/*.norm.geojson, sungai_ln.wgs84.geojson", fontsize=10)
    ax.grid(color="white", linewidth=0.5)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, metadata={"Software": None})  # tanpa metadata versi -> hash stabil
    plt.close(fig)


def main() -> int:
    kel, rt, sungai, check, sungai_rep, mapping = load_inputs()
    md = ["# Ringkasan data GeoJSON — Kota Bontang", "",
          "Dibuat oleh `data-pipeline/scripts/show_data.py`. Angka dalam format Indonesia.", ""]
    for title, headers, rows in tables(kel, rt, check, sungai_rep, mapping):
        print(f"\n{title}\n" + tabulate(rows, headers=headers, tablefmt="simple", disable_numparse=True))
        md += [f"## {title}", "", tabulate(rows, headers=headers, tablefmt="github", disable_numparse=True), ""]
    png = REPORTS / "preview_kelurahan_rt_sungai.png"
    draw_preview(kel, rt, sungai, png)
    md += ["## Preview", "", "![Preview](preview_kelurahan_rt_sungai.png)", ""]
    (REPORTS / "ringkasan_data.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nDitulis: {REPORTS / 'ringkasan_data.md'}\nDitulis: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
