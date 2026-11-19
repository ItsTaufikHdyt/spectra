# Inventaris CityGML Kota Bontang — 2026-11-19

Investigasi read-only terhadap `data-pipeline/raw/citygml/` dan kontrak frontend. Tidak ada file di `raw/`, `processed/`, `frontend/`, atau `backend/` yang diubah. Data mentah lengkap: `citygml_inventory.json`.

**Penanda bukti:** **[V]** dijalankan atau dibaca langsung hari ini; **[D]** diduga (kesimpulan dari pola, bukan bukti langsung).

**Metode:** tiap file CityGML dibaca streaming (blok 16 MB, dipotong per `cityObjectMember`, diparse per bangunan; XML divalidasi penuh dengan `expat`). Pencocokan posisi memakai pusat bounding box 2D (atau centroid footprint) dengan toleransi 2 m. Skrip ada di `/tmp/cg` (bukan di repo).

## a. Ringkasan

1. **Cakupan [V]:** 15 dari 15 kelurahan punya CityGML: 31 file `.gml` (3,50 GB) + 1 `.gfs`. Semua XML valid. 30 file CityGML 2.0, **1 file CityGML 3.0** (Berebas Tengah).
2. **Bangunan [V]:** 51.888 (unik berdasarkan posisi: 51.887), tanpa `BuildingPart`. Angka ini hampir sama dengan CityJSON (51.883 unik) dan **4.779 lebih banyak dari tile saat ini** (47.108). Jadi CityGML **lengkap**; bangunan yang hilang di tile (audit 19 Nov) ada di sini.
3. **Atribut [V]:** 14 kelurahan (93,5% bangunan) membawa atribut, tetapi hanya `measuredHeight` (1.704 nilai unik) dan `storeysAboveGround` (0–13, 94,5% bernilai 1) yang informatif; 11 atribut lain bernilai bawaan sama untuk semua bangunan. `measuredHeight` hanyalah tinggi geometri yang dibulatkan 2 desimal (selisih maks 0,005 m). Berebas Tengah (CityGML 3.0) **tanpa atribut sama sekali**.
4. **Geometri [V]:** LOD2; 99,86% poligon punya pasangan terbalik (setiap permukaan ganda); 35.735 bangunan (68,9%) punya poligon berlabel `RoofSurface` di dasar bangunan (label tertukar pada salinan terbalik). Atap: 76,4% miring, 13,7% datar satu tingkat, 9,6% datar bertingkat. Footprint valid 99,86%.
5. **Tiga temuan terpenting:** (a) **ketinggian dasar tidak konsisten**: 5 file berelevasi absolut/bervariasi (median −15,4 m sampai +5,4 m), sedangkan 26 file bertumpu di 0,001 m, dan CityJSON lama dinormalkan ke 0; (b) **ID**: ±103 bangunan berbagi `gml:id` dengan bangunan lain di file yang sama (bukan salinan), nomor urut `gml:id` punya banyak lompatan, dan ID numerik CityJSON ternyata **nomor di `gml:description`** (bukan `gml:id`); (c) **3 file berlabel EPSG:32748** (UTM 48S) padahal koordinatnya identik dengan data EPSG:32650.
6. **Kontrak frontend [V]:** tile harus `processed/3dtiles/<slug>/tileset.json` (3D Tiles 1.1, `boundingVolume.region`, konten `.glb`), slug = nama kelurahan huruf kecil bergaris bawah. Atribut dibaca dari `EXT_structural_metadata` apa adanya (semua properti tampil; nama = `name`/`nama`; ID = `id`/`gml_id`/…). Tanpa mengubah frontend, bangunan harus berbasis Z ≈ 0 (globe tanpa terrain).
7. **Rekomendasi ADR-002 (awal):** bersihkan geometri LOD2 asli, jangan ekstrusi LOD1 (bagian e).

## b. Tabel per kelurahan

Atap dihitung setelah mengecualikan salinan terbalik lantai yang berlabel `RoofSurface`. "Unik" = posisi (toleransi 2 m) lintas file kelurahan. "Δ tile" = bangunan unik CityGML dikurangi fitur di tile.

| Kelurahan | File | Versi | Bangunan (semua file) | Unik | Tinggi % | Lantai % | Atap datar % | Atap miring % | CityJSON unik | Fitur tile | Δ tile |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Api Api | 1 | 2.0 | 5.142 | 5.142 | 100,0 | 100,0 | 20,7 | 79,0 | 5.142 | 5.142 | 0 |
| Belimbing | 3 | 2.0 | 4.645 | 4.645 | 100,0 | 100,0 | 18,5 | 81,5 | 4.643 | 3.296 | 1.349 |
| Berebas Pantai | 1 | 2.0 | 2.022 | 2.022 | 100,0 | 100,0 | 22,9 | 77,1 | 2.024 | 2.024 | -2 |
| Berebas Tengah | 1 | 3.0 | 3.390 | 3.390 | 0,0 | 0,0 | 25,1 | 74,8 | 3.390 | 3.390 | 0 |
| Bontang Baru | 1 | 2.0 | 4.147 | 4.147 | 100,0 | 100,0 | 28,0 | 71,2 | 4.147 | 4.147 | 0 |
| Bontang Kuala | 1 | 2.0 | 2.366 | 2.366 | 100,0 | 100,0 | 19,1 | 80,7 | 2.366 | 2.366 | 0 |
| Bontang Lestari | 8 | 2.0 | 2.219 | 2.219 | 100,0 | 100,0 | 62,1 | 36,5 | 2.219 | 774 | 1.445 |
| Guntung | 3 | 2.0 | 2.059 | 2.059 | 100,0 | 100,0 | 15,5 | 84,2 | 2.057 | 2.057 | 2 |
| Gunung Elai | 3 | 2.0 | 4.469 | 4.468 | 100,0 | 100,0 | 18,5 | 81,2 | 4.468 | 2.571 | 1.897 |
| Gunung Telihan | 1 | 2.0 | 3.989 | 3.989 | 100,0 | 100,0 | 26,2 | 73,5 | 3.989 | 3.989 | 0 |
| Kanaan | 1 | 2.0 | 1.837 | 1.837 | 100,0 | 100,0 | 31,2 | 68,8 | 1.834 | 1.834 | 3 |
| Loktuan | 4 | 2.0 | 5.010 | 5.010 | 100,0 | 100,0 | 17,5 | 81,8 | 5.009 | 4.923 | 87 |
| Satimpo | 1 | 2.0 | 2.502 | 2.502 | 100,0 | 100,0 | 12,1 | 87,9 | 2.504 | 2.504 | -2 |
| Tanjung Laut | 1 | 2.0 | 4.340 | 4.340 | 100,0 | 100,0 | 25,2 | 74,1 | 4.340 | 4.340 | 0 |
| Tanjung Laut Indah | 1 | 2.0 | 3.751 | 3.751 | 100,0 | 100,0 | 21,0 | 78,7 | 3.751 | 3.751 | 0 |
| **Total** | 31 | | **51.888** | **51.887** | 93,5 | 93,5 | 23,3 | 76,4 | **51.883** | **47.108** | **4.779** |

## c. Detail

### A. Inventaris file

**A.1–A.3 [V]** Daftar lengkap (31 `.gml`):

