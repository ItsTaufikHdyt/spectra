"""
csw.py — Adapter CSW 2.0.2 (GetRecords ISO 19139, paging startPosition/maxRecords).

Hasilnya METADATA katalog (judul, abstrak, bbox, link layer), bukan geometri; ditulis ke
processed/catalog/records.json oleh fetch_sources.py. Data kontak tidak disimpan.
"""

from __future__ import annotations

from .base import DP, Source, log
from .ogc_xml import parse_csw_search, parse_iso_record
from .remote_http import RAW_REMOTE, RawRun

ISO_SCHEMA = "http://www.isotc211.org/2005/gmd"  # = "csw:IsoRecord"
DEFAULT_PAGE_SIZE = 10
MAX_PAGES = 200


class Csw(Source):
    tipe = "csw"

    def __init__(self, cfg: dict, *, stamp: str | None = None, raw_root=RAW_REMOTE, http_opts=None, **kw):
        super().__init__(cfg, **kw)
        self.stamp = stamp
        self.raw_root = raw_root  # None = respons tidak disimpan
        self.http_opts = http_opts or {}

    def fetch(self) -> list[dict]:
        run = RawRun(self.id, self.stamp, root=self.raw_root, **self.http_opts)
        size = int(self.cfg.get("page_size") or DEFAULT_PAGE_SIZE)
        params = {
            "service": "CSW",
            "version": "2.0.2",
            "request": "GetRecords",
            "typeNames": "gmd:MD_Metadata",
            "resultType": "results",
            "outputSchema": ISO_SCHEMA,
            "elementSetName": "full",
            "maxRecords": str(size),
        }
        pages, pos = [], 1
        for n in range(MAX_PAGES):
            page = parse_csw_search(run.fetch(self.cfg["url"], {**params, "startPosition": str(pos)}, f"page_{n:04d}.xml"))
            pages.append(page)
            # nextRecord = 0 berarti halaman terakhir (CSW 2.0.2 §10.8.4.13)
            if page["returned"] == 0 or page["next"] == 0 or page["next"] > page["matched"]:
                break
            pos = page["next"]
        else:
            raise RuntimeError(f"{self.id}: melebihi {MAX_PAGES} halaman")
        got = sum(p["returned"] for p in pages)
        matched = pages[0]["matched"]
        if got != matched:
            raise RuntimeError(f"{self.id}: menerima {got} record, server melaporkan {matched}")
        self.info.update(raw_dir=str(run.dir.relative_to(DP)) if run.dir else None, halaman=len(pages), page_size=size, record=got, numberOfRecordsMatched=matched)
        log.info("%s: %d record dalam %d halaman", self.id, got, len(pages))
        return pages

    def normalize(self, raw: list[dict]) -> list[dict]:
        records = [parse_iso_record(md) for p in raw for md in p["records"]]
        ids = [r["id"] for r in records]
        if len(set(ids)) != len(ids):
            raise RuntimeError(f"{self.id}: id record duplikat antar halaman (paging tidak stabil?)")
        return sorted(records, key=lambda r: r["id"] or "")
