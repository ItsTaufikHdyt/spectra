# ADR-002: Geometri bangunan: bersihkan LOD2, bukan ekstrusi LOD1

- **Status:** Diterima
- **Tanggal:** 2026-11-19
- **Terkait:** ADR-004 (sumber CityGML), PRD §3.1 (aturan geometri bangunan vs terrain), ADR-006

> Pembersihan, normalisasi Z, dan tanda QC di bawah **direncanakan**; belum ada yang diimplementasikan.

## Konteks
Hasil inventaris CityGML (`data-pipeline/reports/citygml_inventory.md`, 51.888 bangunan LOD2):
- **76,4% bangunan beratap miring**, 13,7% datar satu tingkat, 9,6% datar bertingkat, 0,4% tanpa atap.
- **99,86% poligon punya salinan terbalik** (setiap permukaan muncul dua kali); sebagian file juga memuat duplikat searah (0–14%). Label `RoofSurface` dan `GroundSurface` pada salinan itu tertukar (35.735 bangunan memiliki `RoofSurface` di dasar).
- Footprint dapat dibentuk menjadi poligon valid untuk 99,86% bangunan; 73 bangunan tanpa poligon dasar; 205 footprint < 2 m².
- `measuredHeight` identik dengan tinggi geometri (selisih maksimum 0,005 m), sehingga LOD1 dapat diturunkan tanpa kehilangan informasi tinggi.
- Z dasar tidak konsisten: 26 file berbasis 0,001 m, 5 file berelevasi dasar bervariasi (median −15,4 m s.d. +5,4 m). Frontend belum punya terrain.
- 22 bangunan ber-`measuredHeight` 0 dan 57 bangunan setinggi < 0,1 m.

## Keputusan
1. **Bersihkan geometri LOD2 asli**: buang salinan terbalik dan duplikat searah, perbaiki label permukaan yang tertukar. **Tidak** mengekstrusi ulang footprint menjadi LOD1 untuk tampilan (PRD §3.1 tetap berlaku).
2. **LOD1 boleh diturunkan** (footprint × tinggi) sebagai produk sampingan **untuk analisis**, bukan untuk tampilan.
3. **Z dasar dinormalkan ke 0 per bangunan untuk tile**, karena belum ada terrain. Z dasar asli disimpan di basis data sebagai `z_dasar_sumber` (ADR-001).
4. **Aturan QC:** bangunan dengan tinggi < 0,1 m **tidak masuk tile** tetapi tetap di basis data dengan `qc_flag`; footprint < 2 m² **ditandai** (`qc_flag`), tidak dibuang.

## Alternatif yang dipertimbangkan
- **Ekstrusi LOD1 dari footprint:** sederhana dan ringan, tetapi meratakan atap tiga dari empat bangunan dan membuang nilai LOD2 yang sudah dibayar. Ditolak untuk tampilan.
- **Memakai LOD2 apa adanya:** menggandakan jumlah segitiga dan membawa label yang salah. Ditolak.
- **Mempertahankan Z absolut:** bangunan melayang atau tenggelam di globe tanpa terrain. Ditolak sampai terrain tersedia.

## Konsekuensi
- Segitiga berkurang ±separuh setelah salinan terbalik dibuang (dugaan dari persentase poligon; diverifikasi saat pipeline dibuat).
- Atap dan footprint harus dihitung ulang setelah normalisasi Z, terutama untuk 5 file berelevasi bervariasi.
- Perlu aturan perbaikan untuk ±283 bangunan dengan komponen footprint tidak valid dan 73 tanpa poligon dasar.
- Saat terrain ada, normalisasi Z perlu ditinjau (bangunan dapat diletakkan memakai `z_dasar_sumber` atau elevasi terrain; keputusan terpisah).
