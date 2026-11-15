# STATUS PROYEK — Digital Twin Kota Bontang (`spectra`)

> **Terakhir diperbarui:** 2026-11-02
> **Fase:** Scale-Up Skala Kota — 15 kelurahan sudah berupa 3D Tiles, UI tiga area, fondasi registry simulasi.
> Dokumen ini adalah sumber kebenaran status implementasi. Perbarui setiap kali ada perubahan berarti.

---

## 1. Ringkasan Status per Modul

| Modul | Status | Keterangan |
|-------|:------:|------------|
| `frontend/` | 🟡 **Berjalan, render diuji headless** | Master tileset + ikhtisar kelurahan, UI tiga area (redesign), state atribut, penanganan error viewer, registry simulasi (kosong). Bangunan terlihat di screenshot Chromium headless (SwiftShader); klik/picking nyata & performa belum diuji di browser sungguhan. |
| `data-pipeline/` | 🟡 **Sebagian** | 15 kelurahan sudah jadi 3D Tiles v1.1 + `master-tileset.json`. Hanya `04_build_master.py` yang ada di repo; konversi `cjio`/`tyler` dilakukan di luar repo (belum reproducible). |
| `backend/` | ⚪ **Belum dimulai** | Framework (Laravel vs FastAPI) belum diputuskan. |
| Git | 🟡 **Lokal saja** | `master` (baseline `ae7ed67`) + branch kerja `feat/perbaikan-dan-redesign-ui`; belum ada remote. |
| Docker / Orkestrasi | 🔴 **Belum ada** | `docker-compose.yml` belum dibuat. |

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

### Data GeoJSON & layer vektor (2026-11-02, belum di-commit)
- QC & normalisasi `raw/geojson/` (batas kelurahan, batas RT, sungai): `scripts/check_geometry.py`, `normalize_names.py`, `reproject_sungai.py`, `show_data.py` (venv `data-pipeline/.venv`, `requirements.txt`). Laporan di `data-pipeline/reports/`, pemetaan nama di `config/kelurahan_map.csv`, output di `processed/geojson/`. Output deterministik (diuji 2× run, hash identik); hash `raw/` tidak berubah.
- Layer vektor di frontend (`composables/useVectorLayers.js`): batas kelurahan, batas RT (lazy, dimuat saat dinyalakan), sungai/drainase sebagai polyline clamp-to-ground (`classificationType: TERRAIN`). Salinan dev via `scripts/sync_geojson.py` → `frontend/public/geojson/` (di-ignore). Diuji di Chromium headless via DevTools Protocol (waktu nyata, klik toggle & navigasi): 3 request GeoJSON 200, RT hanya diminta setelah toggle, tanpa error konsol.

### Sumber data remote: Geoportal Kota Bontang (2026-11-02, belum di-commit)
- Adapter sumber seragam di `data-pipeline/scripts/sources/` (`base`, `geojson_lokal`, `wfs`, `csw`, `remote_http` read-only, `ogc_xml`), dikonfigurasi di `config/sources.yaml`, dijalankan oleh `scripts/fetch_sources.py`. Inventaris layanan oleh `scripts/inventory_remote.py` → `reports/remote_inventory.md`. Uji offline: `scripts/test_sources.py`.
- Geoportal anonim (tanpa autentikasi): WFS 2.0.0 dengan 23 FeatureType, CSW pycsw dengan 25 record ISO 19139. Kelurahan, RT, dan sungai di WFS **identik** dengan `raw/geojson/` (koordinat persis sama; hanya tipe `objectid` string vs angka). 20 FeatureType belum punya padanan lokal (banjir 2019–2026, rawan bencana, kecamatan, jalan, fasilitas kesehatan, dll.).
- GeoJSON lokal tetap jalur utama (prioritas 1); output adapter lokal identik dengan `processed/geojson/` lama. Output baru: `processed/sources/*.geojson`, `processed/catalog/records.json`; respons mentah di `raw/remote/<id>/<timestamp>/`. Deterministik (diuji 3× run).

