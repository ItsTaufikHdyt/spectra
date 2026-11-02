"""
report_remote.py — Laporan Markdown + pratinjau PNG untuk fetch_sources.py (Tahap 4).

Tabel: katalog CSW, FeatureType WFS (dari reports/remote_inventory.json), perbandingan
WFS vs GeoJSON lokal, status tiap sumber, dan uji identik jalur lama.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from shapely import make_valid, unary_union  # noqa: E402

from geo_common import REPORTS  # noqa: E402

METRIC_CRS = "EPSG:32650"
COLOR_LOCAL = "#1f4e79"
COLOR_WFS = "#e8590c"


def fmt(x, nd: int = 2) -> str:
    """Angka format id-ID (titik ribuan, koma desimal)."""
    if x is None:
        return "-"
    if isinstance(x, int):
        return f"{x:,}".replace(",", ".")
    s = f"{x:,.{nd}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def write_markdown(report: dict, catalog: list[dict] | None) -> None:
    inv_path = REPORTS / "remote_inventory.json"
    inv = json.loads(inv_path.read_text(encoding="utf-8")) if inv_path.exists() else None
    md = [
        "# Laporan sumber data (fetch_sources.py)",
        "",
        f"Run: `{report['timestamp_utc']}` (UTC). Konfigurasi: `config/sources.yaml`.",
        "",
        "## Status sumber",
        "",
        "| id | tipe | layer | prioritas | status | jumlah | halaman | output | catatan |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for e in report["sumber"]:
        note = e.get("error") or (f"urutan sumbu: {e['urutan_sumbu']} (IoU extent {fmt(e.get('iou_extent_vs_lokal'), 4)})" if e.get("urutan_sumbu") else "")
        md.append(
            f"| `{e['id']}` | {e['tipe']} | {e['layer'] or '-'} | {e['prioritas']} | {e['status']} | "
            f"{fmt(e.get('jumlah', e.get('record')))} | {e.get('halaman', '-')} | `{e.get('output', '-')}` | {note} |"
        )
    md += [
        "",
        "## Uji identik GeoJSON lokal vs jalur lama",
        "",
        "Dibandingkan per fitur, dengan urutan yang sama: geometri (koordinat persis), slug, dan nama kelurahan ternormalisasi",
        "(sungai: nama).",
        "",
        "| sumber | file lama | jumlah (baru / lama) | geometri sama | nama & slug sama | identik |",
        "|---|---|---|---|---|---|",
    ]
    for e in report["sumber"]:
        t = e.get("uji_identik_jalur_lama")
        if t:
            md.append(f"| `{e['id']}` | `{t['file_lama']}` | {t['jumlah'][0]} / {t['jumlah'][1]} | {'ya' if t['geometri_sama'] else 'TIDAK'} | "
                      f"{'ya' if t['nama_slug_sama'] else 'TIDAK'} | **{'ya' if t['identik'] else 'TIDAK'}** |")

    if catalog is not None:
        md += [
            "",
            f"## Katalog CSW ({len(catalog)} record)",
            "",
            "| Judul | Tipe | Layer terkait | Status | id |",
            "|---|---|---|---|---|",
            *(
                f"| {r['judul']} | {r['tipe'] or '-'}{' / ' + r['representasi'] if r['representasi'] else ''} | {len(r['layer'])} | "
                f"{r['status'] or 'tidak diisi'} | `{r['id']}` |"
                for r in sorted(catalog, key=lambda r: r["judul"] or "")
            ),
        ]

    if inv:
        cmp_by_layer = {c["layer"]: c for c in report["perbandingan"]}
        md += [
            "",
            f"## FeatureType WFS ({len(inv['wfs']['feature_types'])})",
            "",
            f"Dari `reports/remote_inventory.json` (inventaris `{inv['wfs']['raw_dir']}`).",
            "",
            "| FeatureType | Jumlah fitur | SRS default | Padanan lokal |",
            "|---|---|---|---|",
            *(
                f"| `{ft['name'].split(':')[-1]}` | {fmt(ft['hits'])} | {(ft['default_crs'] or '-').split('::')[-1]} | "
                f"{(ft['padanan_lokal']['file'] + (' (' + cmp_by_layer[ft['padanan_lokal']['layer']]['status'] + ')' if ft['padanan_lokal']['layer'] in cmp_by_layer else '')) if ft['padanan_lokal'] else '-'} |"
                for ft in inv["wfs"]["feature_types"]
            ),
        ]

    md += [
        "",
        "## Perbandingan WFS vs GeoJSON lokal",
        "",
        "Besaran metrik dihitung di EPSG:32650. Beda simetris = luas (gabungan lokal XOR gabungan WFS) / luas gabungan lokal.",
        f"Status: **sama** bila jumlah sama dan selisih ≤ 0,01%; **beda kecil** bila ≤ 1%; selain itu **beda signifikan**.",
        "",
        "| Layer | Jumlah lokal | Jumlah WFS | Besaran | Lokal | WFS | Selisih (%) | Beda geometri | Geser extent maks. (m) | Status |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in report["perbandingan"]:
        geom = f"Hausdorff {fmt(c['hausdorff_m'], 3)} m" if "hausdorff_m" in c else f"{fmt(c['beda_simetris_persen'], 4)}% ({fmt(c['luas_beda_simetris_m2'], 1)} m²)"
        md.append(
            f"| {c['layer']} | {fmt(c['jumlah_lokal'])} | {fmt(c['jumlah_wfs'])} | {c['besaran']} | {fmt(c['nilai_lokal'], 1)} | "
            f"{fmt(c['nilai_wfs'], 1)} | {fmt(c['selisih_persen'], 4)} | {geom} | {fmt(c['geser_extent_maks_m'])} | **{c['status']}** |"
        )
    md += ["", "Detail nama, kunci, dan atribut:", ""]
    for c in report["perbandingan"]:
        md.append(f"- **{c['layer']}**: fid cocok {c['fid_cocok']}; kunci hanya di lokal: {c['kunci_hanya_lokal'] or 'tidak ada'}; "
                  f"hanya di WFS: {c['kunci_hanya_wfs'] or 'tidak ada'}; kelurahan WFS tanpa padanan slug: {c['kelurahan_wfs_tanpa_padanan'] or 'tidak ada'}; "
                  f"kolom atribut beda nilai (jumlah fitur): {c['atribut_beda_per_kolom'] or 'tidak ada'}; "
                  f"beda tipe saja, mis. \"261\" vs 261: {c['atribut_beda_tipe_saja'] or 'tidak ada'}.")
    md += [
        "",
        "## Determinisme",
        "",
        "File di `processed/sources/` dan `processed/catalog/records.json` tidak memuat timestamp. File yang berubah tiap run hanya",
        "folder `raw/remote/<id>/<timestamp>/` (respons server memuat `timeStamp` / `SearchStatus timestamp`) dan laporan ini",
        "(`timestamp_utc`, path folder raw).",
        "",
    ]
    (REPORTS / "fetch_sources.md").write_text("\n".join(md), encoding="utf-8")


ZOOM_FALLBACK_SLUG = "api_api"  # kelurahan padat RT; dipakai bila tidak ada beda geometri


def write_preview(local, remote, layer: str, comparisons: list[dict]) -> None:
    """Dua panel: seluruh kota dan zoom ke area beda terbesar (atau ke satu kelurahan bila identik)."""
    lm, rm = local.to_crs(METRIC_CRS), remote.to_crs(METRIC_CRS)
    diff = unary_union(make_valid(lm.geometry.values)).symmetric_difference(unary_union(make_valid(rm.geometry.values)))
    parts = sorted(getattr(diff, "geoms", [diff]), key=lambda g: g.area, reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.5), dpi=110)
    for ax in axes:
        lm.boundary.plot(ax=ax, color=COLOR_LOCAL, linewidth=1.4, label="GeoJSON lokal")
        rm.boundary.plot(ax=ax, color=COLOR_WFS, linewidth=0.8, linestyle="--", label="WFS geoportal")
        ax.set_aspect("equal")
        ax.tick_params(labelsize=7)
        ax.set_xlabel("Easting (m, EPSG:32650)", fontsize=8)
        ax.set_ylabel("Northing (m)", fontsize=8)
    c = next((x for x in comparisons if x["layer"] == layer), {})
    axes[0].set_title(f"Batas {layer.upper() if layer == 'rt' else layer}: seluruh kota — lokal {c.get('jumlah_lokal')} vs WFS {c.get('jumlah_wfs')} fitur", fontsize=10)
    if parts and parts[0].area > 0:
        x0, y0, x1, y1 = parts[0].buffer(300).bounds
        axes[1].set_xlim(x0, x1)
        axes[1].set_ylim(y0, y1)
        axes[1].set_title(f"Zoom: area beda terbesar ({parts[0].area:,.0f} m²)".replace(",", "."), fontsize=10)
        axes[0].plot(*parts[0].buffer(300).exterior.xy, color="crimson", linewidth=1)
    else:
        sel = lm[lm["slug"] == ZOOM_FALLBACK_SLUG]
        x0, y0, x1, y1 = (sel if len(sel) else lm).total_bounds
        x0, y0, x1, y1 = x0 - 150, y0 - 150, x1 + 150, y1 + 150
        axes[1].set_xlim(x0, x1)
        axes[1].set_ylim(y0, y1)
        axes[0].plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color="crimson", linewidth=1)
        axes[1].set_title(f"Zoom {ZOOM_FALLBACK_SLUG.replace('_', ' ').title()}: tidak ada beda geometri (garis WFS menimpa lokal)", fontsize=10)
    axes[1].legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(REPORTS / "preview_remote_vs_local.png", metadata={"Software": None})
    plt.close(fig)
