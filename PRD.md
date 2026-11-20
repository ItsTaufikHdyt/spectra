# MASTER HANDOFF & PRD: DIGITAL TWIN KOTA BONTANG (3D WEB GIS)

> **Nama Proyek / Repositori:** `spectra` (Digital Twin Kota Bontang)
> **Versi Dokumen:** 1.3
> **Terakhir Diperbarui:** 2026-11-19
> **Status Global:** Scale-Up Skala Kota (15 Kelurahan); arsitektur data bangunan baru (CityGML → PostGIS → 3D Tiles) diputuskan, implementasi direncanakan

---

## 1. Ringkasan Eksekutif & Gambaran Umum
Proyek ini bertujuan membangun **Digital Twin Kota Bontang** berbasis Web 3D GIS menggunakan **CesiumJS**. Sistem ini bukan sekadar penampil 3D (viewer), melainkan platform integrasi geospasial kota untuk simulasi banjir/rob, pemantauan infrastruktur, integrasi data sensor/IoT, dan Decision Support System (DSS) Pemkot Bontang.

Tahap Proof of Concept (POC) di kawasan **Kantor Walikota Bontang** telah sukses memvalidasi integrasi:
- DTM resolusi 1m (GeoTIFF UTM EPSG:32650 -> Quantized-mesh Cesium Terrain).
- Orthophoto resolusi 5cm (XYZ imagery tiles PNG, EPSG:32650).
- Ekstrusi bangunan 3D dari GeoJSON (8 bangunan) dengan sampling elevasi terrain bertingkat.

Tahap selanjutnya adalah **Scale-Up Skala Kota (15 Kelurahan)** dengan data bangunan **LOD2** berformat **CityGML** (31 berkas, 3,5 GB, 51.888 bangunan) sebagai sumber tunggal (ADR-004). CityJSON lama (~281 MB) sudah diarsipkan di luar repo (STATUS.md).

---

## 2. Status Proyek Saat Ini (Snapshot Implementasi)

Ringkasan kondisi repositori per **2026-11-19**. Rincian status dan hutang teknis ada di `STATUS.md` (sumber kebenaran);
temuan audit di `docs/audit/AUDIT-2026-11-19.md`; inventaris data CityGML di `data-pipeline/reports/citygml_inventory.md`;
keputusan arsitektur di `docs/adr/` (ADR-001 s.d. ADR-006). Hal yang belum diimplementasikan ditandai **direncanakan**.

### 2.1. Status per Modul

| Modul | Status | Keterangan |
|-------|--------|------------|
| `frontend/` | 🟡 **Berjalan** | Vue 3 + Vite 5 + Cesium **1.146.0** (di-pin) + Pinia + Tailwind. UI tiga area, master tileset 15 kelurahan, picking `LEFT_CLICK`, layer batas kelurahan/RT/sungai, panel Data geoportal, `requestRenderMode` dengan Mode tampilan (Hemat/Seimbang/Kualitas), registri simulasi (kosong). 17 tes (`npm test`). Terrain dan orthophoto belum ada ("Segera hadir"). Tile belum membawa atribut. Render diuji di Chromium headless (GPU AMD iGPU dan renderer software), belum di GPU lain. |
| `data-pipeline/` | 🟢 **Impor resmi selesai (dev)** | CityGML (`raw/citygml/`, 31 berkas, 51.888 bangunan) → PostGIS → CityJSONSeq → tyler → `processed/3dtiles/` (15 kelurahan, 51.816 fitur). Registri ID resmi di `config/registri_id.csv`. Jalur lama CityJSON diarsipkan di luar repo. Skrip QC/normalisasi GeoJSON dan adapter sumber data (GeoJSON lokal, WFS, CSW) tetap ada. Lihat `STATUS.md`. |
| `backend/` | 🟡 **FastAPI kecil** | Layer geoportal (inspect WFS/CSW, kelola layer, cache); 20 tes pytest; pencegahan SSRF. **Belum ada** autentikasi, akses PostGIS, dan endpoint atribut bangunan (direncanakan, ADR-005). |
| PostGIS / basis data | ⚪ **Direncanakan** | Sumber kebenaran data bangunan (ADR-001); belum ada kontainer, migrasi, maupun skema. |
| Git / Versioning | 🟡 **Lokal** | Branch `main` + `feat/perbaikan-dan-redesign-ui`; **belum ada remote** (tidak ada cadangan di luar mesin ini). Data besar (`raw/`, `processed/`, `public/tiles/`) di-ignore. |
| Docker / Orkestrasi | 🔴 **Belum ada** | `docker-compose.yml` (PostGIS dev, tyler) direncanakan. Image lokal `3dgi/tyler` dan `geonode/postgis` sudah ada di mesin pengembangan. |

