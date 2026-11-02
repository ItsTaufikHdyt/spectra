# STATUS PROYEK — Digital Twin Kota Bontang (`spectra`)

> **Terakhir diperbarui:** 2026-10-12
> **Fase:** Scale-Up Skala Kota — 15 kelurahan sudah berupa 3D Tiles, frontend memuat satu master tileset.
> Dokumen ini adalah sumber kebenaran status implementasi. Perbarui setiap kali ada perubahan berarti.

---

## 1. Ringkasan Status per Modul

| Modul | Status | Keterangan |
|-------|:------:|------------|
| `frontend/` | 🟡 **Berjalan, render belum diuji** | Loader master tileset + tuning performa + picking aman. Render WebGL & klik nyata belum diverifikasi di browser. |
| `data-pipeline/` | 🟡 **Sebagian** | 15 kelurahan sudah jadi 3D Tiles v1.1 + `master-tileset.json`. Hanya `04_build_master.py` yang ada di repo; konversi `cjio`/`tyler` dilakukan di luar repo (belum reproducible). |
| `backend/` | ⚪ **Belum dimulai** | Framework (Laravel vs FastAPI) belum diputuskan. |
| Git | 🟡 **Lokal saja** | 1 commit (`e71f008`), branch `master`, belum ada remote. |
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

### Verifikasi (2026-10-12)
- `04_build_master.py`: 15 kelurahan, 125 konten, tidak ada file hilang; semua region anak berada di dalam region master; `--sync` kedua menyalin 0 file.
- HTTP dev server: 141 file (125 `.glb` + 16 tileset JSON) **identik byte-per-byte** dengan disk (magic bytes `glTF`/`{` cocok).
- Cesium 1.146.0 (Node): `Cesium3DTileset.fromUrl()` sukses untuk master dan ke-15 child; opsi terbaca (SSE 24, cache 512 MB, overflow 256 MB, skipLOD true).
- 14 skenario logika `use3DTiles.js` (viewer tiruan + Cesium/Pinia asli) lulus: picking dua jalur, highlight, toggle, race unload-vs-load, re-init, error. Listener ditambah 45 = dilepas 45. Uji mutasi (3 kerusakan sengaja) terdeteksi.
- `npm run build` sukses (34 modul).

### Belum terverifikasi (jangan diklaim berhasil)
- Render WebGL bangunan di browser, tampilan `skipLevelOfDetail: true`, dan klik/picking sungguhan.
- **Performa/lag**: tidak ada pengukuran FPS atau memori GPU; pengaruh tuning belum terbukti.

---

## 3. Hutang Teknis & Isu Terbuka

| # | Isu | Prioritas | Lokasi |
|---|-----|:---------:|--------|
| 1 | **Tile tidak membawa atribut bangunan.** Seluruh 125 `.glb` hanya punya `EXT_mesh_features` (tanpa `EXT_structural_metadata`); CityJSON mentah yang diperiksa (Bontang Kuala, Api Api) juga tanpa `attributes`. Picking hanya bisa menampilkan kelurahan, tile, dan koordinat — bukan nama/tinggi/kategori. Butuh sumber atribut + penyertaannya di ETL (atau lookup via backend). | Tinggi | ETL / data |
| 2 | **Bangunan hilang bila kamera jauh.** Root tiap kelurahan (kecuali `bontang_lestari`) tidak punya konten; Cesium baru menelusurinya bila SSE root > batas. Perkiraan (asumsi layar 16:9, 1080 px): ambang ±2–7 km pada SSE 24 (median ±4 km; Guntung ±17 km); pada SSE 16 lebih jauh. Tombol "Seluruh Kota" menampilkan peta tanpa bangunan sampai pengguna mendekat. Perlu perilaku yang diinginkan + kemungkinan tile kasar di ETL. | Tinggi | ETL / `TILESET_OPTIONS` |
| 3 | Toggle per kelurahan tidak mungkin dengan satu master tileset (satu objek `Cesium3DTileset`). Bila dibutuhkan: muat per kelurahan (Opsi B). | Sedang | `use3DTiles.js` |
| 4 | Terrain belum tersambung — kedua cabang toggle `EllipsoidTerrainProvider()`. | Tinggi | `useLayers.js` |
| 5 | Orthophoto & `orthoOpacity` belum di-wire. | Sedang | `useLayers.js`, `mapStore.js` |
| 6 | Skrip ETL `01`–`03` (merge, clean, tyler) belum ada di repo; hasil konversi tidak reproducible dari repo. | Tinggi | `data-pipeline/scripts/` |
| 7 | `package.json` menyebut Cesium `^1.119.0`, terpasang 1.146.0 — pin versi. | Sedang | `frontend/package.json` |
| 8 | `PRD.md` §2 usang (menyebut git belum ada, 1 kelurahan, master belum ada). | Sedang | `PRD.md` |
| 9 | `frontend/public/tiles/` (126 MB) ikut tersalin ke `dist/` saat `npm run build`; produksi seharusnya dari MinIO/storage. | Sedang | deploy |
| 10 | Backend, skema PostGIS, Docker belum ada. | Sedang | `backend/` |
| 11 | Komponen terencana belum dibuat: `services/`, `stores/layerStore.js`, `components/common/`, `components/simulation/`. | Rendah | `frontend/src/` |

---

## 4. Roadmap / Milestone

- [x] **M0:** Scaffolding frontend + integrasi 3D Tiles.
- [ ] **M1:** Skrip ETL `cjio` (merge/clean) untuk CityJSON 15 kelurahan di dalam repo.
- [~] **M2:** 3D Tiles 15 kelurahan + `master-tileset.json` **ada**; skrip konversi `tyler` belum di repo.
- [ ] **M3:** Terrain 1m lokal + orthophoto XYZ di frontend; uji render & performa di browser.
- [ ] **M4:** Keputusan backend → PostGIS → GeoServer; sumber atribut bangunan (lihat #1).
- [ ] **M5:** Simulasi genangan banjir/rob (`components/simulation/`).

---

## 5. Cara Memperbarui Dokumen Ini
- Ubah status modul di tabel §1 saat ada perubahan.
- Pindahkan item dari §3 ke §2 setelah selesai **dan** terverifikasi (build/HTTP/test).
- Centang milestone §4 hanya jika ada bukti verifikasi, bukan asumsi.
