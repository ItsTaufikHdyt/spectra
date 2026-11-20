# data-pipeline/processed/geojson/ — GeoJSON ternormalisasi (TIDAK ada di repo, dapat dibuat ulang)

## Isi (3 berkas, ±2,8 MB, EPSG:4326 / WGS84)
`batas-kelurahan.norm.geojson` (15 kelurahan, properti `slug` dan nama ternormalisasi; nama asli di `*_asli`), `batas-rt.norm.geojson` (526 RT), `sungai_ln.wgs84.geojson` (5 sungai). Geometri tidak diubah (invalid hanya ditandai).
Dipakai pipeline (`impor_resmi.py analisis/keputusan`: kelurahan administratif) dan frontend (lewat salinan `frontend/public/geojson/`).

## Asal data
Turunan dari `../../raw/geojson/` (pembuat data asli: belum dicatat; lihat `../../raw/geojson/README.md`).

## Cara membuat ulang (dari root repo)
```
data-pipeline/.venv/bin/python data-pipeline/scripts/normalize_names.py      # → batas-kelurahan.norm.geojson, batas-rt.norm.geojson, config/kelurahan_map.csv
data-pipeline/.venv/bin/python data-pipeline/scripts/reproject_sungai.py     # → sungai_ln.wgs84.geojson (EPSG:32650 → 4326)
python3 data-pipeline/scripts/sync_geojson.py                                # → frontend/public/geojson/
```
`normalize_names.py` memakai slug dari `../3dtiles/master-tileset.json` (fallback folder `raw/citygml/`).

## Keutuhan dan aturan
`../../reports/fetch_sources.md` (uji identik) dan `geometry_check.md`. Boleh dibuat ulang; jangan di-commit.
