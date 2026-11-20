# data-pipeline — pipeline bangunan

CityGML (`raw/citygml/`, read-only) → PostGIS dev → CityJSONSeq → `tyler` → 3D Tiles (`processed/3dtiles/`).
Status: **impor resmi seluruh 15 kelurahan selesai (2026-11-20)**: 51.873 bangunan ber-ID resmi `BTG-BLD-000001`..`BTG-BLD-051873`.
Registri: `config/registri_id.csv` (+ `.sha256`). **ID resmi tidak boleh diterbitkan ulang atau diedit.** Lihat ADR-001..007 di `docs/adr/`.
Bagian 1–6 di bawah menjelaskan tiap langkah; bagian **Impor penuh (resmi)** merangkum urutannya. `scripts/citygml/muat.py` adalah jalur uji coba
satu kelurahan (registri berstatus `uji_coba`), bukan untuk registri resmi.

Semua perintah dari root repo.
**Folder data (`raw/`, `processed/`, `backups/`, `frontend/public/tiles|geojson/`) tidak ada di repo**; tiap folder punya README panduan, dan ringkasannya ada di `README.md` root (tabel "Data yang tidak ada di repo").

## Impor penuh (resmi) — urutan
Semua perintah dari root repo, dengan `PY=data-pipeline/.venv/bin/python`. **Langkah `terbit` hanya SATU KALI** (sudah dijalankan 2026-11-20); jangan diulang.
1. **Persiapan:** simpan baseline hash `raw/citygml` ke `reports/hash_baseline_raw_citygml.txt` (`find … -name '*.gml' | sort | xargs sha256sum`);
   `data-pipeline/docker/db.sh naik`; (database baru: `db.sh reset --ya`); `$PY data-pipeline/db/migrate.py` (migrasi 0001–0005); periksa
   `config/citygml_sources.yaml` (31 berkas; koreksi EPSG 32748→32650 hanya untuk Guntung Part I/II dan Satimpo, dengan `alasan_koreksi`).
2. **Staging (belum ada ID):** `$PY data-pipeline/scripts/citygml/impor_resmi.py staging` (±5 menit) lalu `... analisis` (jumlah per berkas vs inventaris,
   duplikat dalam batch, posisi vs `batas-kelurahan.norm.geojson`, Z dasar, Berebas Tengah). Laporan di `reports/impor_resmi_*`.
3. **Keputusan:** tulis/ubah `config/keputusan_duplikat.yaml` (ADR-007) lalu `... keputusan` (menerapkan keputusan + mengisi `kelurahan_administratif`).
4. **Terbit ID resmi (SATU KALI):** buat cadangan dulu (`db.sh dump data-pipeline/backups/<nama>.dump`), lalu
   `$PY data-pipeline/scripts/citygml/impor_resmi.py terbit --batch <N> --ya-terbitkan-id-resmi`. Menolak bila registri tidak kosong.
5. **Registri dan stabilitas:** `... ekspor-registri` (→ `config/registri_id.csv` + `.sha256`); `... stabilitas` (impor kedua, HANYA BACA; harus 0 ID baru dan registri tidak berubah).
6. **Ekspor dan validasi (per kelurahan):** `$PY data-pipeline/scripts/citygml/ekspor.py --slug <slug> [--validasi]`
   (validasi skema CityJSON; ±50 detik per 2.000 bangunan, bisa paralel per berkas dengan `validasi_cityjson.py`).
7. **Tile:** `$PY data-pipeline/scripts/citygml/buat_tile.py --slug <slug>` (warna dari `config/citygml_sources.yaml`, `#B1BAC2`); master:
   `python3 data-pipeline/scripts/04_build_master.py` (master di `processed/3dtiles/master-tileset.json`).
8. **Verifikasi:** `node data-pipeline/scripts/citygml/verifikasi_tile.cjs <folder> <json>` per kelurahan, `node data-pipeline/scripts/citygml/fitur_glb.cjs` (segitiga per fitur),
   lalu `$PY data-pipeline/scripts/citygml/laporan_verifikasi.py` → `reports/impor_resmi_verifikasi.{md,json}`.
9. **Uji tampil dan sinkron ke frontend:** bagian 6 di bawah; `node data-pipeline/scripts/citygml/uji_impor_resmi.cjs klik|fps`
   (hasil: `reports/uji_tampil_impor_resmi/README.md`).