### 2.2. Keputusan Arsitektur (diterima 2026-11-19; implementasi direncanakan)
1. **Sumber bangunan tunggal = CityGML**; CityJSON lama (`raw/3d/`) sudah diarsipkan di luar repo (ADR-004).
2. **PostGIS** (Docker, terpisah dari GeoNode) = sumber kebenaran; skema lewat migrasi; cadangan `pg_dump` (ADR-001).
3. **ID bangunan** `BTG-BLD-xxxxxx` dari registri `core.registri_id`, tidak pernah dibuat ulang; `gml_id` hanya rujukan (ADR-003).
4. **Geometri:** bersihkan LOD2 asli (76,4% atap miring), bukan ekstrusi LOD1; Z dasar tile = 0, `z_dasar_sumber` disimpan (ADR-002).
5. **Tile statis; hasil simulasi sebagai data** dirujuk dengan ID bangunan (ADR-006). **Backend tetap FastAPI** (ADR-005).

### 2.3. Hutang Teknis & Catatan Prioritas (ringkas; rincian di `STATUS.md` §3)
1. **±4.779 bangunan hilang di tile** (Gunung Elai 1.897, Bontang Lestari 1.445, Belimbing 1.349, Loktuan 87): merge CityJSON berdasarkan ID numerik yang sebenarnya nomor di `gml:description` (dimulai dari 1 di tiap part). Teratasi hanya oleh pipeline baru (direncanakan).
2. **Atribut bangunan tidak ada di tile.** Sumber atribut kini ada di CityGML (`measuredHeight`, `storeysAboveGround`); Berebas Tengah (CityGML 3.0) tanpa atribut.
3. **ID bangunan tidak stabil** (path tile + `featureId`); `gml:id` CityGML bentrok (±103 dalam file, 2 antarfile). Diselesaikan registri ID (ADR-003).
4. **Data sumber bermasalah:** permukaan ganda 99,86%, Z dasar tidak konsisten di 5 file, label EPSG:32748 di 3 file (seharusnya 32650).
5. **Root tile kelurahan tanpa konten** (14 dari 15): dimitigasi kotak ikhtisar di klien; perbaikan permanen di ETL.
6. **Terrain DTM dan orthophoto belum ada** (UI "Segera hadir").
7. **Skrip ETL 01–03 lama tidak ada di repo**; digantikan pipeline baru yang direncanakan.
8. **Aset dev ikut ke `dist/`** (`frontend/public/tiles/`, ±126 MB); produksi seharusnya dari storage.
9. **Backend tanpa autentikasi**; layer WMS terblokir CORS GeoServer.

---

## 3. Prinsip Arsitektur & Aturan Keras (Core Rules)
1. **Aturan Geometri Bangunan vs Terrain:**
   - Workaround `renderBottom` / `renderSkirtDepth` pada POC murni trik rendering visual sementara, **BUKAN** data Authoritative Building Elevation atau Finished Floor Level (FFL).
   - Untuk data LOD2 CityJSON, geometri sudah berbentuk Solid 3D (atap miring, dinding, lantai dasar). Penempatan bangunan wajib mengandalkan titik dasar ground permukaan atau modifikasi terrain pad/clamping, bukan diekstrusi ulang dari 2D footprint.
   - **Catatan 2026-11-19 (ADR-002):** aturan ini tetap berlaku. Sumber LOD2 dibersihkan (salinan terbalik dibuang), **bukan** diekstrusi ulang dari footprint; 76,4% bangunan beratap miring. LOD1 hanya boleh diturunkan untuk analisis. Karena belum ada terrain, Z dasar bangunan di tile dinormalkan ke 0 per bangunan dan Z asli disimpan (`z_dasar_sumber`); ini **direncanakan** dan perlu ditinjau saat terrain tersedia.