| Kelurahan | File | Ukuran (MB) | Diubah | CityGML | srsName (EPSG) | Dim | XML valid | Bangunan |
|---|---|---|---|---|---|---|---|---|
| Api Api | Model 3D - Kelurahan Api Api.gml | 400,0 | 2025-08-14 06:36 | 2.0 | 32650 | 3 | ya | 5.142 |
| Belimbing | Model 3D - Kelurahan Belimbing - Part I.gml | 55,4 | 2025-06-15 16:56 | 2.0 | 32650 | 3 | ya | 832 |
| Belimbing | Model 3D - Kelurahan Belimbing - Part II.gml | 21,5 | 2025-06-15 16:49 | 2.0 | 32650 | 3 | ya | 515 |
| Belimbing | Model 3D - Kelurahan Belimbing - Part III.gml | 253,3 | 2025-06-16 02:01 | 2.0 | 32650 | 3 | ya | 3.298 |
| Berebas Pantai | Model 3D - Kelurahan Berebas Pantai.gml | 160,9 | 2025-06-16 09:55 | 2.0 | 32650 | 3 | ya | 2.022 |
| Berebas Tengah | Model 3D - Kelurahan Berebas Tengah.gml | 153,8 | 2025-05-27 12:53 | 3.0 | 32650 | 3 | ya | 3.390 |
| Bontang Baru | GABUNGAN BONTANG BARU.gml | 319,8 | 2025-06-15 11:38 | 2.0 | 32650 | 3 | ya | 4.147 |
| Bontang Kuala | Model 3D - Kelurahan Bontang Kuala.gml | 143,0 | 2025-08-14 16:54 | 2.0 | 32650 | 3 | ya | 2.366 |
| Bontang Lestari | Model 3D - Kelurahan Bontang Lestari - Part I.gml | 7,2 | 2025-07-17 14:46 | 2.0 | 32650 | 3 | ya | 212 |
| Bontang Lestari | Model 3D - Kelurahan Bontang Lestari - Part II.gml | 11,2 | 2025-07-17 14:54 | 2.0 | 32650 | 3 | ya | 262 |
| Bontang Lestari | Model 3D - Kelurahan Bontang Lestari - Part III.gml | 0,7 | 2025-09-02 18:40 | 2.0 | 32650 | 3 | ya | 5 |
| Bontang Lestari | Model 3D - Kelurahan Bontang Lestari - Part IV.gml | 3,0 | 2025-08-19 23:30 | 2.0 | 32650 | 3 | ya | 162 |
| Bontang Lestari | Model 3D - Kelurahan Bontang Lestari - Part V.gml | 8,7 | 2025-08-19 19:09 | 2.0 | 32650 | 3 | ya | 342 |
| Bontang Lestari | Model 3D - Kelurahan Bontang Lestari - Part VI.gml | 14,8 | 2025-08-15 16:28 | 2.0 | 32650 | 3 | ya | 290 |
| Bontang Lestari | Model 3D - Kelurahan Bontang Lestari - Part VII.gml | 21,6 | 2025-08-14 02:10 | 2.0 | 32650 | 3 | ya | 774 |
| Bontang Lestari | Model 3D - Kelurahan Bontang Lestari - Part VIII.gml | 35,0 | 2025-08-12 16:52 | 2.0 | 32650 | 3 | ya | 172 |
| Guntung | Model 3D - Kelurahan Guntung - Part I.gml | 82,8 | 2025-06-15 09:32 | 2.0 | 32748 | 3 | ya | 1.725 |
| Guntung | Model 3D - Kelurahan Guntung - Part II.gml | 4,1 | 2025-06-15 09:33 | 2.0 | 32748 | 3 | ya | 108 |
| Guntung | Model 3D - Kelurahan Guntung - Part III.gml | 20,7 | 2025-08-14 01:29 | 2.0 | 32650 | 3 | ya | 226 |
| Gunung Elai | Model 3D - Kelurahan Gunung Elai - Part I.gml | 104,1 | 2025-06-15 18:03 | 2.0 | 32650 | 3 | ya | 1.167 |
| Gunung Elai | Model 3D - Kelurahan Gunung Elai - Part II.gml | 166,0 | 2025-06-15 18:15 | 2.0 | 32650 | 3 | ya | 2.571 |
| Gunung Elai | Model 3D - Kelurahan Gunung Elai - Part III.gml | 65,1 | 2025-06-15 18:41 | 2.0 | 32650 | 3 | ya | 731 |
| Gunung Telihan | Model 3D - Kelurahan Gunung Telihan.gml | 254,0 | 2025-06-15 11:03 | 2.0 | 32650 | 3 | ya | 3.989 |
| Kanaan | Model 3D - Kelurahan Kanaan.gml | 98,3 | 2025-06-16 09:30 | 2.0 | 32650 | 3 | ya | 1.837 |
| Loktuan | Model 3D - Kelurahan Loktuan - Part I.gml | 343,6 | 2025-08-13 12:43 | 2.0 | 32650 | 3 | ya | 4.923 |
| Loktuan | Model 3D - Kelurahan Loktuan - Part II.gml | 1,9 | 2025-08-14 00:02 | 2.0 | 32650 | 3 | ya | 55 |
| Loktuan | Model 3D - Kelurahan Loktuan - Part III.gml | 0,9 | 2025-08-14 01:09 | 2.0 | 32650 | 3 | ya | 26 |
| Loktuan | Model 3D - Kelurahan Loktuan - Part IV.gml | 0,5 | 2025-08-15 16:15 | 2.0 | 32650 | 3 | ya | 6 |
| Satimpo | Model 3D - Kelurahan Satimpo.gml | 282,6 | 2025-06-15 09:44 | 2.0 | 32748 | 3 | ya | 2.502 |
| Tanjung Laut | Model 3D - Kelurahan Tanjung Laut.gml | 327,3 | 2025-06-16 13:59 | 2.0 | 32650 | 3 | ya | 4.340 |
| Tanjung Laut Indah | Model 3D - Kelurahan Tanjung Laut Indah.gml | 221,6 | 2025-08-15 11:14 | 2.0 | 32650 | 3 | ya | 3.751 |

- **Pemetaan slug [V]:** 15 folder → 15 slug yang sama persis dengan `processed/3dtiles/` dan `config/kelurahan_map.csv`. Kelurahan tanpa CityGML: **tidak ada**. File tak terpetakan: `Kelurahan Bontang Kuala/Model 3D - Kelurahan Bontang Kuala.gfs` (skema GDAL, diubah 2026-10-15, bukan CityGML). Semua `.gml` berdiri di folder kelurahannya; tidak ada file yang tidak bisa dipetakan.
- **Ekstensi [V]:** semua `.gml`. Tanggal modifikasi file `.gml`: 2025-05-27 s.d. 2025-09-02.
- **Versi [V]:** CityGML 2.0 (namespace `http://www.opengis.net/citygml/2.0`) untuk 30 file; CityGML 3.0 (`.../citygml/3.0`, GML 3.2) hanya `Berebas Tengah`.
- **CRS [V]:** `srsDimension` 3 di semua file. `srsName` EPSG:32650 di 28 file; **EPSG:32748 (UTM 48S) di 3 file** (Model 3D - Kelurahan Guntung - Part I.gml, Model 3D - Kelurahan Guntung - Part II.gml, Model 3D - Kelurahan Satimpo.gml). Koordinat file-file itu (mis. Satimpo E 549.767–555.242, N 11.007–14.497) tidak mungkin UTM selatan (northing ±10.000.000) dan **identik dengan CityJSON yang berlabel 32650** (pencocokan posisi, bagian E.3). Jadi label 32748 diduga salah ketik **[D]**. Envelope di header cocok dengan bounding box aktual bangunan di semua file (selisih XY ≤ 1 m) [V].
- **Satuan XML:** `gml:pos` (2.0) dan `gml:posList` (3.0), koordinat X Y Z.

