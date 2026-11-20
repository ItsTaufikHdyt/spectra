# data-pipeline/processed/ — keluaran pipeline (TIDAK ada di repo, dapat dibuat ulang)

Isi di-ignore git (hanya README dan `.gitkeep`). Semua folder di sini **turunan**: boleh dihapus dan dibuat ulang dari sumbernya; jangan di-commit.
Sumber kebenaran data bangunan adalah **PostGIS** (ADR-001) yang diisi dari `../raw/citygml/`; sumber kebenaran ID adalah `../config/registri_id.csv`.

| Subfolder | Isi | Ukuran | Dibuat oleh | Panduan |
|---|---|---|---|---|
| `buildings/` | CityJSONSeq per kelurahan (masukan tyler) | 109 MB, 15 berkas | `scripts/citygml/ekspor.py` | [`buildings/README.md`](buildings/README.md) |
| `3dtiles/` | 3D Tiles 1.1 per kelurahan + `master-tileset.json` | 74 MB, 170 berkas | `buat_tile.py`, `04_build_master.py` | [`3dtiles/README.md`](3dtiles/README.md) |
| `geojson/` | Batas kelurahan/RT dan sungai ternormalisasi (WGS84) | 2,8 MB, 3 berkas | `normalize_names.py`, `reproject_sungai.py` | [`geojson/README.md`](geojson/README.md) |
| `sources/` | Layer vektor per sumber (`<id>.geojson`, skema standar, EPSG:4326) | 5,6 MB, 6 berkas | `fetch_sources.py` | di bawah |
| `catalog/` | Katalog CSW (`records.json`, 25 record) | 24 KB | `fetch_sources.py` | di bawah |
| `user_layers/` | Registry + cache layer yang ditambahkan lewat panel "Data geoportal" (`registry.json`, `<id>/data.geojson`) | kecil | backend (`backend/`) saat pengguna menambah layer | di bawah |
| `analisis/` | Keluaran antara analisis/verifikasi (JSON tile per kelurahan, segitiga per fitur, log validasi, target uji) | 20 MB | `scripts/citygml/verifikasi_tile.cjs`, `fitur_glb.cjs`, dll. | di bawah |

## `sources/`, `catalog/`, `user_layers/`, `analisis/`
- `sources/` dan `catalog/`: `data-pipeline/.venv/bin/python data-pipeline/scripts/fetch_sources.py` (dari root repo). Membaca `config/sources.yaml` (GeoJSON lokal dari `../raw/geojson/`, WFS dan CSW geoportal; butuh jaringan untuk WFS/CSW). Laporan: `../reports/fetch_sources.md`. Keutuhan: tabel "Uji identik" di laporan itu.
- `user_layers/`: dibuat backend (`backend/.venv/bin/uvicorn app.main:app --app-dir backend --port 8100`) ketika pengguna menambah layer di UI. Jangan dibuat manual; boleh dihapus (layer hilang dari daftar). Panduan: `docs/remote-layers.md`.
- `analisis/`: hasil antara untuk `laporan_verifikasi.py` (`reports/impor_resmi_verifikasi.*`). `fitur/lama_*.json` adalah data riwayat dari tile lama yang sudah dihapus dan **tidak dapat dibuat ulang**; sisanya dapat dibuat ulang (lihat README pipeline, langkah verifikasi).

## Urutan membuat ulang semuanya (dari `raw/citygml/` yang sudah ada)
Lihat `../README.md`, bagian "Impor penuh (resmi)". Ringkas: PostGIS dev → `migrate.py` → pulihkan dump `../backups/` (atau impor bertahap) → `ekspor.py` per kelurahan → `buat_tile.py` per kelurahan → `04_build_master.py [--sync]`. **Jangan menjalankan `impor_resmi.py terbit` lagi** (ID resmi sudah terbit).

## Keutuhan
`raw/citygml`: `reports/hash_baseline_raw_citygml.txt`. Tile: `reports/hash_baseline_public_tiles_v2.txt` (salinan `frontend/public/tiles/`). Registri: `config/registri_id.csv.sha256`.