2. **Skalabilitas Data 3D Kota:**
   - **DILARANG** memuat file CityJSON mentah atau GeoJSON masif secara langsung di browser/client-side.
   - Wajib menggunakan standar **OGC 3D Tiles v1.1** berbasis binary `.glb` terkompresi dengan hierarki spatial tree (Octree/Quadtree).
3. **Penyelarasan Koordinat (CRS):**
   - Data lokal Bontang menggunakan **EPSG:32650 (WGS 84 / UTM Zone 50N)**.
   - CesiumJS bekerja dalam **EPSG:4978 (ECEF)** dan **EPSG:4326 (WGS 84)**. Konversi koordinat wajib dilakukan pada pipeline ETL sebelum disajikan ke web.
4. **Pemisahan Tanggung Jawab Sistem:**
   - **Storage/MinIO:** Penyajian aset statis biner masif (3D Tiles, Terrain, Orthophoto tiles).
   - **PostGIS:** Sumber kebenaran data bangunan dan master data spasial relasional (vektor jalan, batas administrasi, saluran drainase, sungai, status FFL survei) — **direncanakan**, ADR-001.
   - **GeoServer:** Layanan standar OGC (WMS, WFS, Vector Tiles).
   - **Backend API (FastAPI, ADR-005):** Autentikasi, agregasi data, business logic, integrasi IoT/telemetri.
   - **Frontend (Vue 3 + Vite):** Rendering 3D, interaksi visual, UI kontrol layer, dan dashboard analitik.

---

## 4. Struktur Repositori Standar (Modular Monorepo)

> **Catatan:** Blok di bawah adalah struktur **target** (rencana). Tanda `(✓ ada)` menandai yang sudah terwujud di repositori, `(belum)` menandai yang masih direncanakan.

