#!/usr/bin/env python3
"""
inventory_remote.py — Inventaris layanan Geoportal Kota Bontang (READ-ONLY, Tahap 1).

Request (semuanya operasi baca):
  WFS : GetCapabilities, DescribeFeatureType (per FeatureType), GetFeature resultType=hits
  CSW : GetCapabilities, GetRecords resultType=hits (ISO 19139), GetRecords halaman 1 (ambil id
        sampel), GetRecordById untuk beberapa sampel
Respons mentah : raw/remote/wfs_geoportal/<ts>/, raw/remote/csw_geoportal/<ts>/
Output         : reports/remote_inventory.md, reports/remote_inventory.json

Jalankan (dari root repo):
    data-pipeline/.venv/bin/python data-pipeline/scripts/inventory_remote.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import REPORTS, write_json  # noqa: E402
from sources.ogc_xml import (  # noqa: E402
    NS,
    parse_csw_search,
    parse_describe_feature_type,
    parse_iso_by_id,
    parse_wfs_capabilities,
    parse_wfs_hits,
)
from sources.remote_http import FetchError, RawRun  # noqa: E402

WFS_URL = "https://geoportal.bontangkota.go.id/geoserver/ows"
CSW_URL = "https://geoportal.bontangkota.go.id/catalogue/csw"
ISO_SCHEMA = "http://www.isotc211.org/2005/gmd"  # nilai resmi pycsw untuk "csw:IsoRecord"
SAMPLE_RECORDS = 3

# Padanan lokal ditetapkan MANUAL dari judul FeatureType (bukan tebakan otomatis).
LOCAL_EQUIVALENT = {
    "geonode:batas_administrasi_kelurahan_0906202604e2ca2ef6fa": ("kelurahan", "raw/geojson/batas-kelurahan.json"),
    "geonode:batas_administrasi_kelurahan_rt_08062026": ("rt", "raw/geojson/batas-rt.json"),
    "geonode:sungai_ln_5k": ("sungai", "raw/geojson/sungai_ln_5k.json"),
}
LOCAL_FILES = (("kelurahan", "raw/geojson/batas-kelurahan.json"), ("rt", "raw/geojson/batas-rt.json"), ("sungai", "raw/geojson/sungai_ln_5k.json"))

log = logging.getLogger("inventory")


def rel(p: Path) -> str:
    return str(p.relative_to(p.parents[3]))  # data-pipeline/raw/remote/<id>/<ts> -> raw/remote/<id>/<ts>


def wfs_inventory() -> dict:
    run = RawRun("wfs_geoportal")
    base = {"service": "WFS", "version": "2.0.0"}
    caps = parse_wfs_capabilities(
        run.fetch(WFS_URL, {"service": "WFS", "acceptversions": "2.0.0", "request": "GetCapabilities"}, "GetCapabilities.xml")
    )
    for ft in caps["feature_types"]:
        short = ft["name"].split(":")[-1]
        ft["attributes"] = ft["hits"] = None
        try:
            ft["attributes"] = parse_describe_feature_type(
                run.fetch(WFS_URL, {**base, "request": "DescribeFeatureType", "typeNames": ft["name"]}, f"DescribeFeatureType_{short}.xsd")
            )
            ft["hits"] = parse_wfs_hits(
                run.fetch(WFS_URL, {**base, "request": "GetFeature", "typeNames": ft["name"], "resultType": "hits"}, f"hits_{short}.xml")
            )
        except (FetchError, ValueError) as err:  # catat lalu lanjut ke FeatureType berikutnya
            log.error("%s gagal: %s", ft["name"], err)
            ft["error"] = str(err)
        layer, local = LOCAL_EQUIVALENT.get(ft["name"], (None, None))
        ft["padanan_lokal"] = {"layer": layer, "file": local} if layer else None
    return {"raw_dir": rel(run.dir), **caps}


def csw_inventory() -> dict:
    run = RawRun("csw_geoportal")
    base = {"service": "CSW", "version": "2.0.2"}
    run.fetch(CSW_URL, {**base, "request": "GetCapabilities"}, "GetCapabilities.xml")
    q = {**base, "request": "GetRecords", "typeNames": "gmd:MD_Metadata", "outputSchema": ISO_SCHEMA, "elementSetName": "full"}
    total = parse_csw_search(run.fetch(CSW_URL, {**q, "resultType": "hits"}, "GetRecords_hits.xml"))["matched"]
    page = parse_csw_search(
        run.fetch(CSW_URL, {**q, "resultType": "results", "startPosition": "1", "maxRecords": str(SAMPLE_RECORDS)}, "GetRecords_sampel.xml")
    )
    samples = []
    for md in page["records"]:
        rid = md.find("gmd:fileIdentifier/gco:CharacterString", NS).text
        body = run.fetch(CSW_URL, {**base, "request": "GetRecordById", "id": rid, "outputSchema": ISO_SCHEMA, "elementSetName": "full"}, f"GetRecordById_{rid}.xml")
        samples.append(parse_iso_by_id(body))
    return {"raw_dir": rel(run.dir), "total_record": total, "sampel": samples}


def write_report(wfs: dict, csw: dict) -> None:
    fts = wfs["feature_types"]
    by_layer = {ft["padanan_lokal"]["layer"]: ft for ft in fts if ft["padanan_lokal"]}
    c = wfs["constraints"]
    md = [
        "# Inventaris Geoportal Kota Bontang (WFS + CSW)",
        "",
        "Akses read-only, tanpa autentikasi. Respons mentah ada di",
        f"`{wfs['raw_dir']}/` dan `{csw['raw_dir']}/` (URL dan parameter tiap request ada di `requests.json`).",
        "",
        "## WFS (GeoServer)",
        "",
        f"- Versi didukung: {', '.join(wfs['versions'])}",
        f"- Operasi yang diiklankan: {', '.join(wfs['operations'])}",
        "- **Yang dipakai pipeline hanya** GetCapabilities, DescribeFeatureType, dan GetFeature. Transaction, LockFeature,",
        "  GetFeatureWithLock, CreateStoredQuery, dan DropStoredQuery diiklankan server, tetapi ditolak oleh",
        "  `sources/remote_http.py` sebelum request dikirim.",
        f"- Paging: ImplementsResultPaging = {c.get('ImplementsResultPaging')}, CountDefault = {c.get('CountDefault')}, "
        f"PagingIsTransactionSafe = {c.get('PagingIsTransactionSafe')}",
        f"- Jumlah FeatureType: {len(fts)}",
        "",
        "| FeatureType | Judul | SRS default | Jumlah fitur | Atribut | Padanan lokal |",
        "|---|---|---|---|---|---|",
        *(
            f"| `{ft['name']}` | {ft['title']} | {(ft['default_crs'] or '-').split('::')[-1]} | "
            f"{ft['hits'] if ft['hits'] is not None else 'gagal'} | {len(ft['attributes'] or [])} | "
            f"{('`' + ft['padanan_lokal']['file'] + '`') if ft['padanan_lokal'] else '-'} |"
            for ft in fts
        ),
        "",
        "EPSG:9480 = SRGI2013 / UTM zone 50N. Bedanya dengan WGS 84 / UTM 50N (EPSG:32650) di bawah 1 m, jadi untuk QC",
        "keduanya diperlakukan setara.",
        "",
        "### Atribut FeatureType yang punya padanan lokal",
        "",
    ]
    for layer, _ in LOCAL_FILES:
        ft = by_layer.get(layer)
        if ft:
            attrs = ", ".join(f"`{a['name']}` ({(a['type'] or '').split(':')[-1]})" for a in ft["attributes"] or [])
            md += [f"- **{layer}** (`{ft['name']}`): {attrs}", ""]
    md += [
        "## CSW (pycsw)",
        "",
        f"- Total record ISO 19139 (`gmd:MD_Metadata`): **{csw['total_record']}**",
        "- Server juga mengiklankan Transaction dan Harvest; keduanya tidak dipakai.",
        "",
        "Sampel GetRecordById:",
        "",
        "| id | Judul | Tipe | bbox WGS84 | Layer terkait (OGC:WMS/WFS) |",
        "|---|---|---|---|---|",
        *(
            f"| `{s['id']}` | {s['judul']} | {s['tipe']} | {[round(v, 4) for v in s['bbox_wgs84']] if s['bbox_wgs84'] else '-'} | "
            f"{', '.join(f'`{n}`' for n in s['layer']) or '-'} |"
            for s in csw["sampel"]
        ),
        "",
        *(f"- Abstrak `{s['id'][:8]}`: {(s['abstrak'] or '-')[:300]}" for s in csw["sampel"]),
        "",
        "## Pencocokan dengan GeoJSON lokal",
        "",
        "| Layer lokal | File lokal | FeatureType WFS | Jumlah fitur WFS |",
        "|---|---|---|---|",
        *(
            f"| {layer} | `{f}` | {('`' + by_layer[layer]['name'] + '`') if layer in by_layer else 'tidak ada'} | "
            f"{by_layer[layer]['hits'] if layer in by_layer else '-'} |"
            for layer, f in LOCAL_FILES
        ),
        "",
        f"FeatureType tanpa padanan lokal ({sum(1 for ft in fts if not ft['padanan_lokal'])}): "
        + ", ".join(f"`{ft['name'].split(':')[-1]}`" for ft in fts if not ft["padanan_lokal"]),
        "",
    ]
    (REPORTS / "remote_inventory.md").write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    wfs = wfs_inventory()
    csw = csw_inventory()
    write_json(REPORTS / "remote_inventory.json", {"wfs": wfs, "csw": csw})
    write_report(wfs, csw)
    print(json.dumps({"feature_types": len(wfs["feature_types"]), "csw_total": csw["total_record"]}))
    return 0 if all(ft["hits"] is not None for ft in wfs["feature_types"]) else 1


if __name__ == "__main__":
    sys.exit(main())