### B. Bangunan dan ID

- **Jumlah [V]:** 51.888 `bldg:Building`; **0 `bldg:BuildingPart`** di semua file. Setiap `cityObjectMember` berisi satu `Building` (tidak ada tipe objek lain).
- **Pola gml:id [V]:** `<KODE>_<ddmmyyyy>-AAAA-<nomor 5 digit>-<operator>-<hash 7 karakter>`, mis. `BS_02092025-AAAA-00001-GeoAI01-05629B4`; sebagian bangunan memakai operator `GEOAIBTG01`. Kode: AA (Api Api), BL, BP, BT, BB, BK, BS (Bontang Lestari), GG, GE, GT, KN, LK, ST, TL, TI. Contoh 3 per file ada di JSON (`A_file[].gml_id_contoh`). **Prefiks tidak selalu sesuai kelurahan [V]:** Bontang Lestari Part VIII dan Guntung Part III memakai prefiks `LK_` (kode Loktuan), padahal letaknya di Bontang Lestari (N 2.450–3.860 m) dan Guntung; hanya label.
- **Keunikan dalam file [V]:** **103 bangunan berbagi `gml:id` dengan bangunan lain di file yang sama**, tersebar di 17 file dan terbesar di Loktuan Part I (17), Api Api (15), Gunung Telihan (12), Bontang Baru (10). **Bukan salinan**: dari 103 kelebihan, 0 berposisi dan tinggi sama; selebihnya bangunan berbeda (posisi/tinggi beda). Contoh: `AA_13082025-AAAA-01141-GEOAIBTG01-6900268` untuk dua bangunan berbeda (tinggi 6,20 m dan 12,36 m).
- **Antarfile [V]:** hanya **2** `gml:id` yang muncul di dua file (keduanya Loktuan: Part I dengan Part II, dan Part I dengan Part III); posisinya berbeda, jadi bangunan berbeda dengan ID bentrok. Total `gml:id` unik: 51.783 dari 51.888 bangunan (105 bentrok).
- **gml:id elemen lain [V]:** pada CityGML 2.0, **setiap `gml:Polygon` dan `gml:LinearRing` muncul dua kali dengan `gml:id` yang sama** (id duplikat sebanyak jumlah pasangan permukaan; mis. Api Api 489.436). Ini melanggar keunikan `gml:id` GML, tetapi XML tetap terparse. `Surface` (Wall/Roof/Ground) berid unik. Pada CityGML 3.0 (Berebas Tengah) poligon berid UUID unik dan `LinearRing` tanpa id; tidak ada duplikat.
- **Nomor urut dan lompatan [V]:** nomor 5 digit setelah `AAAA-` tidak berurutan penuh. Contoh: Api Api memuat nomor 1–5.244 tetapi hanya 5.142 bangunan (102 lompatan; mis. 38, 87, 139 hilang); Loktuan Part I 1.059 lompatan; **Loktuan Part II dimulai dari 413, Part III dari 1.088, Part IV dari 5.966** (nomor yang hilang dari Part I). Nomor `00005` yang hilang pada sampel Bontang Lestari Part III terkonfirmasi (5 bangunan bernomor 1,2,3,4,6). Hilangnya nomor menunjukkan bangunan yang dihapus atau dipindahkan antar part **[D]**; tidak ada nomor yang melompat di Bontang Lestari Part V/VIII, Guntung Part II/III.
- **`gml:description` [V]:** format `<n>, created by <operator>`; nilai `n` **sama dengan ID numerik di CityJSON** (bagian E.3), bukan dengan nomor di `gml:id`. `gml:name` = `Building-<n>` (tidak bermakna sebagai nama). Operator pembuat: Digital_Twin_UGM (24.010), GeoAI02 (11.484), GeoAI04 (4.340), GeoAIT (4.041), (tanpa) (3.390), GeoAI01 (3.324), GeoAI03 (731), GeoAI (342), GeoAI09 (226).

### C. Atribut

Berlaku untuk 48.498 bangunan (93,47%: seluruh file CityGML 2.0). **Berebas Tengah (3.0): 0 atribut.** [V]

| Atribut | Cakupan | Nilai unik | Min | Maks | Median | 5 nilai teratas | Status |
|---|---|---|---|---|---|---|---|
| `bldg:class` | 93,47% | 1 | 1.000,00 | 1.000,00 | 1.000,00 | 1000 (48.498) | **nilai bawaan** |
| `bldg:function` | 93,47% | 1 | 1.000,00 | 1.000,00 | 1.000,00 | 1000 (48.498) | **nilai bawaan** |
| `bldg:measuredHeight` | 93,47% | 1.704 | 0,00 | 68,25 | 5,87 | 6.02 (137), 6.04 (136), 6.39 (133) | bervariasi |
| `bldg:roofType` | 93,47% | 1 | 1.030,00 | 1.030,00 | 1.030,00 | 1030 (48.498) | **nilai bawaan** |
| `bldg:storeysAboveGround` | 93,47% | 11 | 0,00 | 13,00 | 1,00 | 1 (45.842), 2 (2.327), 3 (247) | bervariasi |
| `bldg:storeysBelowGround` | 93,47% | 1 | 0,00 | 0,00 | 0,00 | 0 (48.498) | **nilai bawaan** |
| `bldg:usage` | 93,47% | 1 | 1.000,00 | 1.000,00 | 1.000,00 | 1000 (48.498) | **nilai bawaan** |
| `bldg:yearOfConstruction` | 93,47% | 1 | 2.025,00 | 2.025,00 | 2.025,00 | 2025 (48.498) | **nilai bawaan** |
| `core:creationDate` | 93,47% | 1 | - | - | - | 2025-01-01 (48.498) | **nilai bawaan** |
| `core:relativeToTerrain` | 93,47% | 1 | - | - | - | entirelyAboveTerrain (48.498) | **nilai bawaan** |
| `gen:ConstructionMethod` | 93,47% | 1 | - | - | - | New Building (48.498) | **nilai bawaan** |
| `gen:GrossPlannedArea` | 93,47% | 1 | 120,00 | 120,00 | 120,00 | 120.00 (48.498) | **nilai bawaan** |
| `gen:IsLandmarked` | 93,47% | 1 | - | - | - | NO (48.498) | **nilai bawaan** |
| `gml:description` | 93,47% | 19.847 | - | - | - | 1, created by Digital_Twin_UGM (12) … | bervariasi |
| `gml:name` | 93,47% | 5.143 | - | - | - | Building-1 (30) … | bervariasi |

