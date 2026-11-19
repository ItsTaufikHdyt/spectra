# data-pipeline — pipeline bangunan (uji coba)

CityGML (`raw/citygml/`, read-only) → PostGIS dev → CityJSONSeq → `tyler` → 3D Tiles (`processed/3dtiles_v2/`).
Status: **uji coba satu kelurahan (Bontang Lestari)**. Registri ID yang diterbitkan **bukan resmi** (status `uji_coba`),
tidak diekspor ke `config/`, dan basis data dev boleh di-reset kapan saja. Lihat ADR-001..006 di `docs/adr/`.

Semua perintah dari root repo.

## 1. Basis data PostGIS dev
Kontainer sendiri (`spectra-postgis-dev`, image `geonode/postgis:15-3.5-latest`, volume `spectra_pgdata_dev`,
`127.0.0.1:55432`), terpisah dari GeoNode. Kredensial hanya di `data-pipeline/.env` (salin dari `.env.example`, di-ignore git).

| Perintah | Fungsi |
|----------|--------|
| `data-pipeline/docker/db.sh naik` | Nyalakan dan tunggu siap. |
| `data-pipeline/docker/db.sh mati` | Hentikan (data tetap di volume). |
| `data-pipeline/docker/db.sh reset --ya` | **Hapus** kontainer + volume spectra lalu nyalakan lagi (semua data dev hilang). |
| `data-pipeline/docker/db.sh status` / `psql` | Status / shell psql. |
| `data-pipeline/docker/db.sh dump data-pipeline/spectra_dev.dump` | Cadangan `pg_dump -Fc`. |
| `data-pipeline/docker/db.sh restore data-pipeline/spectra_dev.dump` | Pulihkan dengan `pg_restore`. |

## 2. Migrasi skema
`data-pipeline/.venv/bin/python data-pipeline/db/migrate.py` menjalankan `db/migrations/NNNN_*.sql` berurutan, tiap migrasi
satu transaksi, checksum dicatat di `public.schema_migrasi` (migrasi yang sudah jalan tidak boleh diubah). `--status` melihat daftar.
Skema diubah **hanya** lewat berkas migrasi baru.

## 3. Impor CityGML → PostGIS
```
data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/muat.py --slug bontang_lestari --jenis uji_coba
```
Membaca sumber aktif di `config/citygml_sources.yaml` (streaming), membersihkan, mencocokkan registri (ADR-003), menulis
`core.bangunan` dan laporan `reports/impor_<slug>_batch<id>.json`. Impor ulang tidak menerbitkan ID baru bila data sama.

## 4. Ekspor CityJSONSeq
```
data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/ekspor.py --slug bontang_lestari
```
→ `processed/buildings/bontang_lestari.city.jsonl` (hanya tinggi ≥ 0,1 m).

Validasi skema CityJSON 2.0.2 (skema lokal di `schemas/cityjson-2.0/`, paket `jsonschema`; ±50 s per 2.000 bangunan):
```
data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/validasi_cityjson.py data-pipeline/processed/buildings/bontang_lestari.city.jsonl
```
atau tambahkan `--validasi` pada `ekspor.py`. Kode keluar 1 bila ada galat skema; peringatan geometri (titik berulang berurutan, vertex
tidak dipakai/kembar) hanya dihitung. Bontang Lestari (2026-11-20): 0 galat skema, 15 peringatan titik berulang berurutan (pembulatan 1 mm).

## 5. Tile 3D (tyler, Docker)
```
data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/buat_tile.py --slug bontang_lestari
```
Menyalin `processed/buildings/<slug>.city.jsonl` ke folder kerja `processed/tyler_work/<slug>/` (di-ignore git; tyler menulis indeks
sqlite di sana), mengosongkan lalu mengisi `processed/3dtiles_v2/<slug>/`, dan mencatat perintah, versi tyler, dan image di
`tileset.json` → `asset.extras.spectra`. Tidak bergantung pada `/tmp`. Perintah tyler yang dijalankan:
`tyler --object-type Building --object-attributes id:string,gml_id:string,nama:string,tinggi:float,jumlah_lantai:int,luas_tapak:float --color-building <warna> --3dtiles-metadata-class bangunan`.

