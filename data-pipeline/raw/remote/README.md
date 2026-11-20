# data-pipeline/raw/remote/ — respons mentah geoportal (TIDAK ada di repo)

Arsip respons WFS/CSW **hanya-baca** dari geoportal Kota Bontang (`https://geoportal.bontangkota.go.id`), dibuat otomatis; jangan di-commit.

## Isi yang diharapkan (±22 MB, 127 berkas pada 2026-11-02)
`raw/remote/<id>/<timestamp UTC>/…` dengan `<id>` dari `../../config/sources.yaml`: `wfs_kelurahan`, `wfs_rt`, `wfs_sungai`, `wfs_geoportal`, `csw_geoportal`.
Satu folder `<timestamp>` baru dibuat tiap run `fetch_sources.py` (contoh `20261102T053649Z`).

## Asal data
Geoportal Kota Bontang (layanan publik, akses anonim, hanya baca: GetCapabilities, DescribeFeatureType, GetFeature, GetRecords, GetRecordById). Diambil 2026-11-02 oleh `fetch_sources.py`; panel "Data geoportal" di frontend juga menulis cache terpisah di `../processed/user_layers/`.

## Cara membuat ulang
```
data-pipeline/.venv/bin/python data-pipeline/scripts/fetch_sources.py     # dari root repo; butuh jaringan
```
Ini juga membuat ulang `../processed/sources/`, `../processed/catalog/`, dan `../../reports/fetch_sources.md`. Isi geoportal bisa berubah sejak 2026-11-02, jadi hasilnya belum tentu sama.

## Keutuhan dan aturan
Tidak ada baseline hash (arsip bertanggal; boleh dibuat ulang). Boleh dihapus dan dibuat ulang; jangan di-commit.