### Layer geoportal dari website (2026-11-02, belum di-commit)
- `backend/` (FastAPI): `/api/sources/inspect` (WFS/CSW), `/api/layers` (tambah, daftar, ubah, refresh, hapus, data). Memakai ulang adapter `data-pipeline/scripts/sources/` (mode **generik** baru di `base.py`; tiga layer bawaan dan `fetch_sources.py` tidak berubah, hash output identik). Registry JSON + cache di `processed/user_layers/`. Allowlist host di `backend/config/allowed_hosts`. Batas 20.000 fitur / 50 MB; di atasnya hanya WMS. Tes: `backend/.venv/bin/pytest backend` (20 lulus).
- Frontend: panel "Data geoportal" (`GeoportalPanel.vue`, `RemoteLayerItem.vue`), `stores/remoteLayerStore.js`, `composables/useRemoteLayers.js`, proxy Vite `/api` → `127.0.0.1:8100`. Klik fitur → atribut di panel info. Diuji end-to-end di Chromium headless (CDP, waktu nyata): banjir 2024 tambah/tampil/klik/nonaktif/aktif/warna/refresh/reload/hapus, CSW → posyandu, layer besar → WMS, 3× tambah-hapus tanpa DataSource/ImageryLayer tertinggal, tanpa error konsol.
- **WMS belum bisa tampil**: GeoServer geoportal hanya mengizinkan CORS dari domainnya sendiri (request dengan `Origin` lain → 403). UI menampilkan pesan; perlu keputusan (CORS di GeoServer atau proxy GetMap lewat backend).

### Optimasi render (2026-11-15, belum di-commit)
- Penyebab GPU ±91% saat peta diam: `requestRenderMode` mati (render terus ±40 fps). Sekarang `requestRenderMode: true` + helper `requestRender()` (`useCesium.js`) dipanggil di semua perubahan visual (toggle layer, geoportal, highlight/penanda, simulasi, basemap, mode tampilan). Peta diam = 0 frame, GPU ±8% (idle sistem).
- "Mode tampilan" Hemat/Seimbang (bawaan)/Kualitas di panel kiri (`utils/displayModes.js`, `settingsStore.js`, `useRenderQuality.js`, `DisplaySettings.vue`); tersimpan di localStorage `spectra.displayMode`; GPU terintegrasi / renderer software mulai di Hemat + pemberitahuan. Uji URL: `?mode=`, `?rs=`.
- Mode debug `?debug=perf[,inspector]` (`usePerfDebug.js`): overlay FPS, `window.__spectraPerf()`.
- Bug lama diperbaiki: `cartesian is not defined` di picking (regresi commit 220b2a9; penanda titik tidak muncul); penanda kini hilang saat pilihan ditutup dari panel.
- `.glb` sudah memakai meshopt + kuantisasi dan tanpa tekstur: kompresi Draco/KTX2 tidak relevan.

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

---

## 3. Hutang Teknis & Isu Terbuka