- **Nilai bawaan (satu nilai untuk semua bangunan) [V]:** `bldg:class`=1000, `bldg:function`=1000, `bldg:usage`=1000, `bldg:roofType`=1030, `bldg:yearOfConstruction`=2025, `bldg:storeysBelowGround`=0, `core:creationDate`=2025-01-01, `core:relativeToTerrain`=entirelyAboveTerrain, `gen:ConstructionMethod`=New Building, `gen:GrossPlannedArea`=120.00 m², `gen:IsLandmarked`=NO. Kode `class/function/usage/roofType` memakai codelist SIG3D (`codeSpace` ke `sig3d.org`) dan nilainya hanya satu kode, sehingga **tidak ada informasi fungsi bangunan**. `GrossPlannedArea` 120 m² konstan padahal luas footprint median ±120 m² hanya kebetulan (min 0 m²–maks 17.849 m²) **[D: nilai pengisi]**.
- **Informatif [V]:** `measuredHeight` (m; median 5,87; maks 68,25; 1.704 nilai) dan `storeysAboveGround` (1: 45.842; 2: 2.327; 3: 247; …; maks 13). Keduanya tercakup 100% di 14 kelurahan CityGML 2.0.
- **measuredHeight vs geometri [V]:** untuk 48.498 bangunan, selisih (atribut − (Zmaks−Zmin)) bermedian 0,0000 m, |selisih| median 0,0025 m, **0 bangunan** berselisih > 0,5 m (maksimum 0,005 m). Artinya `measuredHeight` = tinggi geometri yang dibulatkan, bukan pengukuran independen; untuk Berebas Tengah tinggi dapat diturunkan dari geometri dengan hasil setara.
- **Nilai janggal [V]:** 22 bangunan ber-`measuredHeight` 0; 57 bangunan setinggi < 0,1 m; 9 bangunan > 40 m (maks 68,2 m di Guntung Part III).

Cakupan tinggi dan lantai per kelurahan: 100% di 14 kelurahan CityGML 2.0 dan 0% di Berebas Tengah (lihat tabel b).

### D. Geometri

1. **LOD [V]:** seluruhnya LOD2. CityGML 2.0: hanya `lod2MultiSurface` (surfaceMember polygon per `WallSurface`/`RoofSurface`/`GroundSurface`). CityGML 3.0: `lod2MultiSurface` + `lod2Solid` (solid mereferensikan poligon yang sama lewat `xlink`). Tidak ada `lod1Solid`, `lod2Solid` pada 2.0, ataupun `lod3`.
2. **Rentang Z [V]:** 26 file bertumpu di Z ≈ 0,001 m (bangunan CityGML 2.0 berbasis 0,001; Berebas Tengah 3.0 berbasis 0,000). **5 file berelevasi dasar bervariasi:**

| File | Z dasar bangunan: p5 / median / p95 (m) | Bangunan Zmin < −0,05 | Bangunan Zmin ≈ 0 |
|---|---|---|---|
| Model 3D - Kelurahan Satimpo.gml | -23,4 / -15,4 / 3,2 | 2.094 dari 2.502 | 49 |
| Model 3D - Kelurahan Belimbing - Part III.gml | -18,9 / 5,4 / 32,6 | 917 dari 3.298 | 144 |
| Model 3D - Kelurahan Berebas Pantai.gml | -12,4 / -4,2 / 0,0 | 1.899 dari 2.022 | 123 |
| Model 3D - Kelurahan Kanaan.gml | -6,8 / 4,6 / 10,8 | 541 dari 1.837 | 73 |
| Model 3D - Kelurahan Guntung - Part I.gml | -7,2 / -2,1 / 9,9 | 1.208 dari 1.725 | 248 |

   CityJSON untuk bangunan yang sama **selalu berbasis 0** (selisih tinggi median 0 m, selisih maks ≤ 6,8 m), jadi CityJSON lama dinormalkan per bangunan. Z negatif sampai −23,6 m tidak mungkin ketinggian tanah Kota Bontang; asalnya (datum vertikal, offset, atau hasil sampling terrain) **tidak diketahui [D]**.
3. **Label permukaan [V]:** pada file berbasis 0,001, **35.735 bangunan (68,9%; 148.634 poligon)** punya `RoofSurface` yang seluruh titiknya di Zmin (salinan terbalik lantai), dan **9.132 bangunan (17,6%; 12.045 poligon)** punya `GroundSurface` di Zmaks (salinan terbalik atap). Pada 5 file berelevasi absolut dan Berebas Tengah (3.0) hampir tidak ada (0–5 bangunan). Label surface tidak dapat dipercaya untuk membedakan atap dari lantai.
4. **Permukaan ganda [V]:** **99,86%** dari 4.462.734 poligon punya pasangan dengan titik sama berurutan terbalik di bangunan yang sama (3.0 juga). Sebagian poligon juga duplikat searah (0–14% per file; tertinggi Berebas Pantai 14,4% dan Satimpo 10,1%). Membuang salinan terbalik berarti ±halving jumlah segitiga.
5. **Bentuk atap [V]:** ambang miring: normal menyimpang > 5° dari vertikal pada > 10% luas atap; datar: ketinggian atap dikelompokkan dengan toleransi 5 cm. Salinan atap berlabel di dasar dikecualikan.

| Kelurahan | Bangunan | Datar 1 tingkat % | Datar bertingkat % | Miring % | Tanpa atap % |
|---|---|---|---|---|---|
| Api Api | 5.142 | 7,9 | 12,8 | 79,0 | 0,3 |
| Belimbing | 4.645 | 10,7 | 7,8 | 81,5 | 0,0 |
| Berebas Pantai | 2.022 | 11,5 | 11,4 | 77,1 | 0,0 |
| Berebas Tengah | 3.390 | 13,8 | 11,3 | 74,8 | 0,0 |
| Bontang Baru | 4.147 | 14,7 | 13,3 | 71,2 | 0,8 |
| Bontang Kuala | 2.366 | 8,2 | 10,9 | 80,7 | 0,2 |
| Bontang Lestari | 2.219 | 55,8 | 6,3 | 36,5 | 1,4 |
| Guntung | 2.059 | 10,7 | 4,8 | 84,2 | 0,2 |
| Gunung Elai | 4.469 | 10,1 | 8,4 | 81,2 | 0,2 |
| Gunung Telihan | 3.989 | 18,6 | 7,6 | 73,5 | 0,3 |
| Kanaan | 1.837 | 19,8 | 11,4 | 68,8 | 0,1 |
| Loktuan | 5.010 | 10,4 | 7,1 | 81,8 | 0,7 |
| Satimpo | 2.502 | 6,2 | 5,9 | 87,9 | 0,0 |
| Tanjung Laut | 4.340 | 13,1 | 12,1 | 74,1 | 0,8 |
| Tanjung Laut Indah | 3.751 | 11,1 | 9,9 | 78,7 | 0,3 |
| **Total** | 51.888 | 13,7 | 9,6 | 76,4 | 0,4 |

   Bontang Lestari adalah satu-satunya kelurahan yang didominasi atap datar (55,8% datar satu tingkat). Bangunan dengan *sebagian* atap miring (apa pun luasnya): 76,6%.

