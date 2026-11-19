# ADR-003: Skema ID bangunan dan registri

- **Status:** Diterima
- **Tanggal:** 2026-11-19
- **Terkait:** ADR-001 (PostGIS), ADR-004 (CityGML), ADR-006 (simulasi merujuk ID bangunan)

> Skema ID, tabel `core.registri_id`, dan ekspor CSV **direncanakan**; belum ada yang dibuat.

## Konteks
- ID bangunan di tile saat ini = path tile + `featureId` (`<slug>/<tile>#<id>`): tidak stabil antar-ETL, sehingga atribut dan hasil simulasi tidak dapat dirujuk.
- Di CityJSON lama, ID numerik ternyata **nomor di `gml:description`** dan dimulai dari 1 di setiap part, sehingga bentrok antar part dan diduga menyebabkan ±4.779 bangunan hilang saat merge.
- `gml:id` di CityGML tidak unik: ±103 bangunan berbeda berbagi `gml:id` dalam satu file (17 file) dan 2 `gml:id` muncul di dua file (Loktuan). Prefiks tidak selalu sesuai kelurahan (mis. `LK_` di Bontang Lestari Part VIII). Nomor urut di dalam `gml:id` memiliki banyak lompatan.
- Untuk Satimpo, Kanaan, dan Tanjung Laut Indah, `gml:id` CityGML terbaru tidak sama dengan ID CityJSON lama.
- Frontend sudah mencari ID di properti `id`, `gml_id`, `gmlId`, `identifier`, atau `objectid` (`use3DTiles.js`), dan kontrak lookup `buildingAttributes.js` memakai ID bangunan.

## Keputusan
1. ID bangunan berformat **`BTG-BLD-xxxxxx`** (nomor urut enam digit), **dibuat sekali** saat bangunan pertama kali masuk dan **tidak pernah dibuat ulang**.
2. ID disimpan di **registri** (tabel `core.registri_id`) di PostGIS; registri adalah satu-satunya tempat ID baru diterbitkan.
3. **`gml_id` asli disimpan sebagai rujukan** (kolom biasa, **boleh tidak unik**), bukan sebagai kunci.
4. Registri **diekspor ke CSV di `data-pipeline/config/` dan di-commit ke git** sebagai jaring pengaman jika basis data hilang.
5. Di tile, `id` = `BTG-BLD-xxxxxx` dan `gml_id` = ID asli; nama tampil "Bangunan BTG-BLD-xxxxxx" (ADR-004).

## Alternatif yang dipertimbangkan
- **Memakai `gml:id` sebagai kunci:** tidak unik (bentrok) dan tidak stabil antar-versi ekspor. Ditolak.
- **UUID acak:** unik, tetapi sulit dibaca dan tidak urut; tidak ada keunggulan bagi pengguna. Ditolak.
- **Hash geometri:** berubah ketika geometri dibersihkan atau dinormalkan (ADR-002). Ditolak.
- **ID dari urutan di berkas:** bergantung urutan berkas dan part (penyebab bentrok di CityJSON). Ditolak.

## Konsekuensi
- Aturan pencocokan "bangunan yang sama" antar-impor (agar ID tidak diterbitkan dua kali) harus dirancang bersama skema (**belum diputuskan**).
- Registri harus dicadangkan bersama `pg_dump`; CSV di git hanya jaring pengaman dan perlu diperbarui setiap ada ID baru.
- Properti tile baru: `id` dan `gml_id` (dibaca frontend lewat `ID_KEYS`); lookup backend `/buildings/{id}/attributes` memakai `BTG-BLD-xxxxxx`.
- ±103 `gml:id` bentrok tidak lagi menjadi masalah karena kunci adalah `BTG-BLD`, tetapi tetap dicatat sebagai QC sumber.