| # | Isu | Prioritas | Lokasi |
|---|-----|:---------:|--------|
| 1 | **Tile tidak membawa atribut bangunan.** Seluruh 125 `.glb` hanya punya `EXT_mesh_features` (tanpa `EXT_structural_metadata`); CityJSON mentah yang diperiksa (Bontang Kuala, Api Api) juga tanpa `attributes`. Picking hanya bisa menampilkan kelurahan, tile, dan koordinat — bukan nama/tinggi/kategori. Butuh sumber atribut + penyertaannya di ETL (atau lookup via backend). | Tinggi | ETL / data |
| 2 | **Bangunan hilang bila kamera jauh.** Root tiap kelurahan (kecuali `bontang_lestari`) tidak punya konten; Cesium baru menelusurinya bila SSE root > batas. Perkiraan (asumsi layar 16:9, 1080 px): ambang ±2–7 km pada SSE 24 (median ±4 km; Guntung ±17 km); pada SSE 16 lebih jauh. Tombol "Seluruh Kota" menampilkan peta tanpa bangunan sampai pengguna mendekat. Perlu perilaku yang diinginkan + kemungkinan tile kasar di ETL. | Tinggi | ETL / `TILESET_OPTIONS` |
| 3 | Toggle per kelurahan tidak mungkin dengan satu master tileset (satu objek `Cesium3DTileset`). Bila dibutuhkan: muat per kelurahan (Opsi B). | Sedang | `use3DTiles.js` |
| 4 | Terrain DTM belum ada di proyek (toggle disembunyikan, UI "Segera hadir"). Butuh sumber quantized-mesh 1m. | Tinggi | data / `useLayers.js` |
| 5 | Orthophoto belum ada (UI "Segera hadir"; state lama dihapus dari `mapStore`). | Sedang | data / `useLayers.js` |
| 6 | Skrip ETL `01`–`03` (merge, clean, tyler) belum ada di repo; hasil konversi tidak reproducible dari repo. | Tinggi | `data-pipeline/scripts/` |
| 7 | `raw/3d/Kelurahan Loktuan/gabungan_kanaan.city.json` **salah nama**: isinya data Loktuan (extent = Loktuan Part I, 4.923 objek = jumlah fitur tile `loktuan`), bukan Kanaan. Tidak ada bangunan hilang: part II–IV Loktuan (dan part Belimbing/Bontang Lestari/Gunung Elai/Guntung) adalah subset ID part lain; gabungan = union ID. Belum dicek: bila part yang lebih baru (Loktuan II–IV, 14–15 Agu) adalah revisi geometri ID yang sama, versi mana yang dipakai saat merge. Data mentah tidak diubah. | Sedang | `data-pipeline/raw/` |
| 8 | `PRD.md` §4, §5.2, §7–§8 masih usang (§2 sudah diperbarui). | Rendah | `PRD.md` |
| 9 | `frontend/public/tiles/` (126 MB) ikut tersalin ke `dist/` saat `npm run build`; produksi seharusnya dari MinIO/storage. | Sedang | deploy |
| 10 | Backend, skema PostGIS, Docker belum ada. | Sedang | `backend/` |
| 11 | ID bangunan di tile tidak permanen (path tile + featureId), jadi lookup atribut backend belum andal. Butuh `gml_id` di `EXT_structural_metadata`. | Tinggi | ETL |
| 12 | Belum ada linter; test hanya helper murni (`npm test`). | Rendah | `frontend/` |
| 13 | GeoJSON batas & sungai dimuat utuh di browser (±2,9 MB) — pengecualian sementara AGENTS §3.2; pindah ke GeoServer WMS/WFS atau vector tiles saat backend ada. `public/geojson/` ikut ke `dist/`. | Sedang | `useVectorLayers.js` |
| 14 | Kotak ikhtisar kelurahan (bounding box) bertumpuk dengan batas kelurahan asli saat kamera jauh. Usulan: sembunyikan kotak bila layer batas kelurahan aktif (label tetap). | Rendah | `use3DTiles.js` |
| 15 | Keputusan data GeoJSON tertunda: tampil/tidaknya 29 RT pulau, ejaan & kategori "Drainase Dahllia", 2 grup RT duplikat Loktuan (003, 004), `luaswh` Guntung (−2,21%), 144 RT dengan atribut `luas` beda > 1%. Lihat `data-pipeline/reports/`. | Sedang | data |
| 16 | Prioritas sumber WFS vs GeoJSON lokal belum diputuskan (saat ini lokal = 1). Server WFS/CSW juga mengiklankan Transaction/Harvest; pipeline menolak operasi tulis di `remote_http.py`, tetapi pembatasan di sisi server di luar kendali repo. | Rendah | `config/sources.yaml` |
| 17 | Backend layer geoportal tanpa autentikasi: siapa pun yang bisa membuka spectra bisa menambah/menghapus layer. Registry JSON hanya aman untuk satu worker. WMS terblokir CORS GeoServer. | Sedang | `backend/` |

---

## 4. Roadmap / Milestone

- [x] **M0:** Scaffolding frontend + integrasi 3D Tiles.
- [ ] **M1:** Skrip ETL `cjio` (merge/clean) untuk CityJSON 15 kelurahan di dalam repo.
- [~] **M2:** 3D Tiles 15 kelurahan + `master-tileset.json` **ada**; skrip konversi `tyler` belum di repo.
- [ ] **M3:** Terrain 1m lokal + orthophoto XYZ di frontend; uji render & performa di browser.
- [ ] **M4:** Keputusan backend → PostGIS → GeoServer; sumber atribut bangunan (lihat #1).
- [ ] **M5:** Simulasi genangan banjir/rob — fondasi registry siap (`src/simulations/`, `docs/simulation-contract.md`); logika belum.

---

## 5. Cara Memperbarui Dokumen Ini
- Ubah status modul di tabel §1 saat ada perubahan.
- Pindahkan item dari §3 ke §2 setelah selesai **dan** terverifikasi (build/HTTP/test).
- Centang milestone §4 hanya jika ada bukti verifikasi, bukan asumsi.