```text
spectra/                              # root repositori (Digital Twin Bontang)
├── data-pipeline/                    # ETL, tiling, dan konversi geospasial offline (✓ ada)
│   ├── raw/                          # Data mentah (.gitignore)
│   │   └── citygml/                  # CityGML per kelurahan: SUMBER TUNGGAL, read-only (✓ 15 kelurahan, 31 .gml)
│   ├── scripts/                      # (✓ sebagian) QC/normalisasi GeoJSON, sources/, fetch_sources.py, 04_build_master.py
│   │   └── (direncanakan)            # parser CityGML, ekspor CityJSONSeq, tyler (Docker), registri ID — nama belum final
│   ├── config/                       # (✓) sources.yaml, kelurahan_map.csv; ekspor registri ID (direncanakan, di-commit)
│   ├── reports/                      # (✓) laporan QC dan inventaris (citygml_inventory.md)
│   ├── processed/                    # Output lokal (.gitignore)
│   │   ├── 3dtiles/                  # (✓) tile 15 kelurahan, 51.816 fitur, hasil pipeline CityGML; master-tileset.json; sumber `frontend/public/tiles`
│   │   ├── terrain-tiles/            # (belum) Quantized-mesh terrain
│   │   └── ortho-tiles/              # (belum) XYZ tiles PNG
│   └── docker/                       # (belum) toolchain; tyler kini lewat image lokal 3dgi/tyler
│
├── frontend/                         # Web App Client (Vue 3 + Vite SPA) (✓ ada)
│   ├── public/                       # (✓ ada)
│   │   └── tiles/                    # Aset 3D untuk pengujian lokal (belum terisi)
│   ├── src/
│   │   ├── assets/                   # Style global, CSS, ikon (✓ main.css)
│   │   ├── components/
│   │   │   ├── map/                  # CesiumCanvas.vue (✓) · NavigationControl.vue (belum)
│   │   │   ├── panels/               # LayerControl.vue (✓) · ObjectInfoPanel.vue (✓)
│   │   │   ├── simulation/           # FloodSlider.vue, AnalysisTool.vue (belum)
│   │   │   └── common/               # BaseButton.vue, Modal.vue, Tabs.vue (belum)
│   │   ├── composables/              # Logika CesiumJS (bebas dari Vue reactivity biasa)
│   │   │   ├── useCesium.js          # Inisialisasi Viewer, shallowRef, kamera (✓)
│   │   │   ├── use3DTiles.js         # Loading Master 3D Tileset, styling, picking (✓)
│   │   │   ├── useLayers.js          # Basemap (OSM/ArcGIS), Orthophoto, WMS (✓ sebagian)
│   │   │   └── useObjectSelect.js    # Raycasting/picking objek & kamera focus (belum, picking kini inline di use3DTiles.js)
│   │   ├── stores/                   # Pinia Stores
│   │   │   ├── mapStore.js           # Status kamera, terrain ON/OFF, opacity (✓)
│   │   │   ├── layerStore.js         # Visibility layer spasial (belum)
│   │   │   └── objectStore.js        # Atribut Digital Twin objek terpilih (✓)
│   │   ├── services/                 # Axios / Fetch HTTP API (belum)
│   │   │   ├── geoserver.js          # Konektor WFS/WMS
│   │   │   └── buildingApi.js        # Endpoint data atribut bangunan
│   │   ├── App.vue                   # (✓)
│   │   └── main.js                   # (✓)
│   ├── package.json                  # (✓)
│   └── vite.config.js                # (✓)
│
├── backend/                          # FastAPI (ADR-005) (✓ layer geoportal; PostGIS dan atribut bangunan direncanakan)
│   ├── app/                          # main.py, geoportal.py, guard.py, registry.py (✓)
│   ├── config/                       # allowed_hosts (✓)
│   └── tests/                        # pytest (✓ 20 tes)
│
├── docs/                             # remote-layers.md, simulation-contract.md, adr/ (ADR-001–006), audit/ (✓)
├── docker-compose.yml                # Orkestrasi: PostGIS dev, GeoServer, MinIO (belum; direncanakan)
└── README.md                         # Panduan setup & deployment (belum di root)
```

---

## 5. Pipeline Pengolahan Data 3D Bangunan (CityGML -> PostGIS -> 3D Tiles)

> **Status:** bagian 5.3 s.d. 5.5 menjelaskan pipeline yang **direncanakan** (ADR-001 s.d. ADR-004). Belum ada skripnya di repo; nama perintah belum final.
> Tile yang dipakai frontend berasal dari pipeline ini (impor resmi 2026-11-20).

### 5.1. Tool
- **Parser streaming milik sendiri (direncanakan):** Python (stdlib + shapely) untuk CityGML 2.0 dan 3.0. Alasan: `citygml-tools` tidak ada, `cjio` hanya membaca CityJSON, dan GDAL tidak punya driver CityGML. Berkas dibaca per `cityObjectMember` (tanpa memuat 3,5 GB ke memori).
- **PostGIS (direncanakan):** sumber kebenaran, Docker terpisah dari GeoNode (ADR-001).
- **Konverter 3D Tiles: `3dgi/tyler`** lewat image Docker lokal `3dgi/tyler:latest` (tyler 1.0.0-alpha1). Input harus CityJSON/CityJSONSeq. Opsi relevan: `--object-attributes <nama:tipe,...>` (atribut → `EXT_structural_metadata`), `--3dtiles-metadata-class`, `--object-type Building`, `--color-building #RRGGBB`, `--grid-cellsize`, `--qtree-capacity`.
- **`cjio`:** tidak dipakai di pipeline; hanya untuk ringkasan CityJSON (`cjio info`).

