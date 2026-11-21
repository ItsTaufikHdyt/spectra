# STATUS PROYEK — Digital Twin Kota Bontang (`spectra`)

> **Terakhir diperbarui:** 2026-11-20 (impor resmi; redesign UI v2; Kondisi Terkini)
> **Fase:** Scale-Up Skala Kota — impor resmi seluruh CityGML selesai: **51.873 bangunan ber-ID resmi `BTG-BLD-xxxxxx`** di PostGIS dev, tile untuk 15 kelurahan (51.816 fitur dengan enam atribut) teruji di Chromium headless (SwiftShader dan GPU AMD). **Hanya ada satu jalur data bangunan: CityGML → PostGIS → 3D Tiles** (`processed/3dtiles/`); jalur lama CityJSON sudah diarsipkan di luar repo dan tile lamanya dihapus (2026-11-20). Belum dipakai: backend (atribut bangunan), terrain, simulasi.
> Dokumen ini adalah sumber kebenaran status implementasi. Perbarui setiap kali ada perubahan berarti.

---

## 1. Ringkasan Status per Modul

| Modul | Status | Keterangan |
|-------|:------:|------------|
| `frontend/` | 🟡 **Berjalan** | Master tileset + ikhtisar kelurahan, UI tiga area, layer batas/sungai, panel Data geoportal, `requestRenderMode` + Mode tampilan (Hemat/Seimbang/Kualitas), registry simulasi (kosong). 19 tes `npm test`. Tile v2 (di `public/tiles/` dev) membawa atribut dan teruji klik; atribut kosong (`noData`/kolom hilang) tidak tampil di panel (perbaikan `readFeatureProperties`, hutang #30 selesai); terrain/orthophoto belum ada. Diuji di Chromium headless (SwiftShader dan GPU AMD iGPU). |
| `data-pipeline/` | 🟢 **Impor resmi selesai (dev)** | CityGML (`raw/citygml/`, 31 berkas, 51.888 bangunan) → PostGIS → CityJSONSeq → tyler → `processed/3dtiles/` untuk **15 kelurahan** (139 `.glb`, 72,9 MB, 51.816 fitur; validasi skema CityJSON 0 galat). Registri resmi: `config/registri_id.csv` (+ `.sha256`, di-commit). Jalur lama CityJSON diarsipkan di luar repo; tile lamanya dihapus. Cara menjalankan: `data-pipeline/README.md`. Belum: validasi geometri (hutang #23), pembaruan inkremental/riwayat versi. |
| `backend/` | 🟡 **FastAPI kecil** | Layer geoportal (inspect WFS/CSW, kelola layer), pencegahan SSRF, **`/api/terkini/*` (gempa/cuaca BMKG, hotspot NASA FIRMS, laut Open-Meteo; cache TTL, stale)**, 33 tes pytest. **Belum ada** autentikasi, akses PostGIS, dan endpoint atribut bangunan (direncanakan, ADR-005). Dokumentasi: `docs/remote-layers.md`. |
| PostGIS / basis data | 🟡 **Dev (data resmi)** | Kontainer `spectra-postgis-dev` (port 55432, terpisah dari GeoNode), 5 migrasi, **51.873 bangunan dan 51.873 ID resmi** (batch 1, 2026-11-20), 51.888 baris staging (15 salinan dikecualikan, ADR-007). Cadangan `pg_dump` di `data-pipeline/backups/` (ter-ignore git; pemulihan teruji). Basis data dev bukan produksi: tanpa replikasi; belum dipakai backend. |
| Git | 🟡 **Lokal saja** | `main` (baseline `ae7ed67`) + branch kerja `feat/perbaikan-dan-redesign-ui`; **belum ada remote** (tidak ada cadangan di luar mesin ini). Data besar di-ignore sehingga tidak ada salinan data di git. |
| Docker / Orkestrasi | 🟡 **Sebagian** | `data-pipeline/docker/compose.yml` + `db.sh` untuk PostGIS dev; tyler lewat `docker run` (`buat_tile.py`). Belum ada compose untuk aplikasi (frontend/backend). Image: `geonode/postgis:15-3.5-latest`, `3dgi/tyler:latest` (tyler 1.0.0-alpha1). |

Legenda: 🟢 selesai & terverifikasi · 🟡 sebagian · 🔴 belum ada · ⚪ belum dimulai

---

## 2. Yang Sudah Selesai

### Data Pipeline
- 3D Tiles v1.1 untuk **15 kelurahan** di `data-pipeline/processed/3dtiles/<slug>/` (139 file `.glb`, 72,9 MB, 51.816 fitur), hasil pipeline CityGML (`buat_tile.py`); `frontend/public/tiles/` = salinan dev (156 berkas).
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
- Pipeline (parser streaming → staging → keputusan duplikat → ID resmi → CityJSONSeq → tyler Docker → `processed/3dtiles/` → `04_build_master.py --sync`) sudah dijalankan untuk **seluruh 15 kelurahan** (lihat bagian berikut). Ditambah ADR-007 (duplikat dalam batch dan `kelurahan_administratif`).

### Pipeline CityGML → PostGIS → 3D Tiles teruji pada Bontang Lestari (2026-11-20) — UJI COBA (riwayat; digantikan impor resmi)
Dokumentasi menjalankan: `data-pipeline/README.md`. Ringkasan uji: `data-pipeline/reports/uji_tampil_bontang_lestari/README.md`.
- **Impor:** 8 part = 2.219 bangunan (212+262+5+162+342+290+774+172), tidak ada yang hilang. 2.215 masuk tile; 4 dikeluarkan (tinggi < 0,1 m: `BTG-BLD-000182/000405/000457/002140`, tetap di PostGIS dengan `qc_flag`). `qc_flag`: `footprint_kurang_2m2` 28, `gml_id_bentrok` 6, `tinggi_lebih_40m` 6, `tinggi_kurang_0_1m` 4, `footprint_diperbaiki` 1, `tanpa_atap` 1. Tinggi hitung vs `measuredHeight` sumber: selisih maks 0,005 m.
- **Registri (uji coba):** impor pertama menerbitkan 2.219 ID; impor identik kedua 0 ID baru (2.213 cocok lewat `gml_id`, 6 lewat posisi), 0 tinjauan manual. Aturan footprint kosong (ADR-003: pusat bbox 3D ≤ 2 m, selisih tinggi ≤ 0,5 m) hanya teruji lewat uji unit.
- **Tile v2:** 4 `.glb` (total 1,90 MB, maks 0,75 MB), 2.215 fitur, 167.121 segitiga, `EXT_mesh_features` + `EXT_structural_metadata` dengan enam properti (`id`, `gml_id`, `nama`, `tinggi`, `jumlah_lantai`, `luas_tapak`); atribut di dalam GLB identik dengan PostGIS (0 selisih). Z dasar = 0, region cocok bbox UTM.
- **Validasi skema:** CityJSON 2.0.2 (skema lokal, `jsonschema`): 0 galat pada 2.215 fitur; 15 peringatan titik berulang berurutan (pembulatan 1 mm).
- **Temuan perbandingan segitiga:** tile lama Bontang Lestari (774 fitur) **bukan** hanya Part VII: cocok posisi dengan Part VII (430), I (212), II (50), V (80), ditambah 2 fitur bertinggi ≈ 0 m. Pada 772 pasangan cocok, segitiga tile lama 50.136 vs v2 24.917 = **2,01×**: pipeline lama **tidak membuang permukaan terbalik**.
- **Uji tampil (Chromium headless, WebGL SwiftShader, `?debug=perf`):** master hibrida (v2 untuk `bontang_lestari`, tile lama untuk 14 lainnya) dimuat; konsol 0 galat/peringatan; klik atap miring, atap datar, dan bangunan 49,1 m menampilkan keenam atribut di panel; atap miring dan dinding tampil utuh. Setelah uji `frontend/public/tiles/` dikembalikan (142 berkas, hash cocok baseline); `processed/3dtiles/` dan CityGML mentah utuh; tidak ada perubahan kode di `frontend/` dan `backend/`.
- **Warna:** tyler memperlakukan hex sebagai nilai linear, jadi `#D9DEE2` dirender ≈ sRGB (238,240,242), ~9% lebih terang dari legenda. Konfigurasi impor resmi memakai `#B1BAC2` (`config/citygml_sources.yaml`); tile uji coba belum dibuat ulang.
- **Batasan uji:** hanya satu kelurahan; hanya Chromium headless dengan SwiftShader (bukan GPU nyata, bukan uji performa/FPS); frontend belum memakai tile v2 secara permanen (master hibrida hanya di `processed/3dtiles_v2/`, tidak disinkron).

### Impor resmi seluruh CityGML (2026-11-20)
Rincian dan laporan: `data-pipeline/reports/impor_resmi_*.{json,md}`; cara menjalankan: `data-pipeline/README.md`; keputusan: ADR-007, `config/keputusan_duplikat.yaml`.
- **Parse:** 31 berkas → 51.888 bangunan di staging, **0 selisih** terhadap inventaris di semua berkas (282 detik). Kelima berkas ber-Z dasar tidak nol dinormalkan ke 0 (`z_dasar_sumber` tersimpan); tiga berkas EPSG:32748 dikoreksi ke 32650 (posisi di dalam kelurahan foldernya 99,94% / 94,44% / 99,96%; total 99,56%); Berebas Tengah (CityGML 3.0): `jumlah_lantai` NULL (bukan 0).
- **Duplikat dalam batch:** 17 kasus (inventaris hanya 1; 13 kasus antar kelurahan). Diputuskan (ADR-007): 15 salinan dikecualikan (tetap di staging dengan rujukan), 2 kasus `gml_id` bentrok dipertahankan keduanya; flag `atribut_dari_duplikat` (2) dan `duplikat_kepercayaan_rendah` (2).
- **ID resmi:** **51.873** (`BTG-BLD-000001` s.d. `BTG-BLD-051873`), urut slug sumber, `gml_id`, koordinat pusat. Registri diekspor ke `config/registri_id.csv` (SHA-256 di `.sha256`). **Impor kedua (hanya baca):** 51.873 cocok (51.667 lewat `gml_id`, 206 lewat posisi), 0 ID baru, 0 tinjauan manual, registri tidak berubah; 73 bangunan tanpa footprint dicocokkan (68 `gml_id`, 5 posisi bbox 3D).
- **`kelurahan_administratif`** (migrasi 0005): sama dengan sumber 51.660, beda 30, di luar batas 183.
- **Ekspor dan tile:** 15 CityJSONSeq (51.816 bangunan; 57 bertinggi < 0,1 m tidak masuk tile); validasi skema CityJSON 2.0.2 **0 galat**; tile v2 dengan warna `#B1BAC2`; semua `.glb` ≤ 1,33 MB; `EXT_structural_metadata` dengan enam properti; 51.816 ID unik dan identik dengan PostGIS, 0 atribut berbeda.
- **Segitiga:** v2 5,03 juta vs tile lama 9,34 juta; pada 46.911 bangunan yang cocok satu-ke-satu rasio **2,03×** (pipeline lama tidak membuang permukaan terbalik). Memori tileset pada pandangan yang sama: v2 18–26 MB vs lama 52–74 MB.
- **Nilai kosong di tile:** `jumlah_lantai`/`luas_tapak` kosong disimpan tyler sebagai `noData` (bukan 0); kolom dihilangkan dari tile yang tidak punya satu nilai pun. Sebelum perbaikan panel menampilkan `noData` sebagai `undefined`; sesudah perbaikan (lihat bawah) baris kosong tidak tampil.
- **Satu-satunya perubahan frontend dalam pekerjaan pipeline ini:** `readFeatureProperties` (dipindah ke `frontend/src/utils/tileMeta.js`, dipakai `use3DTiles.js`) melewati properti `undefined`/`null`. Alasan: tile v2 pertama kali membawa atribut dengan nilai kosong (`noData`), dan panel menampilkan teks `undefined` yang menyesatkan serta tidak konsisten antar tile. Diverifikasi: `npm test` 19 lulus, `npm run build` sukses, klik `BTG-BLD-014435` dan `BTG-BLD-000490` tidak lagi menampilkan barisnya.
- **Uji tampil (Chromium headless, GPU AMD Radeon Renoir via ANGLE dan SwiftShader):** 14 klik di 12 kategori (Satimpo, Berebas Tengah ×3, tanpa footprint, Gunung Elai, Guntung, Kanaan, 2 duplikat berkepercayaan rendah, 4 di luar batas) semuanya mengenai ID yang benar; konsol 0 galat. Hasil dan tangkapan layar: `data-pipeline/reports/uji_tampil_impor_resmi/README.md`. FPS/GPU (Seimbang, memutar kamera): lama 56,7 FPS/GPU 68,5% vs v2 58,1 FPS/65,3%; Hemat 30 FPS/20,1% vs 30 FPS/19,2%; kamera diam 0 frame, GPU 1%.
- **Pengaman:** `raw/citygml` (31 hash) tidak berubah; tidak ada perubahan di `frontend/` dan `backend/` selain perbaikan `readFeatureProperties` (di bawah).


### Pembersihan jalur data lama (2026-11-20)
Tujuan (ADR-004): satu jalur data bangunan, CityGML → PostGIS → 3D Tiles.
- **CityJSON lama (`raw/3d/`, 37 berkas, ±281 MB): diarsipkan oleh pemilik proyek di luar repo.** Folder itu sudah tidak ada di `data-pipeline/raw/` dan tidak ada di mesin pengembangan ini; **lokasi arsip sengaja tidak dicatat di repo** (disimpan di penyimpanan lain milik pemilik proyek; tidak ada manifest hash di repo). Jangan dipulihkan sebagai sumber.
- **Dihapus (disetujui pemilik, permanen):** `processed/3dtiles/` tile lama (126 MB, 156 berkas; **tidak dapat dibuat ulang**, skrip ETL lama tidak ada di repo), `processed/backup_public_tiles/` (126 MB), `processed/tyler_work/` (136 MB; dibuat ulang oleh `buat_tile.py`). Total 388 MB. Hash tile lama hanya tersisa sebagai riwayat di `reports/hash_baseline_3dtiles_lama.txt`.
- **Diganti nama:** `processed/3dtiles_v2/` → `processed/3dtiles/` (tile hasil pipeline CityGML, termasuk `master-tileset.json`).
- **Kode:** `04_build_master.py` disederhanakan (opsi `--v2` dan `--master-out` dihapus; `processed/3dtiles/` satu-satunya sumber; `--sync` tidak menyalin `tileset_unpruned.json`); `buat_tile.py` menulis ke `processed/3dtiles/`; `normalize_names.py` memakai fallback `raw/citygml/` (bukan `raw/3d/`); `uji_tampil.cjs` (uji Bontang Lestari yang bergantung pada tile lama) dihapus, digantikan `uji_impor_resmi.cjs` (mode `fps` kini hanya mengukur tile saat ini).
- **Verifikasi:** `frontend/public/tiles/` setelah `--sync` ulang identik dengan baseline `hash_baseline_public_tiles_v2.txt` (156 berkas, 0 disalin); uji klik 14/14 cocok di 9 kelurahan, konsol 0 galat (52 peringatan WebGL yang sama dengan hutang #31); `raw/citygml` 31 hash cocok sebelum dan sesudah. Dokumen bertanggal (`reports/`, `docs/audit/`, bagian riwayat di STATUS) dibiarkan.

### Verifikasi (2026-10-12) — riwayat (tile lama, sudah dihapus)
- `04_build_master.py`: 15 kelurahan, 125 konten, tidak ada file hilang; semua region anak berada di dalam region master; `--sync` kedua menyalin 0 file.
- HTTP dev server: 141 file (125 `.glb` + 16 tileset JSON) **identik byte-per-byte** dengan disk (magic bytes `glTF`/`{` cocok).
- Cesium 1.146.0 (Node): `Cesium3DTileset.fromUrl()` sukses untuk master dan ke-15 child; opsi terbaca (SSE 24, cache 512 MB, overflow 256 MB, skipLOD true).
- 14 skenario logika `use3DTiles.js` (viewer tiruan + Cesium/Pinia asli) lulus: picking dua jalur, highlight, toggle, race unload-vs-load, re-init, error. Listener ditambah 45 = dilepas 45. Uji mutasi (3 kerusakan sengaja) terdeteksi.
- `npm run build` sukses (34 modul).

### Belum terverifikasi (jangan diklaim berhasil)
- Klik kotak ikhtisar kelurahan → terbang ke kelurahan (hanya diuji logika, bukan interaksi browser). Klik bangunan dan sorotan fitur pada tile v2 sudah diuji di Chromium headless (SwiftShader dan GPU AMD).
- Render di browser dan GPU lain (hanya Chromium headless: SwiftShader dan AMD Radeon Renoir via ANGLE). Di 1280×720, 1 dari 6 screenshot headless lama menampilkan langit (kamera tidak di posisi awal); penyebab belum dipastikan.
- **Performa/lag**: diukur sekali (2026-11-20; GPU AMD iGPU, headless) pada satu pandangan (Loktuan, 700 m) — lihat bagian impor resmi. Angka 15 November (Seimbang memutar kamera ±80–82%) tidak direproduksi persis (pandangan dan prosedur berbeda; skrip lama tidak tersimpan). Belum ada pengukuran di perangkat pengguna.
- Tile v2 untuk 15 kelurahan belum diuji di browser non-Chromium atau di GPU selain AMD iGPU ini.

---

## 3. Hutang Teknis & Isu Terbuka

| # | Isu | Prioritas | Lokasi |
|---|-----|:---------:|--------|
| 1 | **Tile lama tidak membawa atribut bangunan.** **Selesai:** tile dari pipeline CityGML membawa enam atribut (teruji klik di Chromium headless); tile lama sudah dihapus (ADR-004). | Selesai | ETL / data |
| 2 | **Bangunan hilang bila kamera jauh.** Root tiap kelurahan (kecuali `bontang_lestari`) tidak punya konten; Cesium baru menelusurinya bila SSE root > batas. Perkiraan (asumsi layar 16:9, 1080 px): ambang ±2–7 km pada SSE 24 (median ±4 km; Guntung ±17 km); pada SSE 16 lebih jauh. Tombol "Seluruh Kota" menampilkan peta tanpa bangunan sampai pengguna mendekat. Perlu perilaku yang diinginkan + kemungkinan tile kasar di ETL. | Tinggi | ETL / `TILESET_OPTIONS` |
| 3 | Toggle per kelurahan tidak mungkin dengan satu master tileset (satu objek `Cesium3DTileset`). Bila dibutuhkan: muat per kelurahan (Opsi B). | Sedang | `use3DTiles.js` |
| 4 | Terrain DTM belum ada di proyek (toggle disembunyikan, UI "Segera hadir"). Butuh sumber quantized-mesh 1m. | Tinggi | data / `useLayers.js` |
| 5 | Orthophoto belum ada (UI "Segera hadir"; state lama dihapus dari `mapStore`). | Sedang | data / `useLayers.js` |
| 6 | Skrip ETL `01`–`03` lama (merge, clean, tyler) tidak ada di repo; hasil konversi tidak reproducible. **Selesai:** digantikan pipeline CityGML → PostGIS → tyler yang reproducible (ADR-004; `data-pipeline/README.md`); tile lama dan CityJSON lama dihapus/diarsipkan sehingga jalur lama tidak ada lagi. | Selesai | `data-pipeline/scripts/` |
| 7 | **±4.779 bangunan hilang di tile lama** (CityGML 51.888 vs 47.108; ID numerik CityJSON saling menimpa antarpart). **Selesai:** pipeline CityGML menghasilkan 51.816 fitur (51.873 ID − 57 bangunan < 0,1 m; ADR-004, impor resmi). Nama berkas lama `gabungan_kanaan.city.json` yang salah ikut diarsipkan. | Selesai | tile |
| 8 | `PRD.md` §4, §5.2, §7–§8 masih usang (§2 sudah diperbarui). | Rendah | `PRD.md` |
| 9 | `frontend/public/tiles/` (74 MB) ikut tersalin ke `dist/` saat `npm run build`; produksi seharusnya dari MinIO/storage. | Sedang | deploy |
| 10 | Backend FastAPI kecil sudah ada (layer geoportal); PostGIS dev (51.873 bangunan resmi) dan 5 migrasi ada, belum dipakai backend; endpoint atribut bangunan, autentikasi, dan Docker untuk aplikasi belum ada. | Sedang | `backend/` |
| 11 | ID bangunan di tile lama tidak permanen. **Selesai:** registri ID resmi `BTG-BLD-xxxxxx` (ADR-003) terbit 2026-11-20, ada di tile (`id`) dan `config/registri_id.csv`; lookup atribut backend belum dibuat. | Sedang | ETL / backend |
| 12 | Belum ada linter. Tes: `npm test` (19), `pytest backend` (20), `test_sources.py`; belum ada tes otomatis untuk `use3DTiles.js` dan `useRemoteLayers.js`. | Rendah | `frontend/` |
| 13 | GeoJSON batas & sungai dimuat utuh di browser (±2,9 MB) — pengecualian sementara AGENTS §3.2; pindah ke GeoServer WMS/WFS atau vector tiles saat backend ada. `public/geojson/` ikut ke `dist/`. | Sedang | `useVectorLayers.js` |
| 14 | Kotak ikhtisar kelurahan (bounding box) bertumpuk dengan batas kelurahan asli saat kamera jauh. Usulan: sembunyikan kotak bila layer batas kelurahan aktif (label tetap). | Rendah | `use3DTiles.js` |
| 15 | Keputusan data GeoJSON tertunda: tampil/tidaknya 29 RT pulau, ejaan & kategori "Drainase Dahllia", 2 grup RT duplikat Loktuan (003, 004), `luaswh` Guntung (−2,21%), 144 RT dengan atribut `luas` beda > 1%. Lihat `data-pipeline/reports/`. | Sedang | data |
| 16 | Prioritas sumber WFS vs GeoJSON lokal belum diputuskan (saat ini lokal = 1). Server WFS/CSW juga mengiklankan Transaction/Harvest; pipeline menolak operasi tulis di `remote_http.py`, tetapi pembatasan di sisi server di luar kendali repo. | Rendah | `config/sources.yaml` |
| 17 | Backend layer geoportal tanpa autentikasi: siapa pun yang bisa membuka spectra bisa menambah/menghapus layer. Registry JSON hanya aman untuk satu worker. WMS terblokir CORS GeoServer. | Sedang | `backend/` |
| 18 | **Permukaan ganda di CityGML:** 99,86% poligon punya salinan terbalik (label `RoofSurface`/`GroundSurface` tertukar; 35.735 bangunan punya `RoofSurface` di dasar); sebagian berkas juga duplikat searah (0–14%). Dibersihkan di pipeline baru (ADR-002, direncanakan). **Teratasi oleh impor resmi (2026-11-20).** | Sedang | `raw/citygml/` |
| 19 | **`gml:id` CityGML bentrok:** ±103 bangunan berbeda berbagi `gml:id` dalam satu berkas (17 berkas) dan 2 `gml:id` muncul di dua berkas (Loktuan Part I dengan Part II/III). Diselesaikan registri ID (ADR-003, direncanakan). **Teratasi oleh impor resmi (2026-11-20).** | Tinggi | `raw/citygml/` |
| 20 | **Z dasar tidak konsisten di 5 berkas CityGML** (Satimpo, Belimbing Part III, Berebas Pantai, Kanaan, Guntung Part I; median −15,4 s.d. +5,4 m); 26 berkas lain berbasis 0,001 m. Asalnya tidak diketahui. Dinormalkan ke 0 untuk tile dan Z asli disimpan sebagai `z_dasar_sumber` (ADR-002, direncanakan); perlu konfirmasi sumber. **Teratasi oleh impor resmi (2026-11-20).** | Tinggi | `raw/citygml/` |
| 21 | **Label EPSG:32748 di 3 berkas** (Guntung Part I, Guntung Part II, Satimpo) padahal koordinatnya EPSG:32650. Dikoreksi lewat konfigurasi eksplisit per berkas (ADR-004, direncanakan). **Teratasi oleh impor resmi (2026-11-20).** | Sedang | `raw/citygml/` |
| 22 | **Berebas Tengah (CityGML 3.0) tanpa atribut:** tinggi diturunkan dari geometri, `jumlah_lantai` dikosongkan (ADR-004). Parser mendukung CityGML 2.0 dan 3.0 (diuji dengan sampel; lihat #25). **Teratasi oleh impor resmi (2026-11-20).** | Sedang | `raw/citygml/` |
| 23 | **Validasi geometri belum ada.** Yang tervalidasi baru skema JSON CityJSON (0 galat); keabsahan geometri (permukaan tertutup/solid, titik berulang 15 cincin, `ST_IsValid` pada `PolyhedralSurface`, perpotongan sendiri) belum diperiksa. | Sedang | `scripts/citygml/validasi_cityjson.py` |
| 24 | **Aturan footprint kosong (ADR-003)**: teruji pada data nyata (73 bangunan tanpa footprint; impor kedua: 68 cocok lewat `gml_id`, 5 lewat bbox 3D + tinggi). Selesai. | Selesai | `scripts/citygml/registri.py` |
| 25 | **Berebas Tengah (CityGML 3.0) dan tiga berkas EPSG:32748**: diimpor resmi dan diverifikasi (lantai NULL, posisi 99,56%). Selesai. | Selesai | `config/citygml_sources.yaml` |
| 26 | **Python 3.14 menyulitkan paket:** `cjvalpy` tidak punya wheel Linux untuk Python 3.14 (validasi diganti `jsonschema` + skema lokal); paket binary lain bisa menyulitkan hal serupa. | Rendah | `data-pipeline/.venv` |
| 27 | **Warna tyler:** tile v2 impor resmi dibuat dengan `#B1BAC2` (`baseColorFactor` 0,69/0,73/0,76 linear = `#D9DEE2`). Kecocokan piksel dengan legenda belum diukur ulang. | Rendah | `config/citygml_sources.yaml` |
| 28 | **Atribut berasal dari model GeoAI:** `tinggi`/`jumlah_lantai` tidak selalu bermakna (mis. `BTG-BLD-000700`: 49,1 m, 9 lantai, 18 m², kemungkinan cerobong). Perlu penyaringan sebelum dipakai statistik. | Sedang | `data-pipeline/README.md` |
| 29 | `db.sh dump`/`restore` teruji (pemulihan ke database sementara: 51.873 registri, 51.873 bangunan, 51.888 staging). Baseline hash awal tugas uji coba hilang (dibuat ulang); baseline impor resmi di `reports/hash_baseline_*.txt`. | Selesai | `data-pipeline/docker/db.sh` |
| 30 | **Panel info menampilkan `undefined`** untuk atribut `noData`. **Selesai:** `readFeatureProperties` melewati `undefined`/`null` (satu-satunya perubahan frontend dalam pekerjaan pipeline ini; tes + build + klik ulang lulus). | Selesai | `use3DTiles.js`, `tileMeta.js` |
| 31 | **Peringatan WebGL `INVALID_VALUE: uniform3fv: no array`** (52×) muncul setelah klik/sorotan fitur di GPU AMD (radeonsi via ANGLE); muncul setelah tile punya metadata (jalur `Cesium3DTileFeature` dan sorotan `feature.color`); tidak muncul di SwiftShader maupun saat memuat/menggerakkan kamera. Asal belum dipastikan (Cesium atau driver); tidak ada dampak visual yang teramati. **Tidak diperbaiki sekarang.** | Rendah | `use3DTiles.js` |
| 32 | **Footprint mikro.** Aturan QC `footprint_mikro` (luas mentah < 0,01 m²) ditambahkan ke pipeline (`citygml/bangunan.py`) dan diterapkan ke data impor resmi lewat `impor_resmi.py qc-ulang`: **22 bangunan** berflag (18 masuk tile; mencakup 16 bangunan `luas_tapak` = 0,00, 2 ber-`luas_tapak` 0,01, dan 4 bertinggi < 0,1 m). Hanya `qc_flag`; ID, registri, geometri, dan tile tidak berubah. | Selesai | `core.bangunan` |
| 33 | **183 bangunan di luar semua batas kelurahan** (`kelurahan_administratif` NULL; 108 Loktuan, 23 Bontang Lestari, 20 Bontang Kuala, selebihnya lain-lain). Empat sampel tampak wajar (tepi permukiman, rumah panggung di atas air/tepi laut, koridor jalan area PLTU). | Rendah | `core.bangunan` |
| 34 | **Keputusan duplikat berkepercayaan rendah** (Gunung Elai Part III; Api Api `BTG-BLD-000046`): dapat ditinjau ulang; salinan yang dikecualikan masih ada di staging. Perubahan setelah ID terbit memakai mekanisme ADR-003. | Rendah | `config/keputusan_duplikat.yaml` |
| 35 | **tyler menghilangkan kolom properti** dari tile yang tidak punya satu nilai pun (mis. `jumlah_lantai` di 6 dari 7 tile Berebas Tengah) dan memakai `noData` bila tile punya sebagian nilai. Konsumen atribut (backend/frontend) harus menangani kolom hilang dan `noData`. | Rendah | tile v2 |
| 36 | `frontend/public/tiles/` adalah salinan dev dari `processed/3dtiles/` (ter-ignore git; hash di `reports/hash_baseline_public_tiles_v2.txt`). Cadangan tile lama dihapus bersama tile lama (2026-11-20). Hutang #9 tetap berlaku. | Selesai | `frontend/public/tiles/` |
| 37 | **Ketentuan pemakaian basemap Esri belum diverifikasi** (layanan Canvas Light/Dark Gray yang dipilih untuk tema terang/gelap **dan citra satelit World_Imagery yang sudah dipakai**) dan harus diperiksa sebelum dipakai publik; metadata Light Gray menyebut "mature support, no longer updated". Alternatif: CARTO Positron/Dark Matter dengan kunci API gratis dari `frontend/.env.local` (`VITE_CARTO_KEY`). Sumber basemap lewat konfigurasi `frontend/src/config/basemaps.js` (redesign UI v2, `docs/desain/spesifikasi-redesign.md` §6). | Sedang | `frontend/src/config/basemaps.js` |
| 38 | **Redesign UI v2 selesai (2026-11-20, branch `feat/redesign-ui-v2`):** tema terang/gelap/sistem, basemap per tema, tata letak baru (header, panel kartu, peta bersudut, rail, legenda). Bukti: `frontend/tests/browser/` (`npm run test:browser`, 16 + 52 uji), `ukur_performa.cjs` (Seimbang memutar 57,5 fps / GPU 72% vs sebelum 58,0 / 67,3% pada kanvas 26% lebih besar; Hemat 30 fps / 21,8% vs 29,9 / 20,8%; diam 0 fps), screenshot `docs/desain/tahap3/`, `tahap4/`. **Batasan tersisa:** kontras persentil ke-10 bangunan tema gelap di kawasan padat ±1,3 (sisi bangunan di bayangan di atas basemap gelap; pencahayaan tidak memperbaikinya, §16 spesifikasi); mode 2D sungguhan tidak ada (toggle "Atas" hanya pitch kamera); uji manual tema gelap di layar sentuh belum dilakukan; ketentuan Esri (#37). | Rendah | `docs/desain/spesifikasi-redesign.md` §14–§16 |
| 39 | **Kondisi Terkini (gempa/cuaca/hotspot/laut) memakai sumber luar yang izinnya belum dipastikan:** (a) **izin integrasi data BMKG** (gempa, prakiraan cuaca) untuk aplikasi pihak ketiga/instansi belum dikonfirmasi (atribusi BMKG sudah ditampilkan; endpoint prakiraan cuaca dibatasi ±60 permintaan/menit/IP, aman dengan cache); (b) **Open-Meteo Marine (CC BY 4.0) gratis hanya untuk non-komersial**, kepastian untuk instansi pemerintah belum ada; (c) kunci **NASA FIRMS** (5.000 transaksi/10 menit) ada di `backend/.env`, dan titik panas bukan kebakaran terkonfirmasi. **Batasan data:** titik laut Open-Meteo adalah sel model ±9 km yang jatuh ±13 km lepas pantai Bontang (bukan perairan dangkal di pantai); daftar gempa M5,0+ BMKG berskala nasional; cache di memori satu worker (hilang saat backend restart). Aturan: `/api/terkini/*`, TTL gempa 2 mnt, cuaca 60 mnt, hotspot 30 mnt, laut 60 mnt, semua waktu WITA. | Sedang | `backend/app/terkini.py`, `backend/config/wilayah_bontang.yaml` |

---

## 4. Roadmap / Milestone

Selaras dengan `PRD.md` §8. M1–M3 selesai dan terverifikasi untuk seluruh 15 kelurahan (impor resmi 2026-11-20).

- [x] **M0:** Scaffolding frontend + integrasi 3D Tiles.
- [x] **M1 — Fondasi data:** PostGIS dev (Docker, terpisah dari GeoNode), migrasi skema, `pg_dump` (ADR-001). *Selesai: 5 migrasi; `pg_dump` dan pemulihan teruji.*
- [x] **M2 — Impor CityGML:** parser streaming (2.0 dan 3.0) → `staging` → `core`; koreksi CRS per berkas; penyatuan semua part; pembersihan LOD2, normalisasi Z, `qc_flag`; registri ID (ADR-002/003/004/007). *Selesai: 51.888 bangunan dibaca, 51.873 ID resmi, impor kedua stabil (0 ID baru).*
- [x] **M3 — Tile:** CityJSONSeq → tyler (Docker) → `processed/3dtiles/` + master; verifikasi picking dan atribut di viewer. *Selesai untuk 15 kelurahan (Chromium headless, SwiftShader dan GPU AMD); jalur lama dihapus.*
- [ ] **M4 — Backend data bangunan:** PostGIS, `GET /buildings/{id}/attributes`, autentikasi, keputusan WMS (ADR-005). *Direncanakan.*
- [ ] **M5 — Terrain dan elevasi:** DTM 1 m, skema `elevasi`, orthophoto. *Direncanakan.*
- [ ] **M6 — Simulasi banjir/rob:** skema `sim`, endpoint hasil, styling per fitur (ADR-006); fondasi registry simulasi sudah ada (`docs/simulation-contract.md`). *Direncanakan.*

---

## 5. Cara Memperbarui Dokumen Ini
- Ubah status modul di tabel §1 saat ada perubahan.
- Pindahkan item dari §3 ke §2 setelah selesai **dan** terverifikasi (build/HTTP/test).
- Centang milestone §4 hanya jika ada bukti verifikasi, bukan asumsi.
