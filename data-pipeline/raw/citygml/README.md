# data-pipeline/raw/citygml/ — CityGML bangunan (TIDAK ada di repo)

**Sumber tunggal data bangunan** (ADR-004). **Read-only**; jangan di-commit.

## Isi yang diharapkan
- **31 berkas `.gml`** dalam 15 folder `Kelurahan <Nama>/`, total **±3,5 GB**, **51.888 bangunan** (`bldg:Building`, LOD2). 30 berkas CityGML 2.0 (`gml:pos`) dan 1 berkas CityGML 3.0 (Berebas Tengah, `gml:posList`).
- Format: CityGML dengan geometri `lod2MultiSurface`; atribut hanya `measuredHeight` dan `storeysAboveGround` (Berebas Tengah tanpa atribut). CRS **EPSG:32650** (UTM 50N). Tiga berkas (Guntung Part I, Guntung Part II, Satimpo) **berlabel EPSG:32748 padahal koordinatnya EPSG:32650**; pipeline mengoreksinya lewat konfigurasi.
- Ada pula `Kelurahan Bontang Kuala/Model 3D - Kelurahan Bontang Kuala.gfs` (skema GDAL, bukan CityGML; diabaikan).

## Struktur folder (nama persis; dipakai `../../config/citygml_sources.yaml`)
| Slug | Folder | Berkas `.gml` | Bangunan | Ukuran (MB) | CityGML | EPSG di berkas |
|---|---|---:|---:|---:|---|---|
| `api_api` | `Kelurahan Api Api/` | 1 | 5.142 | 400 | 2.0 | 32650 |
| `belimbing` | `Kelurahan Belimbing/` | 3 | 4.645 | 330 | 2.0 | 32650 |
| `berebas_pantai` | `Kelurahan Berebas Pantai/` | 1 | 2.022 | 161 | 2.0 | 32650 |
| `berebas_tengah` | `Kelurahan Berebas Tengah/` | 1 | 3.390 | 154 | 3.0 | 32650 |
| `bontang_baru` | `Kelurahan Bontang Baru/` | 1 | 4.147 | 320 | 2.0 | 32650 |
| `bontang_kuala` | `Kelurahan Bontang Kuala/` | 1 | 2.366 | 143 | 2.0 | 32650 |
| `bontang_lestari` | `Kelurahan Bontang Lestari/` | 8 | 2.219 | 102 | 2.0 | 32650 |
| `guntung` | `Kelurahan Guntung/` | 3 | 2.059 | 108 | 2.0 | 32650/32748 |
| `gunung_elai` | `Kelurahan Gunung Elai/` | 3 | 4.469 | 335 | 2.0 | 32650 |
| `gunung_telihan` | `Kelurahan Gunung Telihan/` | 1 | 3.989 | 254 | 2.0 | 32650 |
| `kanaan` | `Kelurahan Kanaan/` | 1 | 1.837 | 98 | 2.0 | 32650 |
| `loktuan` | `Kelurahan Loktuan/` | 4 | 5.010 | 347 | 2.0 | 32650 |
| `satimpo` | `Kelurahan Satimpo/` | 1 | 2.502 | 283 | 2.0 | 32748 |
| `tanjung_laut` | `Kelurahan Tanjung Laut/` | 1 | 4.340 | 327 | 2.0 | 32650 |
| `tanjung_laut_indah` | `Kelurahan Tanjung Laut Indah/` | 1 | 3.751 | 222 | 2.0 | 32650 |
| **Total** | 15 folder | 31 | 51.888 | 3.583 | | |

Nama berkas persis (dan jumlah bangunan per berkas) ada di `../../config/citygml_sources.yaml` (`path`, `part`, `bangunan_inventaris`); contoh: `Kelurahan Bontang Lestari/Model 3D - Kelurahan Bontang Lestari - Part I.gml` (8 part), `Kelurahan Bontang Baru/GABUNGAN BONTANG BARU.gml`.

## Asal data
- **Pembuat:** belum dicatat secara resmi. Metadata di dalam berkas (`gml:description`, "created by …") menyebut operator **Digital_Twin_UGM** (24.010 bangunan), **GeoAI01/02/03/04/09/GeoAI/GeoAIT** (24.488 bangunan), dan Berebas Tengah tanpa operator (3.390).
- **Tanggal:** berkas bertanggal modifikasi 2025-05-27 s.d. 2025-09-02 (menurut inventaris).
- **Penyedia/kontak untuk mendapatkan salinan:** **belum dicatat**. Hubungi pemilik/pengelola repo.
- Inventaris rinci: `../../reports/citygml_inventory.md`.

## Keutuhan
`sha256sum -c --quiet data-pipeline/reports/hash_baseline_raw_citygml.txt` dari root repo (31 hash; harus tanpa keluaran galat).

## Turunan
Dibaca oleh `scripts/citygml/impor_resmi.py staging` (urutan lengkap: `../../README.md`, bagian "Impor penuh"). **Jangan menerbitkan ID resmi ulang**; registri ada di `../../config/registri_id.csv`.