### 5.2. Spesifikasi Data Mentah Aktual
- **Sumber tunggal: `data-pipeline/raw/citygml/`** (read-only): 31 berkas `.gml` (3,5 GB) + 1 `.gfs` (skema GDAL). 30 berkas CityGML 2.0 dan 1 berkas **CityGML 3.0** (Berebas Tengah). **51.888 bangunan** (51.887 unik berdasarkan posisi), tanpa `BuildingPart`, LOD2, 15 dari 15 kelurahan, semua XML valid. Multi-part: Belimbing (3), Bontang Lestari (8), Guntung (3), Gunung Elai (3), Loktuan (4).
- **CRS:** EPSG:32650 (UTM 50N). **Tiga berkas berlabel EPSG:32748** (Guntung Part I, Guntung Part II, Satimpo) padahal koordinatnya EPSG:32650; dikoreksi lewat konfigurasi eksplisit per berkas.
- **Atribut:** `measuredHeight` (= tinggi geometri, dibulatkan) dan `storeysAboveGround` informatif; sebelas atribut lain bernilai bawaan sama untuk semua bangunan. Berebas Tengah (3.0) tanpa atribut.
- **Masalah sumber:** 99,86% poligon punya salinan terbalik (label atap/lantai tertukar); Z dasar bervariasi di 5 berkas (median −15,4 m s.d. +5,4 m; berkas lain 0,001 m); ±103 `gml:id` bentrok dalam berkas dan 2 antarberkas; 22 bangunan ber-`measuredHeight` 0 dan 57 setinggi < 0,1 m.
- **Arsip:** CityJSON lama (37 berkas, ±281 MB) sudah diarsipkan di luar repo; bukan sumber lagi.

### 5.3. Alur Eksekusi (direncanakan)
1. **Impor ke `staging`:** parser streaming membaca `raw/citygml/` (semua part per kelurahan disatukan, termasuk Loktuan Part II–IV); CRS berkas berlabel 32748 dikoreksi lewat konfigurasi eksplisit.
2. **Normalisasi ke `core.bangunan`:** buang salinan terbalik dan duplikat searah, perbaiki label permukaan, hitung footprint/tinggi/`luas_tapak`, normalkan Z dasar ke 0 (simpan `z_dasar_sumber`), beri `qc_flag` (ADR-002).
3. **Penerbitan ID:** `BTG-BLD-xxxxxx` dari `core.registri_id`; `gml_id` asli disimpan sebagai rujukan (ADR-003). Ekspor registri ke CSV di `data-pipeline/config/` (di-commit).
4. **Ekspor CityJSONSeq bersih per kelurahan** dari PostGIS (tanpa bangunan setinggi < 0,1 m).
5. **tyler (Docker):** CityJSONSeq → `data-pipeline/processed/3dtiles/<slug>/` dengan metadata dan warna `#B1BAC2` (tyler menganggap hex linear, sehingga tampil `#D9DEE2`).
6. **Master tileset:** `04_build_master.py --sync` (membaca `processed/3dtiles/`, mengisi `frontend/public/tiles/`).
7. **Verifikasi di frontend** (picking `Cesium3DTileFeature`, atribut di panel, kotak ikhtisar) (selesai; tile lama sudah dihapus).

### 5.4. Aturan Data Bangunan (direncanakan)
- Atribut di tile: `id`, `gml_id`, `nama` ("Bangunan BTG-BLD-xxxxxx"), `tinggi`, `jumlah_lantai`, `luas_tapak`. Nilai bawaan CityGML tidak dibawa. Berebas Tengah: `tinggi` dari geometri, `jumlah_lantai` kosong.
- Bangunan setinggi < 0,1 m tidak masuk tile tetapi tetap di basis data (`qc_flag`); footprint < 2 m² hanya ditandai.
- LOD1 boleh diturunkan hanya untuk analisis; tampilan memakai LOD2 yang dibersihkan.

### 5.5. Kontrak Tile dengan Frontend (frontend tidak diubah)
- Tile di `processed/3dtiles/<slug>/tileset.json` dengan 15 slug yang sama seperti sekarang; `boundingVolume.region`; 3D Tiles 1.1 + `3DTILES_content_gltf`; `.glb` di `<slug>/…`.
- `EXT_structural_metadata` terhubung ke `EXT_mesh_features`, sehingga picking mengembalikan `Cesium3DTileFeature`. Frontend mencari ID di `id`/`gml_id`, nama di `name`/`nama`, tinggi di `measuredHeight`/`height`/`tinggi`; semua properti ditampilkan apa adanya (nilai skalar saja).
- Bangunan berbasis Z = 0 (globe tanpa terrain). Root kelurahan tanpa konten memunculkan kotak ikhtisar; `geometricError` root master tidak diperkecil.
- Warna model `#D9DEE2` (sama dengan `MAP_COLORS.building`). Konten `.glb` ≤ ±3 MB per tile.

