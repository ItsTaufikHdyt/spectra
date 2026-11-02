"""
geoportal.py — Logika WFS/CSW untuk backend, memakai ulang adapter data-pipeline/scripts/sources/.

Semua request lewat remote_http.get (hanya operasi baca) dengan url_guard=check_url (SSRF),
timeout, retry 3x, dan batas ukuran respons.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from sources.base import write_geojson
from sources.csw import Csw
from sources.ogc_xml import parse_describe_feature_type, parse_wfs_capabilities, parse_wfs_hits, parse_wms_layer_names
from sources.remote_http import FetchError, ResponseTooLarge, get
from sources.wfs import Wfs

from .guard import UrlDitolak, check_url

MAX_FITUR = int(os.environ.get("SPECTRA_MAX_FITUR", "20000"))
MAX_BYTES = int(os.environ.get("SPECTRA_MAX_BYTES", str(50 * 1024 * 1024)))
TIMEOUT_S = 30
OUTPUT_SRS = "urn:ogc:def:crs:EPSG::4326"
HTTP = {"timeout": TIMEOUT_S, "max_bytes": MAX_BYTES, "url_guard": check_url}


class GeoportalError(Exception):
    """Kesalahan yang pesannya siap ditampilkan; status = kode HTTP respons backend."""

    def __init__(self, status: int, pesan: str, **extra):
        super().__init__(pesan)
        self.status, self.pesan, self.extra = status, pesan, extra


def explain(err: Exception) -> GeoportalError:
    """Terjemahkan error teknis menjadi pesan Bahasa Indonesia yang jelas."""
    if isinstance(err, GeoportalError):
        return err
    if isinstance(err, UrlDitolak):
        return GeoportalError(400, str(err))
    if isinstance(err, ResponseTooLarge):
        return GeoportalError(413, f"Respons geoportal lebih dari {MAX_BYTES // 1024 // 1024} MB. Gunakan tampilan WMS.", saran="wms")
    if isinstance(err, FetchError):
        if err.status is None:
            return GeoportalError(504, f"Server geoportal tidak merespons (batas {TIMEOUT_S} detik, 3 percobaan).")
        return GeoportalError(502, f"Geoportal menolak permintaan (HTTP {err.status}).")
    if isinstance(err, ET.ParseError):
        return GeoportalError(502, "Respons geoportal tidak dapat dibaca (bukan XML WFS/CSW yang valid).")
    return GeoportalError(502, f"Gagal memproses data geoportal: {err}")


def _get(base: str, params: dict) -> bytes:
    return get(base, params, **HTTP)[0]


def base_of(url: str) -> str:
    p = urlsplit(url.strip())
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def wms_base(wfs_base: str) -> str:
    """GeoServer: /ows melayani WFS dan WMS; /wfs -> /wms."""
    return wfs_base[: -len("/wfs")] + "/wms" if wfs_base.endswith("/wfs") else wfs_base


def count_features(wfs_url: str, typename: str) -> int | None:
    body = _get(wfs_url, {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": typename, "resultType": "hits"})
    return parse_wfs_hits(body)


def wms_layers(wfs_url: str) -> set[str] | None:
    """Nama layer WMS di endpoint yang sama, atau None bila WMS tidak bisa diperiksa."""
    try:
        return parse_wms_layer_names(_get(wms_base(wfs_url), {"service": "WMS", "request": "GetCapabilities"}))
    except (FetchError, ET.ParseError, UrlDitolak):
        return None


def _hits_many(pairs: list[tuple[str, str]]) -> list[int | None]:
    def one(pair):
        try:
            return count_features(*pair)
        except (FetchError, ET.ParseError, UrlDitolak):
            return None

    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(one, pairs))


# ---------------------------------------------------------------------------
# Inspect
# ---------------------------------------------------------------------------
def detect_service(url: str) -> str | None:
    p = urlsplit(url.strip())
    svc = next((v for k, v in parse_qsl(p.query) if k.lower() == "service"), "").upper()
    if svc in ("WFS", "CSW"):
        return svc
    return "CSW" if "csw" in p.path.lower() else None


def inspect(url: str) -> dict:
    check_url(url)
    base = base_of(url)
    svc = detect_service(url)
    if svc == "CSW":
        return inspect_csw(base)
    try:
        return inspect_wfs(base)
    except GeoportalError:
        if svc == "WFS":
            raise
        return inspect_csw(base)  # layanan tidak disebut di URL: coba CSW


def _layer_row(**kw) -> dict:
    hits = kw.get("hits")
    return {**kw, "besar": hits is not None and hits > MAX_FITUR}


def inspect_wfs(base: str) -> dict:
    body = _get(base, {"service": "WFS", "acceptversions": "2.0.0", "request": "GetCapabilities"})
    if b"WFS_Capabilities" not in body[:4096]:
        raise GeoportalError(400, "URL tersebut bukan layanan WFS 2.0 (GetCapabilities tidak dikenali).")
    caps = parse_wfs_capabilities(body)
    wms = wms_layers(base)
    hits = _hits_many([(base, ft["name"]) for ft in caps["feature_types"]])
    rows = [
        _layer_row(
            typename=ft["name"], judul=ft["title"] or ft["name"], hits=n, srs=ft["default_crs"],
            bbox=ft["wgs84_bbox"], wms=(ft["name"] in wms) if wms is not None else None, wfs_url=base,
        )
        for ft, n in zip(caps["feature_types"], hits)
    ]
    return {"tipe": "wfs", "url": base, "batas_fitur": MAX_FITUR, "layers": rows}


def inspect_csw(base: str) -> dict:
    try:
        records = Csw({"id": "inspect", "url": base, "page_size": 50}, raw_root=None, http_opts=HTTP, kelurahan_map={}).run()
    except (RuntimeError, ValueError) as err:  # bukan CSW, paging tidak konsisten, dll.
        raise GeoportalError(400, f"URL tersebut bukan layanan WFS atau CSW yang dikenali ({err}).") from None
    rows, pairs = [], []
    for r in records:
        wfs = next((x for x in r["link_layer"] if x["protocol"] == "OGC:WFS" and x["name"] and x["url"]), None)
        allowed = False
        if wfs:
            try:
                check_url(wfs["url"])
                allowed = True
            except UrlDitolak:
                pass
        rows.append({
            "id_record": r["id"], "judul": r["judul"] or r["id"], "abstrak": r["abstrak"], "bbox": r["bbox_wgs84"],
            "typename": wfs["name"] if wfs else None, "wfs_url": base_of(wfs["url"]) if wfs else None,
            "wms": any(x["protocol"] == "OGC:WMS" for x in r["link_layer"]), "srs": None,
            "catatan": None if not wfs else (None if allowed else "Host WFS tidak ada di allowlist"),
        })
        if wfs and allowed:
            pairs.append((len(rows) - 1, (base_of(wfs["url"]), wfs["name"])))
    for (i, _), n in zip(pairs, _hits_many([p for _, p in pairs])):
        rows[i]["hits"] = n
    rows = [_layer_row(**{"hits": None, **r}) for r in rows]
    return {"tipe": "csw", "url": base, "batas_fitur": MAX_FITUR, "layers": rows}


# ---------------------------------------------------------------------------
# Ambil layer
# ---------------------------------------------------------------------------
def describe(wfs_url: str, typename: str) -> dict:
    """Metadata satu FeatureType: judul, bbox, SRS, atribut, jumlah fitur, ketersediaan WMS."""
    check_url(wfs_url)
    caps = parse_wfs_capabilities(_get(wfs_url, {"service": "WFS", "acceptversions": "2.0.0", "request": "GetCapabilities"}))
    ft = next((x for x in caps["feature_types"] if x["name"] == typename), None)
    if ft is None:
        raise GeoportalError(404, f"Layer {typename} tidak ditemukan di layanan WFS tersebut.")
    attrs = parse_describe_feature_type(
        _get(wfs_url, {"service": "WFS", "version": "2.0.0", "request": "DescribeFeatureType", "typeNames": typename})
    )
    wms = wms_layers(wfs_url)
    return {
        "judul": ft["title"] or typename, "bbox": ft["wgs84_bbox"], "srs_sumber": ft["default_crs"],
        "atribut_tersedia": [a["name"] for a in attrs if not (a["type"] or "").startswith("gml:")],
        "jumlah_fitur": count_features(wfs_url, typename),
        "wms_url": wms_base(wfs_url) if wms and typename in wms else None,
    }


def _id_num(n: int) -> str:
    return f"{n:,}".replace(",", ".")  # format id-ID: 79.167


def ensure_small(jumlah: int | None) -> None:
    if jumlah is None:
        raise GeoportalError(502, "Geoportal tidak melaporkan jumlah fitur; layer tidak diunduh.")
    if jumlah > MAX_FITUR:
        raise GeoportalError(
            413,
            f"Layer terlalu besar ({_id_num(jumlah)} fitur, batas {_id_num(MAX_FITUR)}). Gunakan tampilan WMS.",
            saran="wms",
        )
    if jumlah == 0:
        raise GeoportalError(422, "Layer tidak berisi fitur.")


def download(entry: dict, layer_dir: Path) -> dict:
    """GetFeature (paging) -> GeoJSON EPSG:4326 lon/lat di <layer_dir>/data.geojson (atomik)."""
    cfg = {
        "id": entry["id"], "layer": entry["id"], "generik": True, "url": entry["wfs_url"], "typename": entry["typename"],
        "srs": OUTPUT_SRS, "page_size": 1000, "max_fitur": MAX_FITUR, "field_nama": entry.get("field_nama"),
        "sort_by": "fid" if "fid" in entry.get("atribut_tersedia", []) else None,
    }
    src = Wfs(cfg, ref_bounds=tuple(entry["bbox"]) if entry.get("bbox") else None, raw_root=None, http_opts=HTTP, kelurahan_map={})
    gdf = src.run()
    layer_dir.mkdir(parents=True, exist_ok=True)
    tmp = layer_dir / "data.geojson.tmp"
    write_geojson(gdf, tmp)
    os.replace(tmp, layer_dir / "data.geojson")  # data lama tetap utuh bila langkah sebelumnya gagal
    return {"jumlah_fitur": len(gdf), "field_nama": src.info.get("field_nama"), "urutan_sumbu": src.info.get("urutan_sumbu")}