**Warna:** `<warna>` dibaca dari `config/citygml_sources.yaml` (`umum.warna_bangunan_tyler`, **#B1BAC2**). tyler memperlakukan hex sebagai nilai
linear (`baseColorFactor` = hex/255), jadi #B1BAC2 tampil sebagai #D9DEE2, sesuai legenda frontend. Tile uji coba Bontang Lestari yang ada
sekarang masih dibuat dengan #D9DEE2 (≈9% lebih terang dari legenda); nilai baru dipakai saat impor resmi.

## 6. Master hibrida dan uji tampil
```
python3 data-pipeline/scripts/04_build_master.py --v2 bontang_lestari --master-out data-pipeline/processed/3dtiles_v2/master-tileset.json
```
Tambahkan `--sync` untuk menyalin ke `frontend/public/tiles/`. **Sebelum `--sync`**, buat cadangan dan uji pengembalian:
```
rsync -a frontend/public/tiles/ data-pipeline/processed/backup_public_tiles/            # cadangan (di-ignore git)
rsync -a --delete data-pipeline/processed/backup_public_tiles/ frontend/public/tiles/   # PENGEMBALIAN
(cd frontend/public/tiles && sha256sum -c --quiet ../../../data-pipeline/reports/hash_baseline_public_tiles.txt)
```
Uji tampil di Chromium headless (frontend `npm run dev` di :3000 harus jalan; `sebelum` memakai tile lama dari cadangan lewat
page.route, `sesudah` memakai isi `public/tiles`): `node data-pipeline/scripts/citygml/uji_tampil.cjs sebelum|sesudah`.
Hasil (PNG + log JSON) ke `reports/uji_tampil_bontang_lestari/`.

## Baseline hash (reports/)
Hash berkas yang tidak boleh berubah disimpan di `reports/hash_baseline_*.txt` (bukan `/tmp`): `raw_bontang_lestari` (8 berkas CityGML),
`3dtiles_lama` (`processed/3dtiles/`), `public_tiles` (`frontend/public/tiles/`). Bandingkan dengan
`sha256sum -c` dari root repo (untuk `3dtiles_lama` dan `public_tiles`: dari dalam folder masing-masing). Catatan: baseline
pertama dibuat 2026-11-20 setelah baseline awal di `/tmp` hilang; untuk tahap berikutnya buat baseline **sebelum** mulai bekerja.

## Uji
`data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/test_citygml.py` dan `test_registri.py` (tanpa jaringan/DB).

## Batasan data (baca sebelum memakai atribut bangunan)
- `tinggi` dan `jumlah_lantai` berasal dari **model GeoAI** (hasil ekstraksi otomatis), bukan survei. `tinggi` dihitung ulang dari geometri
  (Zmaks − Zmin; selisih dengan `measuredHeight` sumber ≤ 0,005 m), tetapi nilainya tetap hanya sebaik modelnya.
- `jumlah_lantai` (`storeysAboveGround`) tidak selalu bermakna. Contoh: **BTG-BLD-000700** (tinggi 49,1 m, 9 lantai, luas tapak 18 m²)
  kemungkinan **cerobong**, bukan gedung; jumlah lantainya tidak bermakna. Jangan dipakai untuk statistik hunian tanpa penyaringan.
- Bangunan Berebas Tengah (CityGML 3.0) tidak punya `jumlah_lantai`; tile lama dan uji coba ini belum menguji berkas itu.
- ID `BTG-BLD-xxxxxx` pada basis data dev berstatus `uji_coba` dan **bukan** ID resmi.

## Catatan
- Validasi skema memakai `jsonschema` + skema lokal (`schemas/cityjson-2.0/`), bukan `cjio validate`: `cjvalpy` tidak punya wheel Linux
  untuk Python 3.14 (versi terbaru hanya macOS/Windows, Python ≤ 3.11). `cjio info` tetap berguna untuk ringkasan.
- Paket baru di `requirements.txt`: `psycopg[binary]` (koneksi PostGIS) dan `jsonschema` (+ dependensinya).