---

## 6. Standar Model Objek Digital Twin (Schema)

> **Status:** rancangan; skema final ditetapkan di berkas migrasi PostGIS (**direncanakan**, ADR-001). Tabel di bawah adalah arah, bukan skema yang sudah ada.

### 6.1. Tabel `core.bangunan` (rancangan)
| Kolom | Tipe (usulan) | Keterangan |
|-------|---------------|------------|
| `id` | teks, PK | `BTG-BLD-xxxxxx`, dari `core.registri_id`; tidak pernah dibuat ulang (ADR-003). |
| `gml_id` | teks | `gml:id` asli CityGML; rujukan, **boleh tidak unik**. |
| `kelurahan` | teks | Slug kelurahan (`api_api`, …). |
| `tinggi` | angka (m) | Dari `measuredHeight` atau, bila kosong (Berebas Tengah), dari geometri. |
| `jumlah_lantai` | bilangan bulat, boleh kosong | `storeysAboveGround`; kosong untuk Berebas Tengah. |
| `luas_tapak` | angka (m²) | Luas footprint (EPSG:32650). |
| `z_dasar_sumber` | angka (m) | Z dasar asli dari sumber; tile memakai 0 (ADR-002). |
| `qc_flag` | kode/daftar kode | Mis. tinggi < 0,1 m (tidak masuk tile), footprint < 2 m², tanpa footprint, komponen tidak valid. |
| geometri | PostGIS | Footprint (EPSG:32650) dan geometri LOD2 yang dibersihkan; bentuk simpan ditentukan saat desain skema. |

`core.registri_id` menyimpan ID yang pernah diterbitkan beserta `gml_id`, kelurahan, dan pusat footprint sumbernya; diekspor ke CSV di `data-pipeline/config/`. Aturan (ADR-003, **direncanakan**):

**Pencocokan tiap impor**, berurutan:
1. `gml_id` sama, kelurahan sama, `gml_id` unik di batch, dan pusat footprint bergeser ≤ 2 m.
2. Jika tidak: pusat footprint ≤ 2 m dan IoU footprint ≥ 0,5.
3. Lebih dari satu kandidat: pilih IoU tertinggi; bila selisih IoU < 0,1, masuk daftar tinjauan manual tanpa ID.
4. Tidak ada kecocokan: terbitkan ID baru dengan nomor berikutnya.

**Footprint kosong** di salah satu sisi: dianggap sama bila jarak pusat bounding box 3D ≤ 2 m dan selisih tinggi ≤ 0,5 m; lebih dari satu kandidat masuk tinjauan manual tanpa ID. Footprint kosong tidak pernah dianggap IoU 1,0.

**Aturan tetap:** nomor ID tidak pernah dipakai ulang; bangunan yang hilang dari impor baru ditandai nonaktif dengan tanggal berakhir (tidak dihapus); perubahan geometri atau tinggi pada bangunan yang sama memakai ID yang sama dengan versi baru di riwayat; penomoran pertama deterministik (urut slug, `gml_id`, lalu koordinat pusat footprint); setiap impor menghasilkan laporan jumlah cocok lewat `gml_id`, cocok lewat posisi, ID baru, nonaktif, dan tinjauan manual.

### 6.2. Properti di tile (direncanakan)
Dibaca frontend lewat `EXT_structural_metadata` (nilai skalar saja):
```json
{
  "id": "BTG-BLD-000001",
  "gml_id": "BS_02092025-AAAA-00001-GeoAI01-05629B4",
  "nama": "Bangunan BTG-BLD-000001",
  "tinggi": 3.21,
  "jumlah_lantai": 1,
  "luas_tapak": 65.8
}
```
Backend (direncanakan) memenuhi kontrak lookup frontend `GET /buildings/{id}/attributes` dengan kunci yang dikenal `ATTRIBUTE_KEYS` (mis. `name`, `height`).

