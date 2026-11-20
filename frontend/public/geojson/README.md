# frontend/public/geojson/ — salinan dev GeoJSON (TIDAK ada di repo, dapat dibuat ulang)

Aset yang dilayani dev server di `/geojson/…` (batas kelurahan, batas RT, sungai). **Hanya salinan** dari `data-pipeline/processed/geojson/`; jangan di-commit.

## Isi (3 berkas, ±2,8 MB, EPSG:4326)
`batas-kelurahan.norm.geojson`, `batas-rt.norm.geojson`, `sungai_ln.wgs84.geojson` (lihat `data-pipeline/processed/geojson/README.md`; asal data asli belum dicatat).
Catatan: memuat GeoJSON ini di browser adalah pengecualian sementara AGENTS.md §3.2 (data kecil).

## Cara membuat ulang (dari root repo)
```
python3 data-pipeline/scripts/sync_geojson.py       # menyalin dari data-pipeline/processed/geojson/
```
Bila sumbernya kosong, buat dulu dengan `normalize_names.py` dan `reproject_sungai.py` (dari `data-pipeline/raw/geojson/`).

## Keutuhan dan aturan
Bandingkan dengan `data-pipeline/processed/geojson/` (`diff -r`). Boleh dihapus dan dibuat ulang; jangan di-commit.
