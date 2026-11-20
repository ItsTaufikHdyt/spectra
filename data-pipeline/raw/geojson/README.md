# data-pipeline/raw/geojson/ — batas wilayah dan sungai (TIDAK ada di repo)

Read-only; jangan di-commit.

## Isi yang diharapkan (3 berkas, ±2,8 MB)
| Berkas | Isi | Fitur | CRS |
|---|---|---|---|
| `batas-kelurahan.json` | Batas 15 kelurahan (MultiPolygon) | 15 | EPSG:4326 |
| `batas-rt.json` | Batas RT (termasuk RT pulau) | 526 | EPSG:4326 |
| `sungai_ln_5k.json` | Sungai/drainase (garis) | 5 | EPSG:32650 (diproyeksikan ke 4326 oleh `reproject_sungai.py`) |

## Asal data
- **Pembuat dan tanggal asli: belum dicatat.** Berkas bertanggal 2026-11-02 di mesin pengembangan. Ekstennya sama (IoU 1,0000) dengan layer WFS geoportal Kota Bontang (`reports/fetch_sources.md`), tetapi kesamaan sumber belum dipastikan.
- **Kontak untuk salinan:** belum dicatat (hubungi pemilik/pengelola repo). Alternatif: layer serupa dapat diunduh dari geoportal lewat `fetch_sources.py` (lihat `../remote/README.md`), tetapi hasilnya belum tentu identik berkas ini.

## Keutuhan
Belum ada baseline hash. QC geometri: `../../reports/geometry_check.md` (`scripts/check_geometry.py`, read-only).

## Turunan
Menjadi `../processed/geojson/` lewat `scripts/normalize_names.py` dan `scripts/reproject_sungai.py` (lihat `../processed/geojson/README.md`).
