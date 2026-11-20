# ADR-007: Duplikat dalam batch impor dan kelurahan administratif

- **Status:** Diterima
- **Tanggal:** 2026-11-20
- **Terkait:** ADR-003 (ID dan registri), ADR-004 (CityGML sumber tunggal); berkas `data-pipeline/config/keputusan_duplikat.yaml`

## Konteks
Sebelum ID resmi pertama diterbitkan, analisis staging seluruh CityGML (51.888 bangunan; `reports/impor_resmi_duplikat_batch1.md`) menemukan **17 kasus duplikat dalam batch** (pusat footprint ≤ 2 m dan IoU ≥ 0,5, atau `gml_id` sama dengan pusat ≤ 2 m). Inventaris hanya memeriksa keunikan **dalam satu kelurahan** dan mencatat 1 kasus; 13 kasus lain adalah **antar kelurahan** (bangunan di perbatasan tercatat di dua berkas).
Bangunan di perbatasan juga membuat kelurahan sumber (folder CityGML) tidak selalu sama dengan kelurahan menurut batas administratif (43 bangunan).

## Keputusan
**Aturan duplikat dalam batch** (diputuskan pemilik proyek; dicatat per kasus di `config/keputusan_duplikat.yaml`):
1. **Antar kelurahan:** pertahankan salinan yang berada di dalam batas administratif kelurahan foldernya; kecualikan salinan dari berkas kelurahan lain (Bontang Baru → Bontang Kuala: 3; Guntung Part III → Satimpo: 8).
2. **Berebas Pantai ↔ Berebas Tengah (2 kasus):** aturan yang sama (pertahankan salinan Berebas Tengah), tetapi `jumlah_lantai` diisi dari salinan Berebas Pantai (CityGML 3.0 tidak punya atribut) dan bangunan diberi flag `atribut_dari_duplikat`.
3. **Gunung Elai Part II/III (1 kasus, geometri berbeda):** pertahankan Part III; flag `duplikat_kepercayaan_rendah`.
4. **`gml_id` sama dengan footprint hampir identik dalam satu berkas (Api Api, 1 kasus):** pertahankan yang lebih tinggi; flag `duplikat_kepercayaan_rendah`.
5. **`gml_id` bentrok pada objek berbeda** (Api Api, Loktuan Part I; 2 kasus): pertahankan keduanya.

Salinan yang dikecualikan **tidak mendapat ID** dan tidak masuk `core.bangunan`, tetapi **tetap disimpan di `staging.bangunan_impor`** dengan `keputusan = 'kecualikan'`, `rujukan_urut`/`rujukan_id` (bangunan yang dipertahankan) dan `alasan_keputusan`. Kunci bangunan di berkas keputusan = `slug` + `sumber_file` + `gml_id` + pusat footprint; impor ulang menerapkan keputusan yang sama (`impor_resmi.py`). Berkas keputusan tidak diubah setelah ID resmi terbit.

**Kolom `kelurahan_administratif`** di `core.bangunan` (migrasi `0005`): kelurahan menurut `batas-kelurahan.norm.geojson` berdasarkan pencocokan spasial pusat footprint (pusat bounding box bila tanpa footprint); `NULL` bila di luar semua batas. Kolom `slug` **tetap kelurahan sumber** dan dipakai untuk pengelompokan tile dan urutan penomoran ID (ADR-003). Bangunan dengan keduanya berbeda diberi flag `kelurahan_beda_dengan_sumber`. `kelurahan_administratif` tidak dimasukkan ke atribut tile.

## Konsekuensi
- ID resmi pertama: 51.888 − 15 = **51.873**.
- Aturan ini berlaku untuk impor pertama; impor berikutnya memakai aturan pencocokan ADR-003 terhadap registri.
- Dua kasus berkepercayaan rendah (Gunung Elai, Api Api) dapat ditinjau ulang lewat riwayat staging; perubahan keputusan setelah ID terbit harus memakai mekanisme ADR-003 (ID tidak dipakai ulang).
