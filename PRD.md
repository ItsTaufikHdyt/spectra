# MASTER HANDOFF & PRD: DIGITAL TWIN KOTA BONTANG (3D WEB GIS)

> **Nama Proyek / Repositori:** `spectra` (Digital Twin Kota Bontang)
> **Versi Dokumen:** 1.1
> **Terakhir Diperbarui:** 2026-10-09
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

Bagian ini merefleksikan kondisi repositori secara aktual agar tidak terjadi kesalahpahaman antara rencana PRD dan apa yang sudah dibangun.

### 2.1. Status per Modul

| Modul | Status | Keterangan |
|-------|--------|------------|
| `frontend/` | 🟡 **Scaffolding berjalan** | Vue 3 + Vite + Cesium 1.119 + Pinia + Tailwind. Viewer, basemap, panel UI, picking sudah ada. Terrain & orthophoto belum tersambung. |
| `data-pipeline/` | 🔴 **Belum dieksekusi** | Hanya tersedia 1 data mentah (Kelurahan Bontang Kuala). Folder `scripts/` & `processed/` masih kosong. |
| `backend/` | ⚪ **Kosong / belum dimulai** | Framework (Laravel vs FastAPI) belum diputuskan final. |
| Git / Versioning | 🔴 **Belum diinisialisasi** | Direktori belum menjadi git repository. |
| Docker / Orkestrasi | 🔴 **Belum ada** | `docker-compose.yml` belum dibuat. |

### 2.2. Hutang Teknis & Catatan Prioritas (Known Gaps)

1. **Terrain belum tersambung.** `useLayers.js` masih memakai `EllipsoidTerrainProvider()` (bola kosong) pada kedua cabang toggle ON/OFF. Belum ada quantized-mesh terrain 1m lokal maupun Cesium World Terrain yang di-wire.
2. **Orthophoto & opacity belum diimplementasi.** State `isOrthophotoActive` dan `orthoOpacity` ada di `mapStore`, tetapi belum ada imagery layer orthophoto yang dibuat di `useLayers.js` (state tidak terpakai).
3. **`master-tileset.json` belum tersedia.** `load3DTiles()` saat ini selalu gagal secara graceful (`console.warn`) karena data 3D Tiles belum di-generate.
4. **`.gitignore` perlu diperbaiki.** Format saat ini (`./data-pipeline/`, `./node_modules/`) tidak dikenali Git dengan benar; prefix `./` harus dihapus. Selain itu, meng-ignore seluruh `data-pipeline/` juga akan menyembunyikan `scripts/` yang semestinya di-commit — hanya `raw/` dan `processed/` yang perlu di-ignore.
5. **Komponen PRD belum lengkap.** Direktori terencana yang belum ada: `components/simulation/`, `components/common/`, `composables/useObjectSelect.js`, `services/`, `stores/layerStore.js`.
6. **Keputusan backend tertunda.** Pilih Laravel atau FastAPI sebelum merancang skema PostGIS (Milestone 4).

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
