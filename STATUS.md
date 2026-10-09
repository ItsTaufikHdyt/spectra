# STATUS PROYEK — Digital Twin Kota Bontang (`spectra`)

> **Terakhir diperbarui:** 2026-10-09
> **Fase:** Transisi POC → Scale-Up Skala Kota (15 Kelurahan)
> Dokumen ini adalah sumber kebenaran status implementasi. Perbarui setiap kali ada perubahan berarti.

---

## 1. Ringkasan Status per Modul

| Modul | Status | Keterangan |
|-------|:------:|------------|
| `frontend/` | 🟢 **Berjalan** | Viewer, basemap, panel UI, 3D Tiles Bontang Kuala, picking + highlight. |
| `data-pipeline/` | 🟡 **Sebagian** | 1 kelurahan sudah dikonversi ke 3D Tiles v1.1 (Bontang Kuala). Skrip ETL belum ditulis. |
| `backend/` | ⚪ **Belum dimulai** | Framework (Laravel vs FastAPI) belum diputuskan. |
| Git / Versioning | 🔴 **Belum ada** | Direktori belum menjadi git repository. |
| Docker / Orkestrasi | 🔴 **Belum ada** | `docker-compose.yml` belum dibuat. |

Legenda: 🟢 selesai & terverifikasi · 🟡 sebagian · 🔴 belum ada · ⚪ belum dimulai

---

## 2. Yang Sudah Selesai

### Frontend
- Scaffolding Vue 3 + Vite + Pinia + Tailwind + CesiumJS.
- `useCesium.js` — inisialisasi Viewer di `shallowRef()`; kamera default ke pusat Bontang Kuala (Lng 117.5169, Lat 0.1415, Alt 1500 m, pitch -45°).
- `useLayers.js` — basemap ArcGIS Imagery & OpenStreetMap dengan switcher.
- `use3DTiles.js` — memuat 3D Tiles v1.1 Bontang Kuala dari `/tiles/bontang_kuala/tileset.json`, `zoomToBontangKuala()`, feature picking (`LEFT_CLICK`) + highlight kuning, `applyHeightOffset()`, watcher visibilitas.
- Panel UI: `LayerControl.vue` (basemap switcher, toggle terrain & 3D Tiles, tombol fokus) dan `ObjectInfoPanel.vue` (atribut objek terpilih).
- Pinia stores: `mapStore` (status layer/kamera), `objectStore` (objek terpilih).

### Data Pipeline
- Konversi CityJSON LOD2 Kelurahan Bontang Kuala → OGC 3D Tiles v1.1 (`tileset.json` + 3 file `.glb`), tersimpan di `data-pipeline/processed/3dtiles/bontang_kuala/` dan disalin ke `frontend/public/tiles/bontang_kuala/`.

### Verifikasi Terakhir (2026-10-09)
- `npm run build` sukses tanpa error (33 modul).
- Akses HTTP dev server: `tileset.json` → 200; tiga `.glb` → 200 (2.1 MB / 1.9 MB / 1.3 MB).

---

## 3. Hutang Teknis & Isu Terbuka (Known Gaps)

| # | Isu | Prioritas | Lokasi |
|---|-----|:---------:|--------|
| 1 | Terrain belum tersambung — kedua cabang toggle masih `EllipsoidTerrainProvider()`. | Tinggi | `useLayers.js` |
| 2 | Orthophoto & `orthoOpacity` belum di-wire ke imagery layer. | Sedang | `useLayers.js`, `mapStore.js` |
| 3 | `master-tileset.json` multi-kelurahan belum dibuat (baru single tileset). | Tinggi | `data-pipeline/`, `use3DTiles.js` |
| 4 | Skrip ETL (`01`–`04`) belum ditulis. | Tinggi | `data-pipeline/scripts/` |
| 5 | Versi Cesium terpasang 1.146.0, tapi `package.json` menyebut `^1.119.0`. Opsi `maximumMemoryUsage` sudah usang (ganti `cacheBytes`). | Sedang | `frontend/package.json`, `use3DTiles.js` |
| 6 | `.gitignore` memakai prefix `./` yang tidak dikenali Git; meng-ignore seluruh `data-pipeline/`. | Sedang | `.gitignore` |
| 7 | Git belum diinisialisasi. | Tinggi | root |
| 8 | Data 14 kelurahan lain belum tersedia. | Blocker eksternal | `data-pipeline/raw/` |
| 9 | Backend & skema PostGIS belum ada. | Sedang | `backend/` |
| 10 | Komponen terencana belum dibuat: `services/`, `stores/layerStore.js`, `components/common/`, `components/simulation/`, `composables/useObjectSelect.js`. | Rendah | `frontend/src/` |

---

## 4. Roadmap / Milestone

- [x] **M0:** Scaffolding frontend + integrasi 3D Tiles single kelurahan (Bontang Kuala).
- [ ] **M1:** Tulis skrip ETL (`cjio` merge/clean) untuk CityJSON 15 kelurahan.
- [ ] **M2:** Konversi seluruh kelurahan ke 3D Tiles v1.1 (`3dgi/tyler`) + bentuk `master-tileset.json`.
- [ ] **M3:** Integrasi terrain 1m lokal (quantized-mesh) + orthophoto XYZ tiles di frontend.
- [ ] **M4:** Keputusan backend → skema PostGIS → GeoServer (batas kelurahan/jalan/drainase).
- [ ] **M5:** Skenario simulasi genangan banjir/rob (`components/simulation/`).

---

## 5. Cara Memperbarui Dokumen Ini
- Ubah status modul di tabel §1 saat ada perubahan.
- Pindahkan item dari §3 ke §2 setelah selesai **dan** terverifikasi (build/HTTP/test).
- Centang milestone §4 hanya jika ada bukti verifikasi, bukan asumsi.
