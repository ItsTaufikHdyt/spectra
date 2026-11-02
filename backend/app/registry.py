"""
registry.py — Daftar layer geoportal yang ditambahkan pengguna.

Disimpan sebagai satu file JSON (processed/user_layers/registry.json), bukan SQLite:
jumlah layer kecil (puluhan), satu proses backend, isinya mudah dibaca/di-diff, dan konsisten
dengan output pipeline lain yang juga JSON. Penulisan atomik (file sementara + os.replace)
di bawah satu lock.
shortcut: lock hanya berlaku di dalam satu proses; jalankan uvicorn dengan 1 worker. Pindah ke
SQLite/PostGIS bila backend dijalankan multi-worker atau multi-pengguna.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
import uuid
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,80}$")


class LayerTidakAda(KeyError):
    pass


def new_id(typename: str) -> str:
    short = re.sub(r"[^a-z0-9_]+", "_", typename.split(":")[-1].lower()).strip("_")[:48] or "layer"
    return f"{short}-{uuid.uuid4().hex[:6]}"


class Registry:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "registry.json"
        self.lock = threading.RLock()

    # --- penyimpanan -----------------------------------------------------------------
    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))["layers"]

    def _write(self, layers: list[dict]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"versi": 1, "layers": layers}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    # --- operasi ---------------------------------------------------------------------
    def layer_dir(self, layer_id: str) -> Path:
        if not ID_RE.match(layer_id):  # cegah path traversal lewat id
            raise LayerTidakAda(layer_id)
        return self.root / layer_id

    def list(self) -> list[dict]:
        with self.lock:
            return sorted(self._read(), key=lambda x: (x["urutan"], x["ditambahkan"]))

    def get(self, layer_id: str) -> dict:
        self.layer_dir(layer_id)
        with self.lock:
            for x in self._read():
                if x["id"] == layer_id:
                    return x
        raise LayerTidakAda(layer_id)

    def add(self, entry: dict) -> dict:
        with self.lock:
            layers = self._read()
            entry["urutan"] = max((x["urutan"] for x in layers), default=-1) + 1
            layers.append(entry)
            self._write(layers)
            return entry

    def update(self, layer_id: str, **fields) -> dict:
        with self.lock:
            layers = self._read()
            for x in layers:
                if x["id"] == layer_id:
                    x.update(fields)
                    self._write(layers)
                    return x
        raise LayerTidakAda(layer_id)

    def remove(self, layer_id: str) -> None:
        """Hapus entri DAN cache-nya (folder <root>/<id>/). Tidak menyentuh geoportal."""
        folder = self.layer_dir(layer_id)
        with self.lock:
            layers = self._read()
            remaining = [x for x in layers if x["id"] != layer_id]
            if len(remaining) == len(layers):
                raise LayerTidakAda(layer_id)
            self._write(remaining)
            if folder.exists():
                shutil.rmtree(folder)