6. **Footprint [V]:** poligon dasar = poligon yang seluruh titiknya ≤ Zmin + 2 cm, digabung (`unary_union`). Dapat dibentuk menjadi poligon valid untuk **51.814 dari 51.888 bangunan (99,86%)**; 73 bangunan tanpa poligon dasar; 283 bangunan (0,5%) punya komponen tidak valid yang harus diperbaiki (`make_valid`). Footprint < 2 m²: **205** bangunan.

| Kelurahan | Valid % | Luas min / median / maks (m²) | < 2 m² | Tanpa |
|---|---|---|---|---|
| Api Api | 99,8 | 1,56 / 134,4 / 2.705 | 2 | 8 |
| Belimbing | 99,8 | 0,01 / 171,2 / 9.044 | 7 | 7 |
| Berebas Pantai | 99,8 | 0,01 / 105,8 / 2.357 | 8 | 5 |
| Berebas Tengah | 99,6 | 0,00 / 109,9 / 1.922 | 28 | 12 |
| Bontang Baru | 100,0 | 0,00 / 123,1 / 3.305 | 50 | 2 |
| Bontang Kuala | 99,9 | 3,19 / 123,7 / 2.356 | 0 | 2 |
| Bontang Lestari | 100,0 | 0,16 / 78,6 / 12.398 | 28 | 0 |
| Guntung | 100,0 | 2,50 / 120,1 / 17.849 | 0 | 0 |
| Gunung Elai | 99,9 | 0,67 / 149,6 / 1.896 | 3 | 4 |
| Gunung Telihan | 99,9 | 0,00 / 127,8 / 2.825 | 18 | 5 |
| Kanaan | 100,0 | 0,02 / 114,1 / 1.548 | 18 | 0 |
| Loktuan | 99,7 | 0,68 / 132,0 / 4.214 | 5 | 13 |
| Satimpo | 99,8 | 3,04 / 199,3 / 18.119 | 0 | 5 |
| Tanjung Laut | 99,8 | 0,00 / 125,7 / 5.684 | 31 | 8 |
| Tanjung Laut Indah | 99,9 | 0,00 / 136,2 / 6.175 | 7 | 2 |

### E. Tumpang tindih dan kelengkapan

**E.1 Antarpart [V]** (kelurahan multi-part: Belimbing, Bontang Lestari, Guntung, Gunung Elai, Loktuan):

| Kelurahan | Part A | Part B | Cocok posisi | Geometri sama | Geometri beda | `gml:id` sama |
|---|---|---|---|---|---|---|
| Gunung Elai | Part II | Part III | 1 | 0 | 1 | 0 |
| Loktuan | Part I | Part II | 0 | 0 | 0 | 1 |
| Loktuan | Part I | Part III | 0 | 0 | 0 | 1 |

- Hampir **tidak ada tumpang tindih**: part-part adalah himpunan bangunan **berbeda**. Pengecualian: Gunung Elai Part II/III berbagi 1 bangunan yang geometrinya berbeda; Loktuan Part I berbagi 1 `gml:id` dengan Part II dan 1 dengan Part III (posisi berbeda → ID bentrok, bukan revisi).
- **Loktuan Part II–IV [V]:** 55 + 26 + 6 = 87 bangunan **tambahan** (tanpa padanan posisi di Part I). Nomor ID dimulai dari 413, 1.088, dan 5.966 (isi nomor yang hilang di Part I). Tidak ada indikasi revisi geometri.
- Belimbing, Bontang Lestari, dan Guntung: nol tumpang tindih. Konsekuensi: **gabungan harus berupa penyatuan semua part**, bukan menimpa berdasarkan ID.

**E.2 Total unik [V]:** 51.887 bangunan unik (posisi) di seluruh kota (51.888 dalam file; 1 duplikat posisi di Gunung Elai). Pembanding: audit CityJSON 51.883 unik (selisih 4) dan tile saat ini 47.108 (selisih 4.779, tersebar di Belimbing, Bontang Lestari, Gunung Elai, dan Loktuan).

**E.3 CityGML vs CityJSON `raw/3d/` [V]** (pusat bounding box, toleransi 2 m; CityJSON dedupe antar-file):

| Kelurahan | CityGML | CityJSON | Cocok | Hanya CityGML | Hanya CityJSON | ID CityJSON | `gml:id` sama |
|---|---|---|---|---|---|---|---|
| Api Api | 5.142 | 5.142 | 5.142 | 0 | 0 | nomor urut | 0 dari 5.142 |
| Belimbing | 4.645 | 4.643 | 4.615 | 30 | 29 | nomor urut | 0 dari 4.615 |
| Berebas Pantai | 2.022 | 2.024 | 2.009 | 13 | 15 | asli | 1.991 dari 2.009 |
| Berebas Tengah | 3.390 | 3.390 | 3.390 | 0 | 0 | asli | 3.390 dari 3.390 |
| Bontang Baru | 4.147 | 4.147 | 4.147 | 0 | 0 | nomor urut | 0 dari 4.147 |
| Bontang Kuala | 2.366 | 2.366 | 2.366 | 0 | 0 | nomor urut | 0 dari 2.366 |
| Bontang Lestari | 2.219 | 2.219 | 2.219 | 0 | 0 | nomor urut | 0 dari 2.219 |
| Guntung | 2.059 | 2.057 | 2.047 | 12 | 10 | campuran | 1.818 dari 2.047 |
| Gunung Elai | 4.469 | 4.468 | 4.469 | 0 | 0 | nomor urut | 0 dari 4.469 |
| Gunung Telihan | 3.989 | 3.989 | 3.989 | 0 | 0 | nomor urut | 0 dari 3.989 |
| Kanaan | 1.837 | 1.834 | 1.829 | 8 | 5 | asli | 0 dari 1.829 |
| Loktuan | 5.010 | 5.009 | 5.010 | 0 | 1 | nomor urut | 0 dari 5.010 |
| Satimpo | 2.502 | 2.504 | 2.439 | 63 | 66 | asli | 0 dari 2.439 |
| Tanjung Laut Indah | 3.751 | 3.751 | 3.749 | 2 | 2 | asli | 0 dari 3.749 |
| Tanjung Laut | 4.340 | 4.340 | 4.340 | 0 | 0 | nomor urut | 0 dari 4.340 |

- Total: 51.760 cocok; hanya CityGML 128; hanya CityJSON 128. Selisih kecil ada di Satimpo (63/66), Belimbing (30/29), Berebas Pantai (13/15), Guntung (12/10), Kanaan (8/5). Dugaan: bangunan yang bergeser > 2 m atau dibentuk ulang antar versi **[D]**.
- **ID asli [V]:** untuk Berebas Pantai (1.991 dari 2.009 pasangan), Berebas Tengah (3.390 dari 3.390), dan Guntung (1.818 dari 2.047; sisanya bernomor) **ID CityJSON = `gml:id` CityGML**. Untuk **Satimpo, Kanaan, dan Tanjung Laut Indah ID CityJSON tidak sama dengan `gml:id` saat ini**: nomor 5 digit sama tetapi tanggal, operator, dan hash berbeda (mis. `ST_04062025-AAAA-00001-GeoAI01-3F49B92` di CityJSON vs `ST_14062025-AAAA-00001-GeoAI02-8B27824` di CityGML). CityJSON-nya berasal dari versi ekspor lebih lama.
- **ID numerik [V]:** 9 kelurahan CityJSON memakai ID numerik; ID itu **sama dengan nomor di `gml:description`** untuk hampir semua pasangan (Api Api 5.142/5.142, Bontang Baru 4.147/4.147, Tanjung Laut 4.340/4.340, Loktuan 5.008/5.010, Gunung Elai 4.468/4.469). Karena nomor `description` dimulai dari 1 di tiap part, ID numerik bentrok antar part; ini **diduga [D]** penyebab bangunan hilang saat CityJSON digabung berdasarkan ID. Nomor di `gml:id` dan urutan dalam file **tidak** sama dengan ID numerik itu.
- **Z [V]:** pada pasangan 5 file berelevasi absolut, tinggi bangunan sama (selisih median 0 m) tetapi Zmin CityGML berbeda dari CityJSON (mis. Satimpo −15,4 m vs 0,001 m).