Catatan perilaku tyler: `jumlah_lantai`/`luas_tapak` kosong disimpan sebagai `noData` (bukan 0); kolom properti dihilangkan dari tile yang tidak punya satu nilai pun.

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
sqlite di sana), mengosongkan lalu mengisi `processed/3dtiles/<slug>/`, dan mencatat perintah, versi tyler, dan image di
`tileset.json` → `asset.extras.spectra`. Tidak bergantung pada `/tmp`. Perintah tyler yang dijalankan:
`tyler --object-type Building --object-attributes id:string,gml_id:string,nama:string,tinggi:float,jumlah_lantai:int,luas_tapak:float --color-building <warna> --3dtiles-metadata-class bangunan`.

**Warna:** `<warna>` dibaca dari `config/citygml_sources.yaml` (`umum.warna_bangunan_tyler`, **#B1BAC2**). tyler memperlakukan hex sebagai nilai
linear (`baseColorFactor` = hex/255), jadi #B1BAC2 tampil sebagai #D9DEE2, sesuai legenda frontend. Tile uji coba Bontang Lestari yang ada
sekarang masih dibuat dengan #D9DEE2 (≈9% lebih terang dari legenda); nilai baru dipakai saat impor resmi.

## 6. Master, sinkron ke frontend, dan uji tampil
```
python3 data-pipeline/scripts/04_build_master.py          # bangun processed/3dtiles/master-tileset.json (validasi 15 kelurahan)
python3 data-pipeline/scripts/04_build_master.py --sync   # + salin inkremental ke frontend/public/tiles/ (tanpa tileset_unpruned.json)
(cd frontend/public/tiles && sha256sum -c --quiet ../../../data-pipeline/reports/hash_baseline_public_tiles_v2.txt)   # isi harus identik dengan baseline
```
`frontend/public/tiles/` hanya salinan dev (ter-ignore git); sumbernya `processed/3dtiles/`. Tidak ada lagi cadangan tile lama: bila `public/tiles` rusak,
jalankan `--sync` ulang (atau bangun ulang tile dari PostGIS dengan `ekspor.py` + `buat_tile.py`).
Uji tampil di Chromium headless (frontend `npm run dev` di :3000 dan backend harus jalan): `node data-pipeline/scripts/citygml/uji_impor_resmi.cjs klik|fps`;
hasil di `reports/uji_tampil_impor_resmi/`.

## Baseline hash (reports/)
Hash berkas yang tidak boleh berubah disimpan di `reports/hash_baseline_*.txt` (bukan `/tmp`): `raw_citygml` (31 berkas CityGML) dan `public_tiles_v2` (`frontend/public/tiles/`, 156 berkas). Bandingkan dengan
`sha256sum -c` dari root repo (untuk `public_tiles_v2`: dari dalam `frontend/public/tiles/`). Baseline lain (`raw_bontang_lestari`, `3dtiles_lama`, `public_tiles`) adalah riwayat uji coba; datanya sudah tidak ada. Catatan: baseline
pertama dibuat 2026-11-20 setelah baseline awal di `/tmp` hilang; untuk tahap berikutnya buat baseline **sebelum** mulai bekerja.

## Cadangan dan pemulihan database (`backups/`, di-ignore git)
Cadangan: `data-pipeline/docker/db.sh dump data-pipeline/backups/<nama>.dump` (`pg_dump -Fc` di dalam kontainer). Cadangan impor resmi:
`backups/spectra_dev_pra_terbit_batch1.dump` (staging sebelum ID terbit) dan `backups/spectra_dev_pasca_terbit_batch1.dump` (51.873 ID resmi).
Pemulihan **ke database kosong** (uji 2026-11-20: 51.873 registri, 51.873 bangunan, 51.888 staging pulih utuh):
```
data-pipeline/docker/db.sh naik
data-pipeline/docker/db.sh reset --ya                 # HANYA bila ingin mengosongkan database dev (menghapus data!)
data-pipeline/docker/db.sh restore data-pipeline/backups/spectra_dev_pasca_terbit_batch1.dump
```
Bila `restore` ke database yang sudah berisi skema, kosongkan dulu (`reset --ya`) agar tidak bentrok; `restore` memakai `pg_restore --no-owner`.
Registri ID juga ada di `config/registri_id.csv` (+ `.sha256`, di-commit) sebagai jaring pengaman bila basis data hilang.

## Uji
`data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/test_citygml.py` dan `test_registri.py` (tanpa jaringan/DB).

## Batasan data (baca sebelum memakai atribut bangunan)
- `tinggi` dan `jumlah_lantai` berasal dari **model GeoAI** (hasil ekstraksi otomatis), bukan survei. `tinggi` dihitung ulang dari geometri
  (Zmaks − Zmin; selisih dengan `measuredHeight` sumber ≤ 0,005 m), tetapi nilainya tetap hanya sebaik modelnya.
- `jumlah_lantai` (`storeysAboveGround`) tidak selalu bermakna. Contoh: **BTG-BLD-000700** (tinggi 49,1 m, 9 lantai, luas tapak 18 m²)
  kemungkinan **cerobong**, bukan gedung; jumlah lantainya tidak bermakna. Jangan dipakai untuk statistik hunian tanpa penyaringan.
- Bangunan Berebas Tengah (CityGML 3.0) tidak punya `jumlah_lantai` (NULL, bukan 0; tile menyimpannya sebagai `noData`).
- ID `BTG-BLD-xxxxxx` di basis data dev adalah ID **resmi** (batch 1, 2026-11-20); jalur `muat.py` (uji coba) memakai status `uji_coba` dan tidak boleh dipakai pada registri resmi.

## Flag QC (`qc_flag` di `core.bangunan`)
Dipasang oleh pipeline (parser/pembersihan `citygml/bangunan.py`, `impor_resmi.py keputusan`); bukan perubahan manual. Jumlah pada impor resmi (51.873 bangunan) di `reports/impor_resmi_verifikasi.md`.

| Flag | Arti |
|---|---|
| `epsg_dikoreksi` | Label EPSG berkas (32748) dikoreksi ke 32650 lewat konfigurasi eksplisit |
| `tanpa_geometri` | Bangunan tanpa poligon |
| `z_dasar_tidak_nol_di_sumber` | Z dasar sumber (Zmin) \|z\| > 5 cm; dinormalkan ke 0, nilai asli di `z_dasar_sumber` |
| `tanpa_footprint` | Tidak ada permukaan lantai; `luas_tapak` NULL, pusat dari bounding box (aturan footprint kosong ADR-003) |
| `footprint_kurang_2m2` | Luas footprint < 2 m² (hanya ditandai) |
| `footprint_mikro` | Luas footprint **mentah** < 0,01 m² (serpihan; `luas_tapak` terbulatkan 0,00 atau 0,01). Ambang `AMBANG_TAPAK_MIKRO` di `citygml/bangunan.py`; data lama diberi flag lewat `impor_resmi.py qc-ulang` (hanya `qc_flag`; ID, registri, geometri, tile tidak berubah). Impor resmi: 22 bangunan (18 masuk tile) |
| `footprint_diperbaiki` | Footprint tidak valid diperbaiki (`make_valid`) |
| `tinggi_kurang_0_1m` | Tinggi < 0,1 m: tidak masuk tile |
| `tinggi_lebih_40m` | Tinggi > 40 m (perlu ditinjau; mis. cerobong) |
| `tanpa_atap` | Tidak ada permukaan atap |
| `tinggi_sumber_nol` / `tinggi_sumber_beda` | `measuredHeight` sumber 0 / beda > 5 cm dari tinggi hitung |
| `gml_id_bentrok` | `gml_id` sama dengan bangunan lain dalam batch kelurahan yang sama (bukan kunci) |
| `kelurahan_beda_dengan_sumber` | `kelurahan_administratif` ≠ `slug` sumber (ADR-007) |
| `atribut_dari_duplikat` | `jumlah_lantai` diisi dari salinan duplikat yang dikecualikan (ADR-007) |
| `duplikat_kepercayaan_rendah` | Dipertahankan atas keputusan duplikat berkepercayaan rendah (ADR-007) |

## Catatan
- Validasi skema memakai `jsonschema` + skema lokal (`schemas/cityjson-2.0/`), bukan `cjio validate`: `cjvalpy` tidak punya wheel Linux
  untuk Python 3.14 (versi terbaru hanya macOS/Windows, Python ≤ 3.11). `cjio info` tetap berguna untuk ringkasan.
- Paket baru di `requirements.txt`: `psycopg[binary]` (koneksi PostGIS) dan `jsonschema` (+ dependensinya).
