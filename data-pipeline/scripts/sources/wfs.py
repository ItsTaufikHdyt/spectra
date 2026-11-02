"""
wfs.py — Adapter WFS 2.0 (GetFeature, outputFormat=application/json, paging startIndex/count).

Urutan sumbu: pada WFS 2.0, srsName urn:ogc:def:crs:EPSG::4326 resminya lat/lon. GeoServer
(dicek 2026-11-02) tetap mengirim GeoJSON lon/lat, tetapi itu perilaku implementasi. Karena itu
urutan sumbu DIDETEKSI dari data: extent hasil dibandingkan dengan extent referensi (GeoJSON
lokal layer yang sama); bila versi tertukar jauh lebih cocok, sumbu ditukar.
Paging memakai sortBy=fid agar urutan halaman stabil (server: PagingIsTransactionSafe=FALSE).
"""

from __future__ import annotations

import json

import shapely

from .base import DP, Source, log, round_geometry
from .remote_http import RAW_REMOTE, RawRun

DEFAULT_PAGE_SIZE = 200
MAX_PAGES = 500  # pengaman loop bila server salah melaporkan numberMatched
MIN_IOU = 0.5


def iou(a, b) -> float:
    """Intersection-over-union dua bbox (minx, miny, maxx, maxy)."""
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def _inside(b, ref, pad: float) -> bool:
    return b[0] >= ref[0] - pad and b[1] >= ref[1] - pad and b[2] <= ref[2] + pad and b[3] <= ref[3] + pad


def detect_axis_order(bounds, ref_bounds) -> tuple[str, float]:
    """'lonlat' atau 'latlon' + IoU terbaik terhadap extent referensi.

    Extent sangat kecil (mis. satu titik) membuat IoU ~0; untuk kasus itu dipakai uji
    "berada di dalam extent referensi" dan skor dilaporkan 0.
    """
    swapped = (bounds[1], bounds[0], bounds[3], bounds[2])
    a, b = iou(bounds, ref_bounds), iou(swapped, ref_bounds)
    order, best = ("lonlat", a) if a >= b else ("latlon", b)
    if best < MIN_IOU:
        pad = 0.01 * max(ref_bounds[2] - ref_bounds[0], ref_bounds[3] - ref_bounds[1]) + 1e-6
        fits = [o for o, bb in (("lonlat", bounds), ("latlon", swapped)) if _inside(bb, ref_bounds, pad)]
        if len(fits) == 1:
            return fits[0], 0.0
        raise ValueError(f"Extent WFS tidak cocok dengan referensi dalam urutan sumbu mana pun (IoU {a:.2f} / {b:.2f})")
    return order, best


class Wfs(Source):
    tipe = "wfs"

    def __init__(self, cfg: dict, *, ref_bounds=None, stamp: str | None = None, raw_root=RAW_REMOTE, http_opts=None, **kw):
        super().__init__(cfg, **kw)
        self.ref_bounds = ref_bounds  # extent EPSG:4326 lon/lat (GeoJSON lokal, atau WGS84BoundingBox capabilities)
        self.stamp = stamp
        self.raw_root = raw_root  # None = respons tidak disimpan
        self.http_opts = http_opts or {}

    def fetch(self) -> list[dict]:
        run = RawRun(self.id, self.stamp, root=self.raw_root, **self.http_opts)
        max_features = self.cfg.get("max_fitur")
        size = int(self.cfg.get("page_size") or DEFAULT_PAGE_SIZE)
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": self.cfg["typename"],
            "outputFormat": "application/json",
            "srsName": self.cfg["srs"],
            "count": str(size),
        }
        sort_by = self.cfg.get("sort_by", "fid")  # None: layer tanpa kolom fid (urutan halaman tidak dijamin)
        if sort_by:
            params["sortBy"] = sort_by
        pages, start, matched = [], 0, None
        for n in range(MAX_PAGES):
            page = json.loads(run.fetch(self.cfg["url"], {**params, "startIndex": str(start)}, f"page_{n:04d}.json"))
            pages.append(page)
            got = len(page.get("features") or [])
            matched = page.get("numberMatched", matched)
            if max_features and isinstance(matched, int) and matched > max_features:
                raise RuntimeError(f"{self.id}: {matched} fitur melebihi batas {max_features}")
            start += got
            if got == 0 or (isinstance(matched, int) and start >= matched):
                break
        else:
            raise RuntimeError(f"{self.id}: melebihi {MAX_PAGES} halaman")
        total = sum(len(p["features"]) for p in pages)
        if isinstance(matched, int) and total != matched:
            raise RuntimeError(f"{self.id}: menerima {total} fitur, server melaporkan numberMatched={matched}")
        self.info.update(raw_dir=str(run.dir.relative_to(DP)) if run.dir else None, halaman=len(pages), page_size=size, fitur=total, numberMatched=matched)
        log.info("%s: %d fitur dalam %d halaman", self.id, total, len(pages))
        return pages

    def normalize(self, raw: list[dict]):
        features = [f for p in raw for f in p["features"]]
        gdf = self.standardize(features, "EPSG:4326")
        if self.ref_bounds is None:
            log.warning("%s: tanpa extent referensi; urutan sumbu diasumsikan lon/lat", self.id)
            self.info["urutan_sumbu"] = "lonlat (asumsi, tanpa referensi)"
        else:
            order, score = detect_axis_order(tuple(gdf.total_bounds), self.ref_bounds)
            if order == "latlon":
                gdf["geometry"] = shapely.transform(gdf.geometry.values, lambda c: c[:, ::-1])
            self.info.update(urutan_sumbu=order, iou_extent_vs_lokal=round(score, 4))
        return round_geometry(gdf)
