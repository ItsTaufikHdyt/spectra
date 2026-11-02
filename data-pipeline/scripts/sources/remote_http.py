"""
remote_http.py — Klien HTTP READ-ONLY untuk geoportal (WFS/CSW) + penyimpanan respons mentah.

Pengaman:
  * Hanya metode GET dan hanya operasi baca di ALLOWED_REQUESTS. Transaction, Harvest,
    LockFeature, CreateStoredQuery, dsb. ditolak sebelum request dikirim.
  * Respons mentah disimpan di raw/remote/<sumber>/<timestamp>/ (folder baru tiap run,
    tidak pernah menimpa) bersama requests.json berisi URL, parameter, status, dan sha256.
  * Tanpa kredensial: geoportal Bontang dapat dibaca anonim (dicek 2026-11-02).
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("sources")

DP = Path(__file__).resolve().parents[2]  # data-pipeline/
RAW_REMOTE = DP / "raw" / "remote"

ALLOWED_REQUESTS = frozenset({"GetCapabilities", "DescribeFeatureType", "GetFeature", "GetRecords", "GetRecordById"})
TIMEOUT_S = 60
MAX_ATTEMPTS = 3
BACKOFF_S = 1.0  # jeda 1 s lalu 2 s (eksponensial) di antara percobaan
USER_AGENT = "spectra-data-pipeline/1.0 (read-only ETL Digital Twin Kota Bontang)"


class FetchError(RuntimeError):
    """Request gagal setelah semua percobaan."""


def assert_read_only(params: dict) -> None:
    op = next((v for k, v in params.items() if k.lower() == "request"), None)
    if op not in ALLOWED_REQUESTS:
        raise PermissionError(f"Operasi {op!r} bukan operasi baca yang diizinkan ({sorted(ALLOWED_REQUESTS)}).")


def build_url(base: str, params: dict) -> str:
    return f"{base}?{urllib.parse.urlencode(params)}"


def get(base: str, params: dict, *, timeout: float = TIMEOUT_S) -> tuple[bytes, dict]:
    """GET dengan retry (maks. MAX_ATTEMPTS, jeda eksponensial). Kembalikan (body, meta)."""
    assert_read_only(params)
    url = build_url(base, params)
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        t0 = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                meta = {"status": resp.status, "content_type": resp.headers.get("Content-Type"), "attempt": attempt}
            meta["elapsed_s"] = round(time.monotonic() - t0, 2)
            label = params.get("typeNames") or params.get("id") or params.get("startPosition") or ""
            log.info("GET %s %s -> %s (%d B, %.1f s)", params.get("request"), label, meta["status"], len(body), meta["elapsed_s"])
            return body, meta
        except urllib.error.HTTPError as err:
            last_err = err
            if err.code < 500 and err.code != 429:  # kesalahan klien: mengulang tidak membantu
                break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
            last_err = err
        log.warning("Percobaan %d/%d gagal untuk %s: %s", attempt, MAX_ATTEMPTS, params.get("request"), last_err)
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_S * 2 ** (attempt - 1))
    raise FetchError(f"{params.get('request')} gagal: {last_err}")


class RawRun:
    """Satu folder raw/remote/<sumber>/<timestamp>/ untuk satu kali run; tidak pernah menimpa."""

    def __init__(self, source_id: str, stamp: str | None = None):
        self.stamp = stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.dir = RAW_REMOTE / source_id / self.stamp
        self.dir.mkdir(parents=True, exist_ok=False)  # gagal bila folder sudah ada
        self.entries: list[dict] = []

    def fetch(self, base: str, params: dict, name: str) -> bytes:
        """GET lalu simpan body ke <name>; kegagalan dicatat di requests.json lalu dilempar ulang."""
        entry = {"file": name, "url": build_url(base, params), "base": base, "params": params}
        try:
            body, meta = get(base, params)
        except FetchError as err:
            entry["error"] = str(err)
            self.entries.append(entry)
            self._write_index()
            raise
        path = self.dir / name
        if path.exists():
            raise FileExistsError(path)
        path.write_bytes(body)
        entry.update(meta, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        self.entries.append(entry)
        self._write_index()
        return body

    def _write_index(self) -> None:
        (self.dir / "requests.json").write_text(
            json.dumps({"timestamp_utc": self.stamp, "requests": self.entries}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