**E.4 Letak terhadap batas kelurahan [V]** (pusat bangunan dikonversi EPSG:32650→4326, diuji terhadap `processed/geojson/batas-kelurahan.norm.geojson`, hanya dibaca): **51.662 dari 51.888 bangunan (99,56%) berada di dalam kelurahan folder asalnya.** Terendah: Loktuan Part II 85,5% (8 bangunan di luar semua poligon kelurahan), Guntung Part II 94,4% (6 di luar poligon), Guntung Part III 93,4% (15 di dalam Satimpo). Pengelompokan per folder dapat dipercaya; selisih kecil kemungkinan bangunan di tepi laut atau batas (belum diperiksa satu per satu [D]).

### F. Kontrak frontend (hanya membaca kode)

**F.1 Pemuatan tile [V].** `use3DTiles.js:14` `MASTER_TILESET_URL = '/tiles/master-tileset.json'`; dimuat satu kali dengan `Cesium3DTileset.fromUrl` (`use3DTiles.js:382-385`, opsi `TILESET_OPTIONS` baris 30). Master berisi 15 anak (external tileset). `fetchKelurahanIndex` (`use3DTiles.js:178-189`) menurunkan **slug = segmen pertama `child.content.uri`** (mis. `api_api/tileset.json` → `api_api`), mengharuskan `child.boundingVolume.region` (6 angka; tipe lain diabaikan), dan membaca `child.geometricError` (0 berarti root sudah berkonten; > 0 berarti root kosong sehingga kotak ikhtisar ditampilkan). Nama tampil = `slugToName(slug)` (`utils/tileMeta.js:10-17`: pisah `_`, kapitalisasi tiap kata; `tanjung_laut_indah` → `Tanjung Laut Indah`). Picking memakai `parseContentUrl` (`tileMeta.js:27-40`): konten harus berada di `/tiles/<slug>/<path>.glb`; slug diambil dari segmen setelah `/tiles/`. Master dibangun oleh `04_build_master.py`, yang mensyaratkan `processed/3dtiles/<slug>/tileset.json` ber-`boundingVolume.region` dan file konten `.glb` yang ada.

**F.2 Properti fitur [V].**
- ID bangunan: `ID_KEYS = ['id','gml_id','gmlId','identifier','objectid']` (`use3DTiles.js:53`, dipakai `pickFirst(metadata, ID_KEYS)` baris 472). Tanpa itu ID jatuh ke `<slug>/<tile>#<featureId>`.
- Pembacaan properti: `readFeatureProperties` (`use3DTiles.js:137-146`) memanggil `feature.getPropertyIds()` dan `feature.getProperty(name)` untuk **semua** properti, lalu mengirimnya sebagai `attributes` ke `objectStore.selectObject` (baris 472-484). `objectStore.js:37-39`: bila atribut tidak kosong, langsung dipakai (status `ready`).
- Nama tampil: `ATTRIBUTE_KEYS.name = ['name','nama']` (`services/buildingAttributes.js:14-18`), dipakai di `ObjectInfoPanel.vue:126-129` lewat `pickFirst` (tidak peka huruf besar/kecil; nilai kosong dilewati). Tanpa itu judul = `Bangunan #<featureId>`.
- Kunci lain di `ATTRIBUTE_KEYS`: `height = ['measuredHeight','height','tinggi']` dan `function = ['function','fungsi','usage','penggunaan']`; **keduanya tidak dipakai di UI saat ini** (hanya `name` yang dipakai di `ObjectInfoPanel.vue:127`). Nama properti yang dicari persis seperti di atas.
- Baris atribut: `attributeRows` (`ObjectInfoPanel.vue:131-136`) menampilkan setiap pasangan kunci–nilai; angka diformat `formatNumber(value, {maxDigits: 3})` (koma desimal), selain itu `String(value)`.

**F.3 Properti tak dikenal [V kode, D perilaku di browser].** Properti dengan nama lain (mis. `GrossPlannedArea`, `storeysAboveGround`) **tetap ditampilkan** sebagai baris dengan nama kunci apa adanya (tidak ada daftar putih, tidak diterjemahkan). Tidak ada error. Nilai objek/array tampil `[object Object]`; `null` tampil `null`. Tidak diuji di browser karena tile saat ini tidak punya `EXT_structural_metadata`. Syaratnya: picking harus mengembalikan `Cesium3DTileFeature` (properti terbaca); tanpa tabel properti, hasil pick berupa objek biasa dan jalur lama (tanpa atribut) berlaku (`use3DTiles.js` `resolvePick`, AGENTS.md §4).

**F.4 Asumsi lain yang mengikat data [V].**
- Opsi tileset (`use3DTiles.js:30-42`): `skipLevelOfDetail: true`, `cacheBytes` 512 MB, overflow 256 MB, `dynamicScreenSpaceError`/`foveatedScreenSpaceError` aktif, `maximumScreenSpaceError` mengikuti Mode tampilan (16/24/32). Ambang tampil kotak ikhtisar dihitung dari `geometricError` root kelurahan dan SSE (`buildingsVisibleWithin`).
- `geometricError` root master sengaja besar (986,1 = 4× kelurahan terbesar; AGENTS.md §5) karena root master tanpa konten; jangan diperkecil.
- Penempatan: tiap `tileset.json` kelurahan memuat `transform` ECEF di root (mis. api_api: translasi ≈ (−2.944.133, 5.657.973, 14.442) m); glTF berkoordinat lokal dari UTM. **Tidak ada terrain** (globe ellipsoid), sehingga bangunan duduk di ketinggian elipsoid 0 jika Z dasar = 0. Z dasar ≠ 0 (seperti 5 file CityGML ini) membuat bangunan melayang atau tenggelam di globe. `depthTestAgainstTerrain` aktif.
- Format tile saat ini: 3D Tiles 1.1 dengan `3DTILES_content_gltf`, glTF 2.0 ber-`KHR_mesh_quantization` + `EXT_meshopt_compression` (diwajibkan) + `EXT_mesh_features` (`_FEATURE_ID_0`, `featureCount`), `generator: cityjson-convert`, material `doubleSided` berwarna `#D8C3A5`; **warna legenda frontend `MAP_COLORS.building` = `#D9DEE2`** (komentar `mapColors.js`: 'perkiraan, belum diverifikasi'), sehingga legenda sudah tidak sesuai warna model. Peringatan ukuran konten > 3 MB di `04_build_master.py` (`LARGE_TILE_BYTES`).
- Kotak ikhtisar: dibangun dari `region` dan `geometricError` child master; hanya untuk kelurahan ber-root kosong. Navigasi `flyToKelurahan(slug)` memakai `region` yang sama.
- Tile saat ini **tanpa metadata**; `tileset.json` tidak mencatat versi generator (`asset` hanya `version: 1.1`), jadi versi tyler yang dipakai tidak dapat ditelusuri **[V]**.