### 6.3. Elevasi dan terrain (setelah DTM tersedia; direncanakan)
Skema `elevasi` akan menyimpan elevasi tanah, lantai, dan atap per bangunan (mis. `terrainMin/Median/Max`, `isSurveyedFFL`) agar simulasi banjir dapat membandingkan muka air dengan elevasi lantai. Workaround `renderBottom`/`renderSkirtDepth` pada POC bukan elevasi lantai (FFL) otoritatif (lihat §3.1).

---

## 7. Frontend Coding Standards (CesiumJS + Vue 3)
1. **Isolasi Instance Viewer:**
   Instance `Cesium.Viewer` **TIDAK BOLEH** disimpan di dalam Vue `ref()` atau `reactive()` biasa karena proxy reaktivitas akan melacak ribuan properti internal WebGL yang memicu kebocoran memori. Wajib gunakan `shallowRef()` atau `markRaw()`:
   ```javascript
   import { shallowRef } from 'vue';
   export const viewer = shallowRef(null);
   ```
   > ✓ Sudah diterapkan di `src/composables/useCesium.js`.
2. **Pemuatan 3D Tiles:**
   ```javascript
   const tileset = await Cesium.Cesium3DTileset.fromUrl('/tiles/master-tileset.json', {
     maximumScreenSpaceError: 24, // mengikuti Mode tampilan (16/24/32)
     cacheBytes: 512 * 1024 * 1024, // maximumMemoryUsage tidak ada lagi di Cesium 1.146
     cullWithChildrenBounds: true,
     skipLevelOfDetail: true
   });
   viewer.value.scene.primitives.add(tileset);
   ```
   > ✓ Sudah diterapkan di `src/composables/use3DTiles.js`; opsi ada di `TILESET_OPTIONS`.
3. **Picking & Highlight:**
   Gunakan `Cesium.ScreenSpaceEventType.LEFT_CLICK` dengan `scene.pick()`. Tampilkan panel atribut melalui Pinia Store (`objectStore.selectObject(...)`).
   > ✓ Sudah diterapkan secara inline di `use3DTiles.js`. **Catatan:** PRD awal merencanakan logika ini dipindah ke `composables/useObjectSelect.js` — refactor opsional untuk pemisahan tanggung jawab.
4. **Terrain Provider:**
   Toggle terrain di `mapStore.isTerrainActive` harus benar-benar mengganti provider:
   - **ON:** quantized-mesh terrain 1m lokal (`CesiumTerrainProvider.fromUrl('/tiles/terrain-tiles/')`) atau Cesium World Terrain sebagai fallback.
   - **OFF:** `EllipsoidTerrainProvider()`.
   > 🔴 Belum diterapkan — saat ini kedua cabang memakai `EllipsoidTerrainProvider()`.
5. **Orthophoto Layer:**
   State `isOrthophotoActive` dan `orthoOpacity` di `mapStore` harus di-wire ke `UrlTemplateImageryProvider` (XYZ tiles) di `useLayers.js`, termasuk watcher untuk `alpha`/opacity.
   > 🔴 Belum diterapkan.
6. **Render hemat GPU:**
   Viewer memakai `requestRenderMode: true`; setiap perubahan visual yang tidak memicu render otomatis memanggil `requestRender()` (`useCesium.js`). Mode tampilan Hemat/Seimbang/Kualitas (`utils/displayModes.js`) mengatur resolusi, anti-aliasing, SSE, dan efek.
   > ✓ Sudah diterapkan.
7. **Konvensi Umum:**
   - Alias impor `@` → `src/` (sudah di-set di `vite.config.js`).
   - Dev server berjalan di port `3000`.
   - Styling pakai Tailwind; palet kustom tersedia di namespace `bontang.*` (`tailwind.config.js`).

---

## 8. Roadmap & Milestone Selanjutnya

> Semua milestone di bawah **belum dikerjakan** kecuali dinyatakan lain. Urutan mengikuti ADR-001 s.d. ADR-006.

