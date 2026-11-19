# ADR-001: PostGIS sebagai sumber kebenaran data

- **Status:** Diterima
- **Tanggal:** 2026-11-19
- **Terkait:** ADR-003 (ID bangunan), ADR-004 (sumber tunggal CityGML), ADR-006 (hasil simulasi)

> Bagian "Keputusan" menjelaskan arsitektur yang **direncanakan**. Per tanggal ini belum ada PostGIS, migrasi, maupun skema di repo.

## Konteks
- Data bangunan (51.888 bangunan, 15 kelurahan) kini hanya berupa berkas: CityJSON, CityGML, dan tile `.glb`. Tidak ada tempat untuk query spasial, atribut bangunan, QC, atau hasil simulasi.
- Audit 2026-11-19 menemukan ID bangunan tidak stabil (ID di tile = path tile + `featureId`), ±4.779 bangunan hilang saat merge berdasarkan berkas, dan atribut tidak sampai ke tile. Berkas tidak cukup untuk menjaga konsistensi ini.
- Simulasi banjir membutuhkan footprint, tinggi, dan elevasi per bangunan yang dapat di-query serta hasil per skenario yang dapat dirujuk dengan ID bangunan.
- Di mesin pengembangan sudah ada image `geonode/postgis:15-3.5-latest` milik GeoNode (geoportal). Basis data itu bukan milik proyek ini.

## Keputusan
1. **PostGIS menjadi sumber kebenaran** data bangunan dan data spasial turunan. Tile, CityJSONSeq, dan ekspor lain adalah **turunan** yang dapat dibangun ulang dari basis data.
2. PostGIS dijalankan **di Docker untuk pengembangan, terpisah dari basis data GeoNode** (kontainer, volume, dan kredensial sendiri; kredensial hanya lewat `.env` yang di-ignore).
3. **Skema dikelola sebagai migrasi di repo** (bukan perubahan manual). Skema rencana: `core` (bangunan, registri ID), `ref` (referensi: kelurahan, RT, sungai, kode), `elevasi` (DTM/DEM dan elevasi dasar), `sim` (hasil simulasi), `staging` (impor mentah sementara). Rincian di PRD §9.
4. **Cadangan dengan `pg_dump`**; berkas cadangan disimpan di luar git.
5. Data mentah `data-pipeline/raw/` tetap read-only dan di luar basis data.

## Alternatif yang dipertimbangkan
- **Tetap berkas (CityJSON/GeoJSON/GeoPackage):** sederhana, tetapi tidak ada query spasial, tidak ada integritas ID, dan hasil simulasi sulit dirujuk. Ditolak.
- **3DCityDB:** skema CityGML siap pakai, tetapi berat, perlu pemetaan ke ID kita sendiri, dan tidak menyimpan hasil simulasi. Ditolak untuk tahap ini.
- **Memakai basis data GeoNode:** menyatukan siklus hidup dan risiko dua sistem; kegagalan salah satunya memengaruhi yang lain. Ditolak.
- **SQLite/GeoPackage:** cocok untuk satu pengguna; kurang untuk backend multi-proses dan simulasi. Ditolak.

## Konsekuensi
- Perlu Docker Compose pengembangan, kebijakan migrasi, dan jadwal `pg_dump` (**direncanakan**, belum ada).
- Backend FastAPI (ADR-005) membaca dari PostGIS; kontrak `GET /buildings/{id}/attributes` di frontend dapat dipenuhi tanpa mengubah frontend (**direncanakan**).
- Pipeline berubah: parser → PostGIS → ekspor → tile (ADR-004). Tile lama tetap sebagai cadangan.
- Registri ID bangunan menjadi data penting yang harus dicadangkan, termasuk ekspor CSV di git (ADR-003).
- PostGIS produksi (lokasi, akses, pencadangan) belum diputuskan.
