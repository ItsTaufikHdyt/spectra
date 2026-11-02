"""
main.py — API backend spectra untuk layer geoportal (WFS/CSW), semua di bawah /api.

Jalankan (dari root repo, satu worker; lihat registry.py):
    backend/.venv/bin/uvicorn app.main:app --app-dir backend --port 8100

Browser TIDAK memanggil WFS/CSW langsung; frontend memanggil endpoint ini (proxy Vite /api).
Tidak ada operasi tulis ke geoportal: "hapus" hanya menghapus entri registry dan cache lokal.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from . import geoportal
from .geoportal import GeoportalError, explain
from .registry import LayerTidakAda, Registry, new_id

DP = Path(__file__).resolve().parents[2] / "data-pipeline"
USER_LAYERS = Path(os.environ.get("SPECTRA_USER_LAYERS_DIR", DP / "processed" / "user_layers"))
PALETTE = ["#F97316", "#A78BFA", "#F472B6", "#34D399", "#60A5FA", "#E879F9"]

app = FastAPI(title="spectra backend", docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")
registry = Registry(USER_LAYERS)


@app.exception_handler(GeoportalError)
def _geoportal_error(_req, err: GeoportalError):
    return JSONResponse(status_code=err.status, content={"detail": err.pesan, **err.extra})


@app.exception_handler(LayerTidakAda)
def _not_found(_req, _err):
    return JSONResponse(status_code=404, content={"detail": "Layer tidak ditemukan di daftar spectra."})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _call(fn, *args):
    """Jalankan fungsi geoportal; error teknis -> GeoportalError berpesan jelas."""
    try:
        return fn(*args)
    except Exception as err:  # noqa: BLE001 — diterjemahkan lalu dilempar ulang
        raise explain(err) from err


# ---------------------------------------------------------------------------
class InspectIn(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


class LayerIn(BaseModel):
    wfs_url: str = Field(min_length=8, max_length=2000)
    typename: str = Field(min_length=1, max_length=200)
    judul: str | None = Field(default=None, max_length=120)
    mode: Literal["geojson", "wms"] = "geojson"
    field_nama: str | None = Field(default=None, max_length=100)


class LayerPatch(BaseModel):
    aktif: bool | None = None
    judul: str | None = Field(default=None, min_length=1, max_length=120)
    warna: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    opasitas: float | None = Field(default=None, ge=0, le=1)
    urutan: int | None = Field(default=None, ge=0, le=10_000)
    field_nama: str | None = Field(default=None, max_length=100)


# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "batas_fitur": geoportal.MAX_FITUR, "batas_byte": geoportal.MAX_BYTES}


@app.post("/api/sources/inspect")
def inspect(body: InspectIn):
    return _call(geoportal.inspect, body.url)


@app.get("/api/layers")
def list_layers():
    return {"layers": registry.list(), "batas_fitur": geoportal.MAX_FITUR}


@app.post("/api/layers", status_code=201)
def add_layer(body: LayerIn):
    wfs_url = geoportal.base_of(body.wfs_url)
    if any(x["wfs_url"] == wfs_url and x["typename"] == body.typename for x in registry.list()):
        raise HTTPException(409, "Layer ini sudah ada di daftar spectra.")
    meta = _call(geoportal.describe, wfs_url, body.typename)
    if body.field_nama and body.field_nama not in meta["atribut_tersedia"]:
        raise HTTPException(422, f"Atribut {body.field_nama!r} tidak ada di layer ini.")
    if body.mode == "wms" and not meta["wms_url"]:
        raise HTTPException(422, "Layer ini tidak tersedia sebagai WMS di geoportal.")
    if body.mode == "geojson":
        _call(geoportal.ensure_small, meta["jumlah_fitur"])

    n = len(registry.list())
    entry = {
        "id": new_id(body.typename), "typename": body.typename, "wfs_url": wfs_url, "mode": body.mode,
        "judul": body.judul or meta["judul"], "aktif": True, "warna": PALETTE[n % len(PALETTE)], "opasitas": 0.6,
        "field_nama": body.field_nama, "status": "ok", "pesan_error": None, "ditambahkan": _now(),
        **{k: meta[k] for k in ("bbox", "srs_sumber", "atribut_tersedia", "jumlah_fitur", "wms_url")},
    }
    try:
        if body.mode == "geojson":
            entry.update(_call(geoportal.download, entry, registry.layer_dir(entry["id"])))
        entry["diambil"] = _now()
        return registry.add(entry)
    except Exception:
        shutil.rmtree(registry.layer_dir(entry["id"]), ignore_errors=True)  # jangan tinggalkan cache yatim
        raise


@app.patch("/api/layers/{layer_id}")
def patch_layer(layer_id: str, body: LayerPatch):
    entry = registry.get(layer_id)
    changes = body.model_dump(exclude_unset=True)
    if "field_nama" in changes and changes["field_nama"] != entry.get("field_nama"):
        field = changes["field_nama"]
        if field is not None and field not in entry.get("atribut_tersedia", []):
            raise HTTPException(422, f"Atribut {field!r} tidak ada di layer ini.")
        if entry["mode"] == "geojson":
            _rename_features(layer_id, field)
    return registry.update(layer_id, **changes)


def _rename_features(layer_id: str, field: str | None) -> None:
    """Ganti kolom `nama` di cache dari atribut asli (tanpa request ke geoportal)."""
    path = registry.layer_dir(layer_id) / "data.geojson"
    fc = json.loads(path.read_text(encoding="utf-8"))
    for f in fc["features"]:
        v = (f["properties"].get("atribut") or {}).get(field) if field else None
        f["properties"]["nama"] = str(v) if v is not None else None
    tmp = path.with_suffix(".geojson.tmp")
    tmp.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@app.post("/api/layers/{layer_id}/refresh")
def refresh_layer(layer_id: str):
    entry = registry.get(layer_id)
    try:
        jumlah = _call(geoportal.count_features, entry["wfs_url"], entry["typename"])
        changes = {"jumlah_fitur": jumlah}
        if entry["mode"] == "geojson":
            _call(geoportal.ensure_small, jumlah)
            changes.update(_call(geoportal.download, {**entry, "jumlah_fitur": jumlah}, registry.layer_dir(layer_id)))
    except GeoportalError as err:
        registry.update(layer_id, status="error", pesan_error=err.pesan)  # data lama tetap dipakai
        raise
    return registry.update(layer_id, **changes, status="ok", pesan_error=None, diambil=_now())


@app.delete("/api/layers/{layer_id}", status_code=204)
def delete_layer(layer_id: str):
    registry.remove(layer_id)


@app.get("/api/layers/{layer_id}/data")
def layer_data(layer_id: str):
    entry = registry.get(layer_id)
    path = registry.layer_dir(layer_id) / "data.geojson"
    if entry["mode"] != "geojson" or not path.exists():
        raise HTTPException(404, "Layer ini tidak punya data GeoJSON (mode WMS atau cache hilang; coba refresh).")
    return FileResponse(path, media_type="application/geo+json")
