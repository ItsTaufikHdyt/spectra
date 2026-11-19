# ADR-004: CityGML sebagai sumber tunggal, CityJSON lama diarsipkan

- **Status:** Diterima
- **Tanggal:** 2026-11-19
- **Terkait:** ADR-001, ADR-002, ADR-003, ADR-006

> Seluruh pipeline pada bagian "Keputusan" **direncanakan** dan belum ada di repo. Tile saat ini (`processed/3dtiles/`, 47.108 fitur) masih berasal dari CityJSON lama.

## Konteks
- `data-pipeline/raw/citygml/` berisi 31 file CityGML (30 versi 2.0, 1 versi 3.0 untuk Berebas Tengah; 3,5 GB), memuat **51.888 bangunan** (51.887 unik berdasarkan posisi) di 15 kelurahan. Semua XML valid.
- CityJSON di `raw/3d/` (37 file) hanya berisi 51.883 bangunan unik, tanpa atribut, dengan Z dinormalkan ke 0, dan tile yang dibuat darinya hanya memuat 47.108 bangunan: **±4.779 bangunan hilang** (Gunung Elai 1.897, Bontang Lestari 1.445, Belimbing 1.349, Loktuan 87) akibat merge berdasarkan ID numerik.
- CityGML membawa atribut (`measuredHeight`, `storeysAboveGround`; atribut lain bernilai bawaan), `gml:id` asli, dan seluruh part tanpa tumpang tindih (Loktuan Part II–IV adalah 87 bangunan tambahan).
- Anomali sumber: 3 file berlabel EPSG:32748 padahal koordinatnya EPSG:32650 (Guntung Part I, Guntung Part II, Satimpo); 5 file Z dasar tidak konsisten; Berebas Tengah (CityGML 3.0) tanpa atribut; ±103 `gml:id` bentrok dalam file.
- Peralatan tersedia: `cjio` hanya membaca CityJSON; `citygml-tools` tidak ada; GDAL tidak memiliki driver CityGML; `tyler` tersedia lewat Docker (`3dgi/tyler:latest`, 1.0.0-alpha1) dan menerima CityJSON/CityJSONSeq.

## Keputusan
1. **CityGML di `data-pipeline/raw/citygml/` adalah sumber data bangunan tunggal.** `raw/3d/` (CityJSON) menjadi **arsip** dan tidak dipakai lagi. `raw/citygml/` read-only.
2. **Pipeline (direncanakan):** parser streaming milik sendiri → PostGIS (sumber kebenaran, ADR-001) → ekspor CityJSONSeq yang bersih per kelurahan → `tyler` (Docker `3dgi/tyler`) → `processed/3dtiles_v2/<slug>/` → `04_build_master.py --sync`. **Tile lama (`processed/3dtiles/`) tetap sebagai cadangan** sampai tile baru diverifikasi.
3. **Semua part per kelurahan disatukan** (termasuk Loktuan Part II–IV), bukan ditimpa berdasarkan ID.
4. **Label EPSG:32748 dikoreksi menjadi EPSG:32650 lewat konfigurasi eksplisit per file** (tiga file di atas), bukan lewat tebakan otomatis.
5. **Atribut di tile:** `id`, `gml_id`, `nama` ("Bangunan BTG-BLD-xxxxxx"), `tinggi`, `jumlah_lantai`, `luas_tapak`. Nilai bawaan CityGML (class, function, usage, roofType, yearOfConstruction, GrossPlannedArea, dst.) **tidak dibawa** ke tile. Berebas Tengah: `tinggi` dari geometri, `jumlah_lantai` kosong.
6. **Warna model `#D9DEE2`** agar sesuai legenda frontend (`MAP_COLORS.building`); model saat ini berwarna `#D8C3A5`.
7. Pembersihan geometri, normalisasi Z, dan tanda QC mengikuti ADR-002; ID mengikuti ADR-003.

## Alternatif yang dipertimbangkan
- **Memperbaiki merge CityJSON:** CityJSON tidak membawa atribut dan ID asli, dan hanya 51.883 bangunan; menambal sumber turunan lebih rumit daripada memakai sumbernya. Ditolak.
- **Mengunduh `citygml-tools`:** butuh jaringan dan menambah dependensi; parser streaming sendiri sudah terbukti pada inventaris (31 file, 3,5 GB). Ditolak untuk tahap ini.
- **Mempertahankan dua sumber (CityGML dan CityJSON):** ID dan versi ekspor berbeda (Satimpo, Kanaan, Tanjung Laut Indah), menimbulkan konflik. Ditolak.

## Konsekuensi
- Perlu parser CityGML 2.0 dan 3.0, konfigurasi per berkas (koreksi CRS), dan skrip ekspor CityJSONSeq (**direncanakan**).
- `04_build_master.py` saat ini membaca `processed/3dtiles/`; dukungan `3dtiles_v2` perlu disesuaikan (**direncanakan**, kode belum diubah).
- Frontend tidak berubah: kontrak tile (slug, `boundingVolume.region`, properti `id`/`gml_id`/`nama`/`tinggi`) dijaga (AGENTS.md §4).
- Struktur tile baru perlu diuji di viewer (picking `Cesium3DTileFeature`) sebelum menggantikan tile lama.
