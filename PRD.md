# MASTER HANDOFF & PRD: DIGITAL TWIN KOTA BONTANG (3D WEB GIS)

> **Nama Proyek / Repositori:** `spectra` (Digital Twin Kota Bontang)
> **Versi Dokumen:** 1.2
> **Terakhir Diperbarui:** 2026-11-02
> **Status Global:** Transisi POC → Scale-Up Skala Kota (15 Kelurahan)

---

## 1. Ringkasan Eksekutif & Gambaran Umum
Proyek ini bertujuan membangun **Digital Twin Kota Bontang** berbasis Web 3D GIS menggunakan **CesiumJS**. Sistem ini bukan sekadar penampil 3D (viewer), melainkan platform integrasi geospasial kota untuk simulasi banjir/rob, pemantauan infrastruktur, integrasi data sensor/IoT, dan Decision Support System (DSS) Pemkot Bontang.

Tahap Proof of Concept (POC) di kawasan **Kantor Walikota Bontang** telah sukses memvalidasi integrasi:
- DTM resolusi 1m (GeoTIFF UTM EPSG:32650 -> Quantized-mesh Cesium Terrain).
- Orthophoto resolusi 5cm (XYZ imagery tiles PNG, EPSG:32650).
- Ekstrusi bangunan 3D dari GeoJSON (8 bangunan) dengan sampling elevasi terrain bertingkat.

Tahap selanjutnya adalah **Scale-Up Skala Kota (15 Kelurahan)** dengan data bangunan berformat **CityJSON v2.0 LOD2 Solid** (~194 MB total, terbagi per kelurahan ~20 MB).

---

## 2. Status Proyek Saat Ini (Snapshot Implementasi)

Ringkasan kondisi repositori per **2026-11-02**. Rincian verifikasi dan hutang teknis lengkap
ada di `STATUS.md` (sumber kebenaran status). Catatan: §4 (struktur), §5.2 (data mentah) dan
§7–§8 masih ditulis dari sudut pandang awal proyek; bila bertentangan, ikuti §2 ini dan `STATUS.md`.

### 2.1. Status per Modul

| Modul | Status | Keterangan |
|-------|--------|------------|
| `frontend/` | 🟡 **Berjalan, render belum diuji penuh** | Vue 3 + Vite 5 + Cesium **1.146.0** (di-pin) + Pinia + Tailwind. Memuat satu `master-tileset.json` (15 kelurahan), picking `LEFT_CLICK`, ikhtisar kelurahan untuk kamera jauh, penanganan error init viewer, state atribut bangunan. Terrain & orthophoto belum ada (UI menampilkan "Segera hadir"). |
| `data-pipeline/` | 🟡 **Sebagian** | Data mentah CityJSON **15 kelurahan** ada di `raw/3d/` (±281 MB, sebagian masih berupa beberapa part). 3D Tiles v1.1 sudah jadi untuk 15 kelurahan (`processed/3dtiles/`, 125 `.glb`, ±131 MB) + `master-tileset.json`. Di repo hanya ada `scripts/04_build_master.py`; langkah merge/clean (`cjio`) dan konversi (`tyler`) dijalankan di luar repo — belum reproducible. |
| `backend/` | ⚪ **Belum dimulai** | Framework (Laravel vs FastAPI) belum diputuskan. Frontend sudah menyiapkan klien lookup atribut (`services/buildingAttributes.js`, aktif bila `VITE_API_BASE_URL` diisi). |
| Git / Versioning | 🟡 **Lokal** | Repositori git aktif (branch `master` + branch kerja), belum ada remote. `.gitignore` sudah benar: hanya `raw/*`, `processed/*`, `frontend/public/tiles/*` yang di-ignore; `scripts/` dilacak. |
| Docker / Orkestrasi | 🔴 **Belum ada** | `docker-compose.yml` belum dibuat. |

### 2.2. Hutang Teknis & Catatan Prioritas (Known Gaps)

1. **Atribut bangunan tidak ada di tile.** Seluruh `.glb` hanya membawa `EXT_mesh_features` (tanpa `EXT_structural_metadata`); CityJSON mentah yang diperiksa juga tanpa `attributes`. Panel info hanya bisa menampilkan kelurahan, tile, dan koordinat. Butuh sumber atribut + ID bangunan permanen di tile.
2. **Root tile kelurahan tanpa konten** (14 dari 15, kecuali `bontang_lestari`). Dari jauh tidak ada bangunan dirender; frontend sementara menampilkan kotak ikhtisar per kelurahan. Perbaikan permanen di ETL — lihat `TODO(ETL)` di `04_build_master.py`.
3. **Terrain DTM 1m belum tersedia** di proyek (tidak ada quantized-mesh/`layer.json`). Toggle disembunyikan sampai data ada.
4. **Orthophoto belum ada.** State orthophoto sudah dihapus dari `mapStore`; tambahkan kembali bersama layer-nya.
5. **Skrip ETL `01`–`03` belum di repo** (merge, clean, tyler).
6. **Aset dev ikut ke `dist/`.** `frontend/public/tiles/` (±126 MB) tersalin saat `npm run build`; produksi seharusnya dari MinIO/storage.
7. **Keputusan backend tertunda.** Pilih Laravel atau FastAPI sebelum merancang skema PostGIS (Milestone 4).