### G. Tooling [V]

| Alat | Ketersediaan |
|---|---|
| python3 | 3.14.4 (/usr/bin/python3) |
| venv `data-pipeline/.venv` | python 3.14.4, shapely 2.2.0, pyproj 3.8.0, pyogrio 0.13.0, geopandas 1.2.0, numpy 2.5.4, pandas 3.1.0, lxml TIDAK ADA, fiona TIDAK ADA, cjio TIDAK ADA di venv |
| java | openjdk 25.0.2 (/opt/android-studio/jbr/bin/java; JBR Android Studio, bukan JDK sistem) |
| citygml-tools | TIDAK ADA |
| cjio | v0.10.1 (/home/itstaufikhdyt/.local/bin/cjio; hanya membaca CityJSON) |
| tyler_biner | TIDAK ADA di PATH; cargo/rustc juga tidak ada |
| tyler_docker | image 3dgi/tyler:latest (349 MB, dibuat 2026-07-27), tyler 1.0.0-alpha1 |
| gdal | GDAL 3.12.2 (ogr2ogr, ogrinfo); driver GML dan GMLAS, tanpa driver CityGML khusus |
| docker | 29.6.0; image lokal terkait: 3dgi/tyler, geonode/postgis:15-3.5-latest, geonode/geoserver 2.27.4 dan 2.28.x |
| psql | PostgreSQL client 18.6 (tanpa server yang berjalan; container berjalan hanya portainer) |

**Opsi tyler (`tyler 1.0.0-alpha1`, via Docker) terkait atribut/metadata:** `--object-attributes <nama:tipe,...>` (tipe `bool|int|float|string`; atribut CityObject dimasukkan sebagai fitur pada output 3D Tiles), `--3dtiles-metadata-class <kelas>` (default `citymodel`; kelas `EXT_structural_metadata` untuk property table), `--object-type Building`, `--include-parent-attributes`, `--lod-building <LoD>`, `--color-building <#RRGGBB>`, `--grid-cellsize` (default 250), `--qtree-capacity` (default 42000), `--3dtiles-geometric-error-factor` (default 0,024), `--3dtiles-content-add-bv`, `--grid-minz/--grid-maxz`. Input tyler **harus CityJSON/CityJSONSeq (cjindex)**, bukan CityGML, jadi konversi CityGML → CityJSON diperlukan lebih dulu: `cjio` (terpasang) hanya membaca CityJSON, `citygml-tools` tidak ada, dan GDAL tidak memiliki driver CityGML. Pilihan: konverter sendiri (stdlib/venv) atau mengunduh `citygml-tools` (butuh jaringan; belum dicoba). `psql` klien ada; ada image `geonode/postgis:15-3.5` untuk penyimpanan spasial.

## d. Syarat kontrak frontend (F.5)

Agar frontend dan backend **tidak perlu diubah**, pipeline baru harus memenuhi:

1. **Lokasi dan nama:** keluaran tile di `processed/3dtiles/<slug>/` (disarankan dibangun di folder baru lalu disinkronkan), dengan 15 slug huruf kecil bergaris bawah yang sama dengan `config/kelurahan_map.csv` (`api_api`, `belimbing`, …, `tanjung_laut_indah`).
2. **Struktur tileset:** 3D Tiles 1.1 dengan `3DTILES_content_gltf`; tiap `<slug>/tileset.json` punya `root.boundingVolume.region` (bukan box/sphere), `refine: REPLACE`, `transform` ECEF, dan konten `.glb` bernama jalur `<slug>/<…>.glb` (parser menghapus ekstensi). Master tetap dibangun lewat `04_build_master.py` (konvensi: `child.content.uri = '<slug>/tileset.json'`, `child.geometricError` = galat root kelurahan, 0 bila root berkonten).
3. **`geometricError`:** root master besar (≥ 4× terbesar) dan root kelurahan konsisten dengan aturan kotak ikhtisar; **root tanpa konten** memunculkan kotak ikhtisar. Bila pipeline baru menyertakan konten root kasar, `geometricError` anak master harus 0 dan perilaku jarak-jauh diuji.
4. **Z dasar = 0:** bangunan harus berbasis Z ≈ 0 (relatif tanah), karena globe tanpa terrain. Z absolut atau negatif dari 5 file CityGML harus dinormalkan per bangunan (seperti CityJSON lama) kecuali terrain ditambahkan.
5. **Metadata:** `EXT_structural_metadata` dengan property table yang dihubungkan ke `EXT_mesh_features`, sehingga picking mengembalikan `Cesium3DTileFeature` dan `getPropertyIds()` bekerja. Tanpa metadata frontend tetap jalan tetapi tanpa atribut.
6. **Nama properti:** ID bangunan harus berada di salah satu `id`, `gml_id`, `gmlId`, `identifier`, `objectid` (disarankan `gml_id`); nama tampil di `name`/`nama` (bila tidak ada, judul = `Bangunan #<featureId>`; jangan memakai `Building-<n>` bila tidak ingin judul generik); tinggi `measuredHeight` (nama sudah dikenal `ATTRIBUTE_KEYS.height`); fungsi di `function`/`usage`. Semua properti lain **ikut tampil di panel** apa adanya, jadi hanya sertakan yang layak dibaca pengguna dan hindari nilai bawaan.
7. **Tipe nilai:** skalar saja (string, angka, boolean). Angka tampil dengan koma desimal; objek/array akan tampil `[object Object]`.
8. **ID stabil dan unik:** `gml_id` unik di seluruh kota (51.888 bangunan; ±103 bentrok dan 2 antarfile harus diselesaikan) dan stabil antar-ETL; ini juga kunci lookup backend `buildingAttributes.js` (`/buildings/{id}/attributes`, belum ada).
9. **Ukuran:** konten `.glb` ≤ ±3 MB per tile (peringatan `04_build_master.py`), total memori mengikuti `cacheBytes` 512 MB; geometri dengan meshopt + kuantisasi seperti sekarang (tidak diwajibkan frontend, tetapi sudah didukung Cesium 1.146 dan menjaga ukuran kecil).
10. **Warna:** warna material model tetap menjadi sumber tampilan; legenda (`#D9DEE2`) tidak sesuai dengan `#D8C3A5` saat ini. Pilih satu; bila ingin legenda sesuai tanpa mengubah frontend, gunakan `--color-building #D9DEE2` pada tyler.
11. **Tidak mengubah:** jangan menaruh keluaran baru di atas `processed/3dtiles/` yang ada dan jangan menjalankan ulang `04_build_master.py` pada folder lama (aturan proyek); keluarkan ke folder baru, validasi, lalu pindahkan setelah persetujuan.

## e. Rekomendasi awal ADR-002 (ekstrusi LOD1 vs bersihkan geometri asli)

