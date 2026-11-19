#!/usr/bin/env python3
"""Runner migrasi sederhana: menjalankan db/migrations/*.sql berurutan dan mencatatnya di public.schema_migrasi.

  data-pipeline/.venv/bin/python data-pipeline/db/migrate.py            # jalankan yang belum
  data-pipeline/.venv/bin/python data-pipeline/db/migrate.py --status   # lihat status

Aturan: migrasi yang sudah dijalankan TIDAK boleh diubah (checksum dibandingkan); perubahan skema = berkas baru.
Tiap migrasi berjalan dalam satu transaksi (gagal = batal seluruhnya).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from koneksi import buka_koneksi  # noqa: E402

MIGRASI = Path(__file__).resolve().parent / "migrations"


def checksum(teks: str) -> str:
    return hashlib.sha256(teks.encode("utf-8")).hexdigest()


def main(argv: list[str]) -> int:
    berkas = sorted(MIGRASI.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    with buka_koneksi() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS public.schema_migrasi ("
            " nomor text PRIMARY KEY, nama text NOT NULL, checksum text NOT NULL,"
            " dijalankan_pada timestamptz NOT NULL DEFAULT now())"
        )
        conn.commit()
        sudah = {r[0]: r[1] for r in conn.execute("SELECT nomor, checksum FROM public.schema_migrasi")}
        if "--status" in argv:
            for b in berkas:
                nomor = b.name[:4]
                print(f"{b.name:45} {'sudah' if nomor in sudah else 'BELUM'}")
            return 0
        baru = 0
        for b in berkas:
            nomor, teks = b.name[:4], b.read_text(encoding="utf-8")
            if nomor in sudah:
                if sudah[nomor] != checksum(teks):
                    print(f"ERROR: {b.name} berubah setelah dijalankan (checksum beda). Buat migrasi baru.", file=sys.stderr)
                    return 1
                continue
            try:
                conn.execute(teks)
                conn.execute("INSERT INTO public.schema_migrasi (nomor, nama, checksum) VALUES (%s, %s, %s)", (nomor, b.name, checksum(teks)))
                conn.commit()
            except Exception as err:  # noqa: BLE001 — batalkan lalu laporkan
                conn.rollback()
                print(f"ERROR: migrasi {b.name} gagal dan dibatalkan: {err}", file=sys.stderr)
                return 1
            print(f"dijalankan: {b.name}")
            baru += 1
        print(f"Selesai: {baru} migrasi baru, {len(sudah)} sudah ada sebelumnya.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