---

## 3. Prinsip Arsitektur & Aturan Keras (Core Rules)
1. **Aturan Geometri Bangunan vs Terrain:**
   - Workaround `renderBottom` / `renderSkirtDepth` pada POC murni trik rendering visual sementara, **BUKAN** data Authoritative Building Elevation atau Finished Floor Level (FFL).
   - Untuk data LOD2 CityJSON, geometri sudah berbentuk Solid 3D (atap miring, dinding, lantai dasar). Penempatan bangunan wajib mengandalkan titik dasar ground permukaan atau modifikasi terrain pad/clamping, bukan diekstrusi ulang dari 2D footprint.
2. **Skalabilitas Data 3D Kota:**
   - **DILARANG** memuat file CityJSON mentah atau GeoJSON masif secara langsung di browser/client-side.
   - Wajib menggunakan standar **OGC 3D Tiles v1.1** berbasis binary `.glb` terkompresi dengan hierarki spatial tree (Octree/Quadtree).
3. **Penyelarasan Koordinat (CRS):**
   - Data lokal Bontang menggunakan **EPSG:32650 (WGS 84 / UTM Zone 50N)**.
   - CesiumJS bekerja dalam **EPSG:4978 (ECEF)** dan **EPSG:4326 (WGS 84)**. Konversi koordinat wajib dilakukan pada pipeline ETL sebelum disajikan ke web.
4. **Pemisahan Tanggung Jawab Sistem:**
   - **Storage/MinIO:** Penyajian aset statis biner masif (3D Tiles, Terrain, Orthophoto tiles).
   - **PostGIS:** Master data spasial relasional (vektor jalan, batas administrasi, saluran drainase, sungai, status FFL survei).
   - **GeoServer:** Layanan standar OGC (WMS, WFS, Vector Tiles).
   - **Backend API:** Autentikasi, agregasi data, business logic, integrasi IoT/telemetri.
   - **Frontend (Vue 3 + Vite):** Rendering 3D, interaksi visual, UI kontrol layer, dan dashboard analitik.

---

## 4. Struktur Repositori Standar (Modular Monorepo)

> **Catatan:** Blok di bawah adalah struktur **target** (rencana). Tanda `(✓ ada)` menandai yang sudah terwujud di repositori, `(belum)` menandai yang masih direncanakan.

```text
spectra/                              # root repositori (Digital Twin Bontang)
├── data-pipeline/                    # ETL, tiling, dan konversi geospasial offline (✓ ada)
│   ├── raw/                          # Data mentah (.gitignore)
│   │   └── 3d/                       # CityJSON LOD2 per kelurahan (✓ 1 kelurahan: Bontang Kuala)
│   │       └── "Kelurahan Bontang Kuala/Model 3D - Kelurahan Bontang Kuala.json"
│   ├── scripts/                      # Skrip otomatisasi pemrosesan (belum)
│   │   ├── 01_merge_parts.py         # Menggabungkan part CityJSON per kelurahan
│   │   ├── 02_clean_compress.py      # Deduplikasi vertex & kuantisasi via cjio
│   │   ├── 03_run_tyler.sh           # Konversi CityJSON ke 3D Tiles v1.1 via 3dgi/tyler
│   │   └── 04_build_master.py        # Kompilasi master root tileset.json Kota Bontang
│   ├── processed/                    # Output lokal siap deploy (.gitignore) (belum terisi)
│   │   ├── terrain-tiles/            # Quantized-mesh terrain (layer.json, *.terrain)
│   │   ├── ortho-tiles/              # XYZ tiles PNG ({z}/{x}/{y}.png)
│   │   └── 3dtiles/                  # Folder 3D Tiles per kelurahan (*.glb + tileset.json)
│   └── docker/                       # Dockerfile toolchain (GDAL, terrainwarp, tyler) (belum)
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
├── backend/                          # API Server (Laravel ATAU FastAPI — belum diputuskan) (⚪ kosong)
│   ├── app/                          # Controller, Model, Entity
│   ├── database/migrations/          # DDL PostGIS tabel master
│   └── routes/                       # API endpoints objek & spasial query
│
├── docker-compose.yml                # Orkestrasi: PostGIS, GeoServer, MinIO (belum)
└── README.md                         # Panduan setup & deployment (belum di root)
```

---

## 5. Pipeline Pengolahan Data 3D Bangunan (CityJSON -> 3D Tiles)

### 5.1. Tool Rekomendasi
- **Penggabungan & Optimasi Mentah:** `cjio` (Python CLI).
- **Konverter 3D Tiles Utama:** **`3dgi/tyler`** (Rust binary).
  - *Alasan:* Menghasilkan standar **3D Tiles v1.1** biner `.glb` terkompresi dengan metadata semantik (`EXT_structural_metadata`). Jauh lebih stabil dan cepat dibanding `py3dtilers` (deprecated) atau wrapper Node.js.

