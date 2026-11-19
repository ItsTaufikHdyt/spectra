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

### Aturan pencocokan registri (setiap impor; **direncanakan**)
Untuk tiap bangunan dari impor baru, dicari bangunan yang sudah punya ID, berurutan:
1. **Cocok lewat `gml_id`:** `gml_id` sama, kelurahan sama, `gml_id` itu unik di dalam batch impor, dan pusat footprint bergeser **≤ 2 m**.
2. **Jika tidak, cocok lewat posisi:** pusat footprint **≤ 2 m** dan **IoU footprint ≥ 0,5**.
3. **Lebih dari satu kandidat:** pilih IoU tertinggi; bila selisih IoU antara dua teratas **< 0,1**, bangunan masuk **daftar tinjauan manual dan tidak diberi ID** sampai diputuskan.
4. **Tidak ada kecocokan:** terbitkan ID baru dengan nomor berikutnya.

**Footprint kosong** (bangunan tanpa footprint di salah satu sisi atau kedua sisi): IoU tidak dapat dihitung, jadi aturan 2 dan 3 diganti. Bangunan dianggap sama bila **jarak antar pusat bounding box 3D ≤ 2 m** dan **selisih tinggi ≤ 0,5 m**. Bila ada **lebih dari satu kandidat**, bangunan masuk **daftar tinjauan manual dan tidak diberi ID**. Footprint kosong tidak pernah dianggap IoU 1,0.

### Aturan tetap
- **Nomor ID tidak pernah dipakai ulang**, termasuk untuk bangunan yang sudah tidak aktif.
- Bangunan yang **hilang dari impor baru** ditandai **nonaktif dengan tanggal berakhir**, tidak dihapus.
- **Perubahan geometri atau tinggi** pada bangunan yang sama **memakai ID yang sama**; versi baru dicatat di riwayat.
- **Penomoran pertama deterministik:** urut slug kelurahan, lalu `gml_id`, lalu koordinat pusat footprint.
- **Setiap impor menghasilkan laporan**: jumlah cocok lewat `gml_id`, cocok lewat posisi, ID baru, nonaktif, dan tinjauan manual.

## Alternatif yang dipertimbangkan
- **Memakai `gml:id` sebagai kunci:** tidak unik (bentrok) dan tidak stabil antar-versi ekspor. Ditolak.
- **UUID acak:** unik, tetapi sulit dibaca dan tidak urut; tidak ada keunggulan bagi pengguna. Ditolak.
- **Hash geometri:** berubah ketika geometri dibersihkan atau dinormalkan (ADR-002). Ditolak.
- **ID dari urutan di berkas:** bergantung urutan berkas dan part (penyebab bentrok di CityJSON). Ditolak.

## Konsekuensi
- Aturan pencocokan antar-impor sudah diputuskan (bagian Keputusan); implementasinya, tabel riwayat versi, dan format laporan impor **direncanakan** bersama skema.
- Bangunan pada daftar tinjauan manual belum punya ID dan belum masuk tile sampai diputuskan; ambang (2 m, IoU 0,5, selisih 0,1) dapat disetel setelah impor pertama.
- Registri harus dicadangkan bersama `pg_dump`; CSV di git hanya jaring pengaman dan perlu diperbarui setiap ada ID baru.
- Properti tile baru: `id` dan `gml_id` (dibaca frontend lewat `ID_KEYS`); lookup backend `/buildings/{id}/attributes` memakai `BTG-BLD-xxxxxx`.
- ±103 `gml:id` bentrok tidak lagi menjadi masalah karena kunci adalah `BTG-BLD`, tetapi tetap dicatat sebagai QC sumber.
