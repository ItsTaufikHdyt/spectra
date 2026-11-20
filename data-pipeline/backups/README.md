# data-pipeline/backups/ — cadangan basis data (TIDAK ada di repo)

Cadangan `pg_dump` PostGIS dev. Berisi **data per bangunan (geometri, ID, atribut)**; jangan di-commit atau dipublikasikan. Hanya `README.md` dan `.gitkeep` dilacak.

## Isi yang diharapkan
`spectra_dev_pra_terbit_batch1.dump` (57 MB; staging sebelum ID resmi terbit), `spectra_dev_pasca_terbit_batch1.dump` (113 MB; 51.873 ID resmi), `spectra_dev_pasca_qc_footprint_mikro.dump` (113 MB; terbaru, setelah flag `footprint_mikro`). Format custom (`-Fc`), skema `core`, `ref`, `elevasi`, `sim`, `staging` (PostgreSQL 15 / PostGIS 3.5).

## Asal
Dibuat sendiri oleh pipeline (`db.sh dump`). Tidak ada penyedia eksternal.

## Cara membuat dan memulihkan
```
data-pipeline/docker/db.sh dump data-pipeline/backups/<nama>.dump
# pulihkan ke database KOSONG:
data-pipeline/docker/db.sh naik
data-pipeline/docker/db.sh reset --ya          # MENGHAPUS data dev, hanya bila ingin database kosong
data-pipeline/docker/db.sh restore data-pipeline/backups/spectra_dev_pasca_qc_footprint_mikro.dump
```
Pemulihan teruji (51.873 registri, 51.873 bangunan, 51.888 staging).

## Keutuhan dan aturan
Periksa dengan `select count(*) from core.registri_id` (51.873) dan bandingkan `config/registri_id.csv.sha256` setelah `impor_resmi.py ekspor-registri`.
**Bila dump hilang dan basis data juga hilang:** ID resmi hanya tersisa di `../config/registri_id.csv`; **mengimpor registri dari CSV belum diimplementasikan** (hutang). Jangan menerbitkan ID ulang dari nol: itu menghasilkan ID berbeda. Simpan salinan dump di penyimpanan lain.