### 5.2. Spesifikasi Data Mentah Aktual
Satu-satunya data yang tersedia saat ini:
- **File:** `data-pipeline/raw/3d/Kelurahan Bontang Kuala/Model 3D - Kelurahan Bontang Kuala.json`
- **Format:** CityJSON v2.0, LOD2 Solid.
- **CRS:** EPSG:32650 (WGS 84 / UTM Zone 50N).
- **Geographical Extent (UTM):** `[555260.99, 13409.15, 0.001] → [558074.23, 16084.98, 20.83]`.
- **Ukuran:** ~7.9 MB.

> Data 14 kelurahan lainnya belum tersedia di repositori. Pipeline harus dirancang per-kelurahan dan idempoten agar bisa dijalankan ulang saat data baru masuk.

### 5.3. Alur Eksekusi
1. **Merge Part Files (jika terbagi):**
   ```bash
   cjio part1.city.json merge part2.city.json save kelurahan_merged.city.json
   ```
   > Untuk Bontang Kuala saat ini hanya satu file utuh, langkah ini dapat dilewati.
2. **Clean & Quantize:**
   ```bash
   cjio kelurahan_merged.city.json clean compress save kelurahan_clean.city.json
   ```
3. **Generate 3D Tiles v1.1:**
   ```bash
   tyler \
     --input ./data-pipeline/raw/cityjson/kelurahan_clean.city.json \
     --output ./data-pipeline/processed/3dtiles/bontang_kuala \
     --format 3dtiles \
     --object-type Building
   ```
4. **Master Root Tileset:**
   Buat satu `master-tileset.json` di tingkat root yang mereferensikan masing-masing sub-tileset kelurahan sebagai *external tile children* untuk membatasi beban memory streaming kamera CesiumJS. Hasil akhir disalin/di-symlink ke `frontend/public/tiles/master-tileset.json` untuk pengujian lokal.

---

## 6. Standar Model Objek Digital Twin (Schema)
Setiap objek bangunan yang diidentifikasi dalam sistem wajib mengikuti skema struktur data standar berikut:

```json
{
  "identity": {
    "id": "BTG-BLD-000001",
    "name": "Gedung Utama Kantor Walikota",
    "kelurahan": "Bontang Lestari",
    "kecamatan": "Bontang Selatan",
    "category": "Pemerintahan"
  },
  "source": {
    "lod": "2",
    "footprintArea": 5753.94,
    "height": 18.5,
    "sourceFormat": "CityJSON v2.0"
  },
  "elevation": {
    "terrainMin": 12.73,
    "terrainMedian": 29.84,
    "terrainMax": 46.44,
    "groundElevation": 29.84,
    "floorElevation": 29.89,
    "roofElevation": 48.39,
    "isSurveyedFFL": false
  },
  "spatial": {
    "center": [117.4458, 0.0682],
    "crs": "EPSG:32650"
  }
}
```

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
     maximumScreenSpaceError: 16,
     maximumMemoryUsage: 512,
     cullWithChildrenBounds: true,
     skipLevelOfDetail: true
   });
   viewer.value.scene.primitives.add(tileset);
   ```
   > ✓ Sudah diterapkan di `src/composables/use3DTiles.js` (data tileset masih menunggu Milestone 2).
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
6. **Konvensi Umum:**
   - Alias impor `@` → `src/` (sudah di-set di `vite.config.js`).
   - Dev server berjalan di port `3000`.
   - Styling pakai Tailwind; palet kustom tersedia di namespace `bontang.*` (`tailwind.config.js`).

---

## 8. Roadmap & Milestone Selanjutnya

### 8.1. Milestone Fungsional
- [ ] **Milestone 1:** Eksekusi skrip ETL merge & clean CityJSON (mulai dari Kelurahan Bontang Kuala) via `cjio`.
- [ ] **Milestone 2:** Konversi data kelurahan menjadi 3D Tiles v1.1 menggunakan `3dgi/tyler` dan pembentukan `master-tileset.json`.
- [ ] **Milestone 3:** Integrasi rendering master 3D tileset di frontend (sudah ter-scaffold; tinggal menyediakan data + verifikasi di viewer).
- [ ] **Milestone 4:** Keputusan framework backend → perancangan skema PostGIS → integrasi layer batas kelurahan/jalan/drainase via GeoServer.
- [ ] **Milestone 5:** Pembuatan skenario layer visual simulasi genangan banjir/rob pada terrain 3D (`components/simulation/`).

### 8.2. Perbaikan Teknis (Technical Debt — kerjakan paralel)
- [ ] Inisialisasi Git repository + perbaiki `.gitignore` (hapus prefix `./`, ignore `raw/` & `processed/` saja, bukan seluruh `data-pipeline/`).
- [ ] Implementasi terrain provider nyata di `useLayers.js` (lihat §7.4).
- [ ] Implementasi orthophoto imagery layer + kontrol opacity (lihat §7.5).
- [ ] Tambahkan `README.md` di root (panduan setup monorepo + `docker-compose.yml`).
- [ ] Lengkapi direktori terencana: `services/`, `stores/layerStore.js`, `components/common/`, `components/simulation/`.