### 8.1. Milestone Fungsional
- [ ] **Milestone 1 — Fondasi data:** PostGIS dev di Docker (terpisah dari GeoNode), migrasi skema `core`/`ref`/`elevasi`/`sim`/`staging`, jadwal `pg_dump` (ADR-001).
- [ ] **Milestone 2 — Impor CityGML:** parser streaming (2.0 dan 3.0) → `staging` → `core`; koreksi CRS per berkas; penyatuan semua part; pembersihan LOD2, normalisasi Z, `qc_flag`; registri ID `BTG-BLD-xxxxxx` dan ekspor CSV (ADR-002/003/004).
- [x] **Milestone 3 — Tile:** ekspor CityJSONSeq per kelurahan → `tyler` (Docker) → `processed/3dtiles/`; `04_build_master.py` disederhanakan; verifikasi picking dan atribut di viewer (selesai 2026-11-20; tile lama dihapus).
- [ ] **Milestone 4 — Backend data bangunan:** akses PostGIS, endpoint `GET /buildings/{id}/attributes`, autentikasi dan hak tambah/hapus layer, keputusan WMS (CORS atau proxy) (ADR-005).
- [ ] **Milestone 5 — Terrain dan elevasi:** DTM (quantized-mesh), skema `elevasi`, elevasi dasar bangunan; orthophoto.
- [ ] **Milestone 6 — Simulasi banjir/rob:** skema `sim`, endpoint hasil, styling per fitur di frontend melalui kontrak simulasi (ADR-006; `docs/simulation-contract.md`).

### 8.2. Perbaikan Teknis (Technical Debt — kerjakan paralel)
- [ ] Remote git dan kebijakan cadangan data mentah/tile/registri di luar repo.
- [ ] Perbarui `frontend/README.md` dan tambahkan `README.md` di root (setup monorepo, backend, docker-compose).
- [ ] Linter (eslint, ruff) dan tes otomatis untuk `use3DTiles.js` dan `useRemoteLayers.js`.
- [ ] Terrain provider nyata di `useLayers.js` (lihat §7.4) dan orthophoto (lihat §7.5).
- [ ] Autentikasi backend, `.env.example`, dan satu perintah menjalankan backend + frontend.
- [ ] Putuskan keputusan data GeoJSON tertunda (pulau, "Drainase Dahllia", `_5k`, RT duplikat, `luaswh` Guntung).

---

## 9. Arsitektur Jangka Panjang (direncanakan)

> **Status: direncanakan.** Tidak ada bagian di bawah yang sudah ada. Alasan dan alternatif: ADR-001 s.d. ADR-006 di `docs/adr/`.

```text
raw/citygml/ (read-only) --parser--> PostGIS [staging -> core] --ekspor--> CityJSONSeq --tyler--> processed/3dtiles/
                                        |  ref  elevasi  sim                                         |
                                        |                                                             v
                                   Backend FastAPI  <-- atribut, hasil simulasi -->  Frontend (Cesium; tile statis + styling per fitur)
```

| Skema | Isi | ADR |
|-------|-----|-----|
| `staging` | Impor mentah sementara dari CityGML (belum dibersihkan; dapat dihapus setelah impor sukses). | 001, 004 |
| `core` | `bangunan` (atribut, footprint, geometri LOD2 bersih, `z_dasar_sumber`, `qc_flag`) dan `registri_id` (ID `BTG-BLD-xxxxxx`). | 001, 002, 003 |
| `ref` | Data referensi: kelurahan, RT, sungai/drainase, kode, sumber data. | 001 |
| `elevasi` | DTM/DEM dan elevasi dasar/lantai bangunan (setelah terrain tersedia). | 001, 002 |
| `sim` | Hasil simulasi per skenario dan versi, dirujuk dengan ID bangunan. | 006 |

Prinsip: (1) PostGIS adalah sumber kebenaran, tile adalah turunan; (2) ID bangunan dibuat sekali dan tidak pernah dibuat ulang; (3) tile bangunan statis, hasil simulasi berupa data yang ditampilkan lewat styling per fitur (frontend perlu helper baru dan `requestRender()`); (4) data mentah (`raw/`) read-only; (5) backend tetap FastAPI dan browser hanya memanggil `/api`.
