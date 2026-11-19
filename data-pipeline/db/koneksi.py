"""Koneksi ke PostGIS pengembangan spectra. Kredensial HANYA dari data-pipeline/.env atau variabel lingkungan.

Tidak ada kredensial di kode atau di repo (.env di-ignore git; contoh tanpa rahasia: .env.example).
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

DP = Path(__file__).resolve().parents[1]  # data-pipeline/
ENV_FILE = DP / ".env"
WAJIB = ("SPECTRA_DB_HOST", "SPECTRA_DB_PORT", "SPECTRA_DB_NAME", "SPECTRA_DB_USER", "SPECTRA_DB_PASSWORD")


def baca_env(path: Path = ENV_FILE) -> dict[str, str]:
    """Baca berkas KEY=VALUE sederhana; variabel lingkungan yang sudah ada menang."""
    nilai: dict[str, str] = {}
    if path.exists():
        for baris in path.read_text(encoding="utf-8").splitlines():
            baris = baris.strip()
            if baris and not baris.startswith("#") and "=" in baris:
                k, v = baris.split("=", 1)
                nilai[k.strip()] = v.strip()
    nilai.update({k: os.environ[k] for k in WAJIB if k in os.environ})
    return nilai


def buka_koneksi(*, autocommit: bool = False) -> psycopg.Connection:
    cfg = baca_env()
    hilang = [k for k in WAJIB if not cfg.get(k)]
    if hilang:
        raise RuntimeError(f"Konfigurasi database kurang ({', '.join(hilang)}). Salin .env.example ke .env lalu isi sandi.")
    return psycopg.connect(
        host=cfg["SPECTRA_DB_HOST"], port=int(cfg["SPECTRA_DB_PORT"]), dbname=cfg["SPECTRA_DB_NAME"],
        user=cfg["SPECTRA_DB_USER"], password=cfg["SPECTRA_DB_PASSWORD"], autocommit=autocommit,
        connect_timeout=10,
    )