**Rekomendasi: bersihkan geometri LOD2 asli dan jangan ekstrusi LOD1.** Alasan berbasis data:

1. **76,4% bangunan beratap miring** (hanya 13,7% datar satu tingkat). Ekstrusi LOD1 (footprint × tinggi) meratakan atap untuk tiga dari empat bangunan dan menghilangkan nilai LOD2 yang sudah dibayar (data dari survei GeoAI).
2. **Kebersihan yang dibutuhkan mudah dan terukur:** 99,86% poligon berpasangan terbalik (cukup dibuang salinannya; ±separuh segitiga), label atap/lantai pada salinan itu tertukar (hilang bersama salinannya), dan footprint valid untuk 99,86%.
3. **LOD1 tetap bisa diturunkan sebagai produk sampingan** untuk analisis (footprint valid + tinggi), terutama simulasi banjir yang hanya butuh footprint dan tinggi: `measuredHeight` identik dengan tinggi geometri, jadi tidak ada kehilangan informasi tinggi. LOD1 tidak perlu menggantikan model tampilan.
4. **Ukuran tile bukan alasan memilih LOD1:** tile LOD2 saat ini 1,0 MB rata-rata (maks 2,4 MB), memakai meshopt dan tanpa tekstur; setelah menghapus salinan terbalik beban GPU turun (tile saat ini memuat ±9,3 juta segitiga secara total).
5. **Risiko pembersihan:** 73 bangunan tanpa poligon dasar, 205 footprint < 2 m², 283 bangunan ber-komponen footprint tidak valid, dan geometri 22 bangunan setinggi 0 m perlu aturan khusus (sembunyikan, tandai, atau ekstrusi minimal). Bentuk atap 5 file berelevasi absolut perlu dihitung ulang setelah normalisasi Z.

Catatan: keputusan LOD1 vs LOD2 juga bergantung pada tujuan (tampilan vs analisis) dan Z/terrain (pertanyaan di bagian f).

## f. Pertanyaan sebelum pipeline dirancang

1. **Referensi Z:** apakah 5 file ber-Z absolut (Satimpo, Belimbing Part III, Berebas Pantai, Kanaan, Guntung Part I) mewakili tinggi tanah dari DTM (datum apa?) atau artefak? Kita normalkan semua bangunan ke dasar 0 (seperti CityJSON lama), atau menunggu terrain? Z negatif −23 m terlihat salah.
2. **ID unik:** `gml:id` bentrok untuk ±103 bangunan berbeda (di 17 file) dan 2 antarfile. Strategi apa untuk ID di tile: `gml_id` + sufiks, `<slug>/<nomor>`, atau ID baru? Apakah ID lama di CityJSON (BP_/BT_/GG_/KN_/ST_/TI_) perlu dipertahankan (untuk Satimpo/Kanaan/TLI ID-nya sudah tidak sama dengan CityGML terbaru)?
3. **Sumber yang berlaku:** untuk Satimpo, Kanaan, dan Tanjung Laut Indah, CityGML (operator GeoAI02/GeoAIT, lebih baru) dan CityJSON (GeoAI01) berbeda ID dan 63–66 bangunan berbeda posisi. Gunakan CityGML sebagai sumber tunggal?
4. **Berebas Tengah (CityGML 3.0):** tanpa atribut. Turunkan tinggi (dan lantai?) dari geometri, atau ada file 2.0 lain? Apakah 3.0 untuk kelurahan lain akan datang?
5. **Atribut yang dibawa ke tile:** hanya `measuredHeight` dan `storeysAboveGround` (+ ID, nama)? Nilai bawaan (class, function, usage, roofType, yearOfConstruction, GrossPlannedArea 120 m², dst.) dibuang? Nama tampil apa (`Building-<n>` tidak informatif)?
6. **Loktuan Part II–IV:** 87 bangunan tambahan tanpa tumpang tindih; disertakan?
7. **ADR-002:** setuju membersihkan LOD2 (bukan ekstrusi LOD1), dan LOD1 hanya untuk analisis? Apakah salinan terbalik boleh dibuang (menjadikan model satu sisi dengan `doubleSided`)?
8. **Label EPSG:32748** pada 3 file: konfirmasi bahwa koordinatnya EPSG:32650 (sudah cocok dengan CityJSON 32650).
9. **Alat konversi CityGML → CityJSON:** buat konverter sendiri (tanpa unduhan, memakai parser streaming seperti analisis ini) atau unduh `citygml-tools` (butuh jaringan)? Tyler tersedia lewat Docker (`3dgi/tyler`, 1.0.0-alpha1).
10. **Warna dan legenda:** pertahankan `#D8C3A5` atau set `#D9DEE2` agar cocok dengan legenda?
11. **Penyimpanan atribut:** hanya di tile (`EXT_structural_metadata`) atau juga di PostGIS (image `geonode/postgis` tersedia) untuk simulasi banjir?
12. **Bangunan ekstrem:** 22 bangunan tinggi 0, 57 setinggi < 0,1 m, 9 > 40 m (maks 68,2 m di Guntung Part III), 205 footprint < 2 m²: dibuang, ditandai, atau dibiarkan?

## g. Hal yang belum bisa diperiksa

- **Asal Z absolut** pada 5 file (datum vertikal, sampling terrain, atau kesalahan): tidak ada DTM di proyek dan tidak ada metadata datum di file. Hanya perilaku yang terukur yang dilaporkan.
- **Perilaku properti tak dikenal di browser:** hanya dibaca dari kode; tile saat ini tidak punya `EXT_structural_metadata`, jadi jalur `Cesium3DTileFeature` dengan metadata belum pernah dijalankan.
- **Pencocokan posisi bersifat perkiraan:** pusat bounding box dengan toleransi 2 m; selisih kecil antar-sumber (256 bangunan 'hanya di satu sumber', terutama di 5 kelurahan) tidak bisa dibedakan antara bergeser, direvisi, atau dibentuk ulang.
- **Penyebab lompatan nomor `gml:id`** (bangunan dihapus atau dipindah antar part) hanya diduga dari pola.
- **Validasi skema CityGML** (XSD): tidak dijalankan (tanpa `lxml`/`xmllint` terkonfigurasi); yang dicek adalah kebaikan-bentuk XML dan struktur. `gml:id` poligon duplikat adalah pelanggaran skema yang diamati, bukan hasil validator.
- **Appearance/tekstur dan interior:** tidak dihitung secara khusus. Yang terverifikasi: semua `cityObjectMember` bertipe `Building`, dan satu-satunya elemen anak `Building` di luar atribut/geometri adalah `boundary` (CityGML 3.0, 10.156); tidak ada `BuildingPart`, alamat, instalasi, atau interior sebagai elemen anak langsung.
- **Versi tyler yang dipakai untuk tile saat ini** tidak tercatat; tyler dijalankan dari image lokal `1.0.0-alpha1` untuk `--help` saja (tidak untuk konversi).
- **Konversi nyata CityGML → CityJSON → 3D Tiles** tidak dicoba (di luar ruang lingkup read-only).
- **Satu proses ekstraksi** menggunakan parameter tetap (ambang atap miring 5° dan 10% luas; toleransi 5 cm untuk tingkat atap; 2 cm untuk dasar bangunan); persentase atap bergantung pada ambang itu.
