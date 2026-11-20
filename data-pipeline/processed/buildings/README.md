# data-pipeline/processed/buildings/ — CityJSONSeq per kelurahan (TIDAK ada di repo, dapat dibuat ulang)

## Isi
15 berkas `<slug>.city.jsonl` (±109 MB; 51.816 bangunan): **CityJSON 2.0 Sequences**, **EPSG:32650** dengan `transform` (skala 0,001, presisi 1 mm).
Baris 1 = metadata (`transform`, `referenceSystem`, `geographicalExtent`, tanpa objek); baris berikutnya = satu `CityJSONFeature` (satu bangunan) dengan `MultiSurface` LOD 2 bersemantik (lantai/atap/dinding) dan atribut `id` (`BTG-BLD-xxxxxx`), `gml_id`, `nama`, `tinggi`, `jumlah_lantai` (dihilangkan bila kosong), `luas_tapak` (dihilangkan bila kosong). Hanya bangunan bertinggi ≥ 0,1 m. Z dasar = 0.

## Asal data
Turunan dari PostGIS (`core.bangunan`), bukan data eksternal. Tidak ada kontak penyedia.

## Cara membuat ulang
Prasyarat: PostGIS dev berisi data resmi (pulihkan dari `../../backups/*.dump`, lihat `../../backups/README.md`).
```
data-pipeline/docker/db.sh naik
data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/ekspor.py --slug <slug> [--validasi]      # ulangi untuk 15 slug (config/kelurahan_map.csv)
```
`--validasi` memeriksa skema CityJSON 2.0.2 (±50 detik per 2.000 bangunan).

## Keutuhan dan aturan
Keluaran deterministik dari PostGIS; periksa dengan `validasi_cityjson.py` dan `reports/impor_resmi_validasi_skema.md` (0 galat, 51.816 fitur). Boleh dibuat ulang; jangan di-commit.
