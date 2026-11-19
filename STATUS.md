# STATUS PROYEK — Digital Twin Kota Bontang (`spectra`)

> **Terakhir diperbarui:** 2026-11-20
> **Fase:** Scale-Up Skala Kota — 15 kelurahan berupa 3D Tiles (dari CityJSON lama, tidak lengkap), UI tiga area, backend FastAPI kecil, render hemat GPU. Arsitektur data bangunan baru (CityGML → PostGIS → 3D Tiles; ADR-001–006) **teruji pada satu kelurahan (Bontang Lestari, uji coba, ID belum resmi)**; 14 kelurahan lain dan frontend masih memakai tile lama.
> Dokumen ini adalah sumber kebenaran status implementasi. Perbarui setiap kali ada perubahan berarti.

---

## 1. Ringkasan Status per Modul

| Modul | Status | Keterangan |
|-------|:------:|------------|
| `frontend/` | 🟡 **Berjalan** | Master tileset + ikhtisar kelurahan, UI tiga area, layer batas/sungai, panel Data geoportal, `requestRenderMode` + Mode tampilan (Hemat/Seimbang/Kualitas), registry simulasi (kosong). 17 tes `npm test`. Tile belum membawa atribut; terrain/orthophoto belum ada. Diuji di Chromium headless (GPU AMD iGPU dan software); belum di GPU lain. |
| `data-pipeline/` | 🟡 **Sebagian** | 15 kelurahan berupa 3D Tiles v1.1 (125 `.glb`, 47.108 fitur) dari CityJSON lama dengan **±4.779 bangunan hilang** (lihat hutang #7). Ada skrip QC GeoJSON, adapter sumber data, dan `04_build_master.py`. **CityGML** (`raw/citygml/`, 51.888 bangunan) adalah sumber tunggal baru; inventaris selesai. **Pipeline baru sudah ada dan teruji pada Bontang Lestari** (uji coba, 2026-11-20; lihat §2) — belum dijalankan untuk 14 kelurahan lain dan belum dipakai frontend. Konversi lama (`cjio`/`tyler`) tidak reproducible dari repo. |
| `backend/` | 🟡 **FastAPI kecil** | Layer geoportal (inspect WFS/CSW, kelola layer), pencegahan SSRF, 20 tes pytest. **Belum ada** autentikasi, akses PostGIS, dan endpoint atribut bangunan (direncanakan, ADR-005). Dokumentasi: `docs/remote-layers.md`. |
| PostGIS / basis data | 🟡 **Dev (uji coba)** | Kontainer `spectra-postgis-dev` (port 55432, terpisah dari GeoNode), 3 migrasi, 2.219 bangunan Bontang Lestari. ID `BTG-BLD-xxxxxx` berstatus `uji_coba`: **bukan registri resmi**, boleh di-reset. Kontainer dimatikan setelah uji; volume `spectra_pgdata_dev` dipertahankan. Belum dipakai backend. |
| Git | 🟡 **Lokal saja** | `master` (baseline `ae7ed67`) + branch kerja `feat/perbaikan-dan-redesign-ui`; **belum ada remote** (tidak ada cadangan di luar mesin ini). Data besar di-ignore sehingga tidak ada salinan data di git. |
| Docker / Orkestrasi | 🟡 **Sebagian** | `data-pipeline/docker/compose.yml` + `db.sh` untuk PostGIS dev; tyler lewat `docker run` (`buat_tile.py`). Belum ada compose untuk aplikasi (frontend/backend). Image yang dipakai: `geonode/postgis:15-3.5-latest`, `3dgi/tyler:latest` (tyler 1.0.0-alpha1). |

Legenda: 🟢 selesai & terverifikasi · 🟡 sebagian · 🔴 belum ada · ⚪ belum dimulai

---

## 2. Yang Sudah Selesai

### Data Pipeline
- 3D Tiles v1.1 untuk **15 kelurahan** di `data-pipeline/processed/3dtiles/<slug>/` (125 file `.glb`, ±125 MB, 47.108 feature).
- `data-pipeline/scripts/04_build_master.py`: membaca seluruh kelurahan, memvalidasi (region + keberadaan tiap file konten), menggabungkan region (union), menulis `master-tileset.json` (15 anak, external tileset), dan `--sync` ke `frontend/public/tiles/` (inkremental, idempoten, tidak menyalin `tileset_unpruned.json`).

  ```bash
  python3 data-pipeline/scripts/04_build_master.py          # bangun master saja
  python3 data-pipeline/scripts/04_build_master.py --sync   # + salin ke frontend/public/tiles/
  ```

### Frontend
- `use3DTiles.js`: memuat `/tiles/master-tileset.json` via `Cesium3DTileset.fromUrl()`; state di `shallowRef`; opsi performa di konstanta `TILESET_OPTIONS`; picking `LEFT_CLICK` saja dengan satu `ScreenSpaceEventHandler` yang di-destroy; `unload3DTiles()` (handler, marker, watcher, listener, tileset) + HMR dispose; navigasi `zoomToKota()`, `flyToKelurahan(slug)`, `zoomToBontangKuala()`.
- `useCesium.js`: `destroyViewer()`. `CesiumCanvas.vue`: cleanup di `onBeforeUnmount`, basemap gagal tidak menahan pemuatan model.
- `LayerControl.vue`: tombol "Seluruh Kota" / "Bontang Kuala" + pesan error muat. `ObjectInfoPanel.vue`: kelurahan, tinggi aman, daftar properti.
- `utils/tileMeta.js`: helper murni (slug → nama, parse URL konten, pickFirst).

### Perbaikan & redesign (2026-11-02, branch `feat/perbaikan-dan-redesign-ui`)
- Toggle terrain palsu dihapus → "Segera hadir" (data DTM belum ada di proyek).
- `CesiumCanvas.vue`: status loading/ready/error + tombol "Coba lagi"; dispose: simulasi → tileset → viewer.
- Ikhtisar kelurahan (kotak region + label) untuk kamera jauh; `flyToKelurahan` membatasi jarak agar bangunan ikut dirender. Langkah perbaikan permanen: `TODO(ETL)` di `04_build_master.py`.
- Atribut bangunan: `objectStore.attributeStatus` + `services/buildingAttributes.js` (lookup backend via `VITE_API_BASE_URL`, belum ada backend).
- Cesium di-pin 1.146.0; PRD §2 diperbarui; sisa scaffolding & state orthophoto dihapus.
- UI: header (status data), panel kiri/kanan yang bisa dilipat, legenda yang bisa diperluas, format angka id-ID, token desain `bontang.*` (WCAG AA), atribusi data ArcGIS/OSM ditampilkan kembali.
- Simulasi: `src/simulations/` (kontrak + registry), `simulationStore`, `useSimulation`, `SimulationPanel.vue`; dokumentasi `docs/simulation-contract.md`.
- Uji: `npm test` (node --test) — 10 uji (format, tileMeta, kontrak simulasi). Siklus hidup `useSimulation` diuji sekali dengan loader Node sementara (tidak di repo).

### Data GeoJSON & layer vektor (2026-11-02, ter-commit)
- QC & normalisasi `raw/geojson/` (batas kelurahan, batas RT, sungai): `scripts/check_geometry.py`, `normalize_names.py`, `reproject_sungai.py`, `show_data.py` (venv `data-pipeline/.venv`, `requirements.txt`). Laporan di `data-pipeline/reports/`, pemetaan nama di `config/kelurahan_map.csv`, output di `processed/geojson/`. Output deterministik (diuji 2× run, hash identik); hash `raw/` tidak berubah.
- Layer vektor di frontend (`composables/useVectorLayers.js`): batas kelurahan, batas RT (lazy, dimuat saat dinyalakan), sungai/drainase sebagai polyline clamp-to-ground (`classificationType: TERRAIN`). Salinan dev via `scripts/sync_geojson.py` → `frontend/public/geojson/` (di-ignore). Diuji di Chromium headless via DevTools Protocol (waktu nyata, klik toggle & navigasi): 3 request GeoJSON 200, RT hanya diminta setelah toggle, tanpa error konsol.

### Sumber data remote: Geoportal Kota Bontang (2026-11-02, ter-commit)
- Adapter sumber seragam di `data-pipeline/scripts/sources/` (`base`, `geojson_lokal`, `wfs`, `csw`, `remote_http` read-only, `ogc_xml`), dikonfigurasi di `config/sources.yaml`, dijalankan oleh `scripts/fetch_sources.py`. Inventaris layanan oleh `scripts/inventory_remote.py` → `reports/remote_inventory.md`. Uji offline: `scripts/test_sources.py`.
- Geoportal anonim (tanpa autentikasi): WFS 2.0.0 dengan 23 FeatureType, CSW pycsw dengan 25 record ISO 19139. Kelurahan, RT, dan sungai di WFS **identik** dengan `raw/geojson/` (koordinat persis sama; hanya tipe `objectid` string vs angka). 20 FeatureType belum punya padanan lokal (banjir 2019–2026, rawan bencana, kecamatan, jalan, fasilitas kesehatan, dll.).
- GeoJSON lokal tetap jalur utama (prioritas 1); output adapter lokal identik dengan `processed/geojson/` lama. Output baru: `processed/sources/*.geojson`, `processed/catalog/records.json`; respons mentah di `raw/remote/<id>/<timestamp>/`. Deterministik (diuji 3× run).

### Layer geoportal dari website (2026-11-02, ter-commit)
- `backend/` (FastAPI): `/api/sources/inspect` (WFS/CSW), `/api/layers` (tambah, daftar, ubah, refresh, hapus, data). Memakai ulang adapter `data-pipeline/scripts/sources/` (mode **generik** baru di `base.py`; tiga layer bawaan dan `fetch_sources.py` tidak berubah, hash output identik). Registry JSON + cache di `processed/user_layers/`. Allowlist host di `backend/config/allowed_hosts`. Batas 20.000 fitur / 50 MB; di atasnya hanya WMS. Tes: `backend/.venv/bin/pytest backend` (20 lulus).
- Frontend: panel "Data geoportal" (`GeoportalPanel.vue`, `RemoteLayerItem.vue`), `stores/remoteLayerStore.js`, `composables/useRemoteLayers.js`, proxy Vite `/api` → `127.0.0.1:8100`. Klik fitur → atribut di panel info. Diuji end-to-end di Chromium headless (CDP, waktu nyata): banjir 2024 tambah/tampil/klik/nonaktif/aktif/warna/refresh/reload/hapus, CSW → posyandu, layer besar → WMS, 3× tambah-hapus tanpa DataSource/ImageryLayer tertinggal, tanpa error konsol.
- **WMS belum bisa tampil**: GeoServer geoportal hanya mengizinkan CORS dari domainnya sendiri (request dengan `Origin` lain → 403). UI menampilkan pesan; perlu keputusan (CORS di GeoServer atau proxy GetMap lewat backend).

### Optimasi render (2026-11-15, ter-commit)
- Penyebab GPU ±91% saat peta diam: `requestRenderMode` mati (render terus ±40 fps). Sekarang `requestRenderMode: true` + helper `requestRender()` (`useCesium.js`) dipanggil di semua perubahan visual (toggle layer, geoportal, highlight/penanda, simulasi, basemap, mode tampilan). Peta diam = 0 frame, GPU ±8% (idle sistem).
- "Mode tampilan" Hemat/Seimbang (bawaan)/Kualitas di panel kiri (`utils/displayModes.js`, `settingsStore.js`, `useRenderQuality.js`, `DisplaySettings.vue`); tersimpan di localStorage `spectra.displayMode`; GPU terintegrasi / renderer software mulai di Hemat + pemberitahuan. Uji URL: `?mode=`, `?rs=`.
- Mode debug `?debug=perf[,inspector]` (`usePerfDebug.js`): overlay FPS, `window.__spectraPerf()`.
- Bug lama diperbaiki: `cartesian is not defined` di picking (regresi commit 220b2a9; penanda titik tidak muncul); penanda kini hilang saat pilihan ditutup dari panel.
- `.glb` sudah memakai meshopt + kuantisasi dan tanpa tekstur: kompresi Draco/KTX2 tidak relevan.

### Audit dan inventaris CityGML (2026-11-19)
- Audit menyeluruh: `docs/audit/AUDIT-2026-11-19.md`. Inventaris CityGML: `data-pipeline/reports/citygml_inventory.md` (+ `.json`).
- `raw/citygml/`: 31 berkas `.gml` (3,5 GB; 30 CityGML 2.0, 1 CityGML 3.0), **51.888 bangunan** (51.887 unik berdasarkan posisi), 15 dari 15 kelurahan, semua XML valid. Hanya `measuredHeight` dan `storeysAboveGround` informatif (Berebas Tengah tanpa atribut). 99,86% poligon bersalinan terbalik; atap 76,4% miring.
- Koreksi: catatan lama "tidak ada bangunan hilang" (hutang #7) **keliru**; tile memuat 47.108 dari 51.888 bangunan.

### Keputusan arsitektur (2026-11-19) — direncanakan, belum diimplementasikan
- Diterima: ADR-001 (PostGIS sumber kebenaran), ADR-002 (bersihkan LOD2, bukan ekstrusi LOD1), ADR-003 (ID `BTG-BLD-xxxxxx` + registri), ADR-004 (CityGML sumber tunggal, CityJSON diarsipkan), ADR-005 (backend FastAPI), ADR-006 (tile statis, hasil simulasi sebagai data). Lihat `docs/adr/`.
- Pipeline baru (parser streaming → PostGIS → CityJSONSeq → tyler Docker → `processed/3dtiles_v2/` → `04_build_master.py --v2 … --sync`) sudah dijalankan **hanya untuk Bontang Lestari** (lihat bagian berikut). Tile yang dipakai frontend tetap `processed/3dtiles/` (cadangan setelah tile baru terverifikasi).

### Pipeline CityGML → PostGIS → 3D Tiles teruji pada Bontang Lestari (2026-11-20) — UJI COBA, ID belum resmi
Dokumentasi menjalankan: `data-pipeline/README.md`. Ringkasan uji: `data-pipeline/reports/uji_tampil_bontang_lestari/README.md`.
- **Impor:** 8 part = 2.219 bangunan (212+262+5+162+342+290+774+172), tidak ada yang hilang. 2.215 masuk tile; 4 dikeluarkan (tinggi < 0,1 m: `BTG-BLD-000182/000405/000457/002140`, tetap di PostGIS dengan `qc_flag`). `qc_flag`: `footprint_kurang_2m2` 28, `gml_id_bentrok` 6, `tinggi_lebih_40m` 6, `tinggi_kurang_0_1m` 4, `footprint_diperbaiki` 1, `tanpa_atap` 1. Tinggi hitung vs `measuredHeight` sumber: selisih maks 0,005 m.
- **Registri (uji coba):** impor pertama menerbitkan 2.219 ID; impor identik kedua 0 ID baru (2.213 cocok lewat `gml_id`, 6 lewat posisi), 0 tinjauan manual. Aturan footprint kosong (ADR-003: pusat bbox 3D ≤ 2 m, selisih tinggi ≤ 0,5 m) hanya teruji lewat uji unit.
- **Tile v2:** 4 `.glb` (total 1,90 MB, maks 0,75 MB), 2.215 fitur, 167.121 segitiga, `EXT_mesh_features` + `EXT_structural_metadata` dengan enam properti (`id`, `gml_id`, `nama`, `tinggi`, `jumlah_lantai`, `luas_tapak`); atribut di dalam GLB identik dengan PostGIS (0 selisih). Z dasar = 0, region cocok bbox UTM.
- **Validasi skema:** CityJSON 2.0.2 (skema lokal, `jsonschema`): 0 galat pada 2.215 fitur; 15 peringatan titik berulang berurutan (pembulatan 1 mm).
- **Temuan perbandingan segitiga:** tile lama Bontang Lestari (774 fitur) **bukan** hanya Part VII: cocok posisi dengan Part VII (430), I (212), II (50), V (80), ditambah 2 fitur bertinggi ≈ 0 m. Pada 772 pasangan cocok, segitiga tile lama 50.136 vs v2 24.917 = **2,01×**: pipeline lama **tidak membuang permukaan terbalik**.
- **Uji tampil (Chromium headless, WebGL SwiftShader, `?debug=perf`):** master hibrida (v2 untuk `bontang_lestari`, tile lama untuk 14 lainnya) dimuat; konsol 0 galat/peringatan; klik atap miring, atap datar, dan bangunan 49,1 m menampilkan keenam atribut di panel; atap miring dan dinding tampil utuh. Setelah uji `frontend/public/tiles/` dikembalikan (142 berkas, hash cocok baseline); `processed/3dtiles/` dan CityGML mentah utuh; tidak ada perubahan kode di `frontend/` dan `backend/`.
- **Warna:** tyler memperlakukan hex sebagai nilai linear, jadi `#D9DEE2` dirender ≈ sRGB (238,240,242), ~9% lebih terang dari legenda. Konfigurasi impor resmi memakai `#B1BAC2` (`config/citygml_sources.yaml`); tile uji coba belum dibuat ulang.
- **Batasan uji:** hanya satu kelurahan; hanya Chromium headless dengan SwiftShader (bukan GPU nyata, bukan uji performa/FPS); frontend belum memakai tile v2 secara permanen (master hibrida hanya di `processed/3dtiles_v2/`, tidak disinkron).

### Verifikasi (2026-10-12)
- `04_build_master.py`: 15 kelurahan, 125 konten, tidak ada file hilang; semua region anak berada di dalam region master; `--sync` kedua menyalin 0 file.
- HTTP dev server: 141 file (125 `.glb` + 16 tileset JSON) **identik byte-per-byte** dengan disk (magic bytes `glTF`/`{` cocok).
- Cesium 1.146.0 (Node): `Cesium3DTileset.fromUrl()` sukses untuk master dan ke-15 child; opsi terbaca (SSE 24, cache 512 MB, overflow 256 MB, skipLOD true).
- 14 skenario logika `use3DTiles.js` (viewer tiruan + Cesium/Pinia asli) lulus: picking dua jalur, highlight, toggle, race unload-vs-load, re-init, error. Listener ditambah 45 = dilepas 45. Uji mutasi (3 kerusakan sengaja) terdeteksi.
- `npm run build` sukses (34 modul).

### Belum terverifikasi (jangan diklaim berhasil)
- Klik/picking sungguhan, highlight, dan klik kotak ikhtisar → terbang ke kelurahan (hanya diuji logika, bukan interaksi browser).
- Render di GPU/browser nyata (screenshot hanya Chromium headless + SwiftShader). Di 1280×720, 1 dari 6 screenshot headless menampilkan langit (kamera tidak di posisi awal); penyebab belum dipastikan.
- **Performa/lag**: tidak ada pengukuran FPS atau memori GPU; pengaruh tuning belum terbukti.
- Tile v2 hanya diuji di Chromium headless dengan SwiftShader (≈1–3 FPS); perilaku di GPU nyata dan dengan 15 kelurahan v2 belum diuji.

---

## 3. Hutang Teknis & Isu Terbuka

| # | Isu | Prioritas | Lokasi |
|---|-----|:---------:|--------|
| 1 | **Tile tidak membawa atribut bangunan.** Seluruh 125 `.glb` hanya punya `EXT_mesh_features` (tanpa `EXT_structural_metadata`); CityJSON lama juga tanpa atribut. Picking hanya menampilkan kelurahan, tile, dan koordinat. **Tile v2 Bontang Lestari sudah membawa atribut** (teruji di Chromium headless); 14 kelurahan lain belum (ADR-004). | Tinggi | ETL / data |
| 2 | **Bangunan hilang bila kamera jauh.** Root tiap kelurahan (kecuali `bontang_lestari`) tidak punya konten; Cesium baru menelusurinya bila SSE root > batas. Perkiraan (asumsi layar 16:9, 1080 px): ambang ±2–7 km pada SSE 24 (median ±4 km; Guntung ±17 km); pada SSE 16 lebih jauh. Tombol "Seluruh Kota" menampilkan peta tanpa bangunan sampai pengguna mendekat. Perlu perilaku yang diinginkan + kemungkinan tile kasar di ETL. | Tinggi | ETL / `TILESET_OPTIONS` |
| 3 | Toggle per kelurahan tidak mungkin dengan satu master tileset (satu objek `Cesium3DTileset`). Bila dibutuhkan: muat per kelurahan (Opsi B). | Sedang | `use3DTiles.js` |
| 4 | Terrain DTM belum ada di proyek (toggle disembunyikan, UI "Segera hadir"). Butuh sumber quantized-mesh 1m. | Tinggi | data / `useLayers.js` |
| 5 | Orthophoto belum ada (UI "Segera hadir"; state lama dihapus dari `mapStore`). | Sedang | data / `useLayers.js` |
| 6 | Skrip ETL `01`–`03` lama (merge, clean, tyler) tidak ada di repo; hasil konversi tidak reproducible. Digantikan pipeline baru CityGML → PostGIS → tyler yang **direncanakan** (ADR-004). | Tinggi | `data-pipeline/scripts/` |
| 7 | **±4.779 bangunan hilang di tile** (CityGML 51.888 vs tile 47.108): Gunung Elai 1.897, Bontang Lestari 1.445, Belimbing 1.349, Loktuan 87. Penyebab: CityJSON digabung berdasarkan ID numerik yang ternyata nomor di `gml:description` (dimulai dari 1 di tiap part), sehingga bangunan antarpart saling menimpa. Catatan lama "tidak ada bangunan hilang" **keliru** (hanya ID yang dibandingkan, bukan posisi). Part Loktuan II–IV adalah 87 bangunan tambahan, bukan revisi. Nama berkas `raw/3d/Kelurahan Loktuan/gabungan_kanaan.city.json` juga salah (isinya Loktuan). Teratasi oleh pipeline baru: Bontang Lestari di tile v2 = 2.215 bangunan (vs 774 di tile lama; uji coba); 14 kelurahan lain menunggu impor. | Tinggi | `raw/3d/`, tile |
| 8 | `PRD.md` §4, §5.2, §7–§8 masih usang (§2 sudah diperbarui). | Rendah | `PRD.md` |
| 9 | `frontend/public/tiles/` (126 MB) ikut tersalin ke `dist/` saat `npm run build`; produksi seharusnya dari MinIO/storage. | Sedang | deploy |
| 10 | Backend FastAPI kecil sudah ada (layer geoportal); PostGIS dev dan migrasi ada (uji coba, belum dipakai backend); endpoint atribut bangunan, autentikasi, dan Docker untuk aplikasi belum ada. | Sedang | `backend/` |
| 11 | ID bangunan di tile tidak permanen (path tile + `featureId`), jadi lookup atribut backend belum andal. Diselesaikan registri ID `BTG-BLD-xxxxxx` (ADR-003; teruji sebagai uji coba pada Bontang Lestari, belum resmi); `gml:id` CityGML tidak dapat jadi kunci (lihat #19). | Tinggi | ETL |
| 12 | Belum ada linter. Tes: `npm test` (17), `pytest backend` (20), `test_sources.py`; belum ada tes otomatis untuk `use3DTiles.js` dan `useRemoteLayers.js`. | Rendah | `frontend/` |
| 13 | GeoJSON batas & sungai dimuat utuh di browser (±2,9 MB) — pengecualian sementara AGENTS §3.2; pindah ke GeoServer WMS/WFS atau vector tiles saat backend ada. `public/geojson/` ikut ke `dist/`. | Sedang | `useVectorLayers.js` |
| 14 | Kotak ikhtisar kelurahan (bounding box) bertumpuk dengan batas kelurahan asli saat kamera jauh. Usulan: sembunyikan kotak bila layer batas kelurahan aktif (label tetap). | Rendah | `use3DTiles.js` |
| 15 | Keputusan data GeoJSON tertunda: tampil/tidaknya 29 RT pulau, ejaan & kategori "Drainase Dahllia", 2 grup RT duplikat Loktuan (003, 004), `luaswh` Guntung (−2,21%), 144 RT dengan atribut `luas` beda > 1%. Lihat `data-pipeline/reports/`. | Sedang | data |
| 16 | Prioritas sumber WFS vs GeoJSON lokal belum diputuskan (saat ini lokal = 1). Server WFS/CSW juga mengiklankan Transaction/Harvest; pipeline menolak operasi tulis di `remote_http.py`, tetapi pembatasan di sisi server di luar kendali repo. | Rendah | `config/sources.yaml` |
| 17 | Backend layer geoportal tanpa autentikasi: siapa pun yang bisa membuka spectra bisa menambah/menghapus layer. Registry JSON hanya aman untuk satu worker. WMS terblokir CORS GeoServer. | Sedang | `backend/` |
| 18 | **Permukaan ganda di CityGML:** 99,86% poligon punya salinan terbalik (label `RoofSurface`/`GroundSurface` tertukar; 35.735 bangunan punya `RoofSurface` di dasar); sebagian berkas juga duplikat searah (0–14%). Dibersihkan di pipeline baru (ADR-002, direncanakan). | Sedang | `raw/citygml/` |
| 19 | **`gml:id` CityGML bentrok:** ±103 bangunan berbeda berbagi `gml:id` dalam satu berkas (17 berkas) dan 2 `gml:id` muncul di dua berkas (Loktuan Part I dengan Part II/III). Diselesaikan registri ID (ADR-003, direncanakan). | Tinggi | `raw/citygml/` |
| 20 | **Z dasar tidak konsisten di 5 berkas CityGML** (Satimpo, Belimbing Part III, Berebas Pantai, Kanaan, Guntung Part I; median −15,4 s.d. +5,4 m); 26 berkas lain berbasis 0,001 m. Asalnya tidak diketahui. Dinormalkan ke 0 untuk tile dan Z asli disimpan sebagai `z_dasar_sumber` (ADR-002, direncanakan); perlu konfirmasi sumber. | Tinggi | `raw/citygml/` |
| 21 | **Label EPSG:32748 di 3 berkas** (Guntung Part I, Guntung Part II, Satimpo) padahal koordinatnya EPSG:32650. Dikoreksi lewat konfigurasi eksplisit per berkas (ADR-004, direncanakan). | Sedang | `raw/citygml/` |
| 22 | **Berebas Tengah (CityGML 3.0) tanpa atribut:** tinggi diturunkan dari geometri, `jumlah_lantai` dikosongkan (ADR-004). Parser mendukung CityGML 2.0 dan 3.0 (diuji dengan sampel; lihat #25). | Sedang | `raw/citygml/` |
| 23 | **Validasi geometri belum ada.** Yang tervalidasi baru skema JSON CityJSON (0 galat); keabsahan geometri (permukaan tertutup/solid, titik berulang 15 cincin, `ST_IsValid` pada `PolyhedralSurface`, perpotongan sendiri) belum diperiksa. | Sedang | `scripts/citygml/validasi_cityjson.py` |
| 24 | **Aturan footprint kosong (ADR-003) belum teruji pada data nyata:** Bontang Lestari tidak punya bangunan tanpa footprint; hanya uji unit. | Sedang | `scripts/citygml/registri.py` |
| 25 | **Berebas Tengah (CityGML 3.0) belum diuji pada impor nyata** (parser hanya diuji dengan sampel di uji unit; tiga berkas EPSG:32748 juga belum diimpor). | Sedang | `config/citygml_sources.yaml` |
| 26 | **Python 3.14 menyulitkan paket:** `cjvalpy` tidak punya wheel Linux untuk Python 3.14 (validasi diganti `jsonschema` + skema lokal); paket binary lain bisa menyulitkan hal serupa. | Rendah | `data-pipeline/.venv` |
| 27 | **Warna tyler:** hex dianggap linear; tile uji coba memakai `#D9DEE2` (terlalu terang). Impor resmi harus memakai `#B1BAC2` (sudah di konfigurasi, belum dipakai membuat tile). | Rendah | `config/citygml_sources.yaml` |
| 28 | **Atribut berasal dari model GeoAI:** `tinggi`/`jumlah_lantai` tidak selalu bermakna (mis. `BTG-BLD-000700`: 49,1 m, 9 lantai, 18 m², kemungkinan cerobong). Perlu penyaringan sebelum dipakai statistik. | Sedang | `data-pipeline/README.md` |
| 29 | `db.sh dump`/`restore` (`pg_dump`) belum pernah dijalankan; baseline hash awal berkas mentah hilang (dibuat ulang 2026-11-20 di `reports/hash_baseline_*.txt`). | Rendah | `data-pipeline/docker/db.sh` |

---

## 4. Roadmap / Milestone

Selaras dengan `PRD.md` §8. M1–M3 sudah diuji pada **satu kelurahan (uji coba)** tetapi belum dicentang: belum untuk 15 kelurahan dan ID belum resmi.

- [x] **M0:** Scaffolding frontend + integrasi 3D Tiles.
- [ ] **M1 — Fondasi data:** PostGIS dev (Docker, terpisah dari GeoNode), migrasi skema, `pg_dump` (ADR-001). *PostGIS dev dan 3 migrasi sudah ada; `pg_dump` belum diuji.*
- [ ] **M2 — Impor CityGML:** parser streaming (2.0 dan 3.0) → `staging` → `core`; koreksi CRS per berkas; penyatuan semua part; pembersihan LOD2, normalisasi Z, `qc_flag`; registri ID (ADR-002/003/004). *Teruji pada Bontang Lestari (uji coba); belum 15 kelurahan, belum ID resmi.*
- [ ] **M3 — Tile v2:** CityJSONSeq → tyler (Docker) → `processed/3dtiles_v2/` + master; verifikasi picking dan atribut di viewer; tile lama tetap cadangan. *Teruji pada Bontang Lestari (Chromium headless); belum 15 kelurahan.*
- [ ] **M4 — Backend data bangunan:** PostGIS, `GET /buildings/{id}/attributes`, autentikasi, keputusan WMS (ADR-005). *Direncanakan.*
- [ ] **M5 — Terrain dan elevasi:** DTM 1 m, skema `elevasi`, orthophoto. *Direncanakan.*
- [ ] **M6 — Simulasi banjir/rob:** skema `sim`, endpoint hasil, styling per fitur (ADR-006); fondasi registry simulasi sudah ada (`docs/simulation-contract.md`). *Direncanakan.*

---

## 5. Cara Memperbarui Dokumen Ini
- Ubah status modul di tabel §1 saat ada perubahan.
- Pindahkan item dari §3 ke §2 setelah selesai **dan** terverifikasi (build/HTTP/test).
- Centang milestone §4 hanya jika ada bukti verifikasi, bukan asumsi.
