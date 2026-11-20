# Spesifikasi redesign UI spectra (v2) — mode terang dan gelap

> **Status: DISETUJUI dengan perubahan (2026-11-20).** Keputusan pemilik proyek ada di §13 dan sudah dimasukkan ke seluruh dokumen ini. Branch kerja: `feat/redesign-ui-v2` (dari `main`).
> Referensi: `docs/desain/referensi/DT1.png` (tiga kolom, panel kanan tertutup) dan `DT2.png` (panel kanan terbuka). Mockup: `docs/desain/mockup/` (`mockup-terang.html`, `mockup-gelap.html`, dan PNG-nya).
> Hanya **gaya dan tata letak** referensi yang dipakai. Tidak ada logo, nama, atau aset visual referensi; identitas tetap spectra / Kota Bontang. Tidak ada data palsu.

## 1. Analisis referensi

Ukuran di bawah adalah **perkiraan dari gambar** (diasumsikan @2×; px CSS ≈ px gambar tampil × 0,62).

**Tata letak (DT1, ±1240 px lebar).** Latar halaman abu kebiruan sangat terang; semua elemen berupa kartu putih mengambang.
- **Header** tanpa garis dasar, tinggi ±70 px: logo di kiri; pil navigasi putih di tengah (±320 × 42 px, tiga item, item aktif berwarna aksen); pil pencarian di kanan (±150 px); dua tombol ikon (bahasa, tema) tanpa bingkai.
- **Tiga kolom:** kolom kiri ±288 px (kartu bertumpuk, bisa digulir di bawah header), **peta di tengah ±830 px** dengan sudut membulat, rail ikon kanan ±55 px. Jarak antarkolom dan antarkartu ±16 px; margin tepi ±15 px.
- **DT2:** panel kanan terbuka (±314 px) berisi kartu bertumpuk; peta menyempit jadi ±570 px dan kontrol di sisinya ikut bergeser; rail kanan tersembunyi.
- **Peta:** radius ±22–24 px. Kiri atas: toggle segmen **2D | 3D** (pil putih, segmen aktif terisi aksen). Kanan atas: **pil vertikal** kontrol (zoom +/−, kompas, penggaris, lokasi) berbayang halus. Kiri bawah: pil putih "Tren lingkungan" yang bisa dilipat. Kanan bawah: pil **skala + koordinat**. Kanan bawah di atasnya: dua tombol bulat (street view, asisten).
- **Rail kanan:** pil putih vertikal berisi tombol ikon (tutup/buka panel, lalu ikon kategori) dengan garis pemisah tipis setelah tombol pertama.

**Kartu.** Putih, **radius ±20 px**, padding ±16–17 px, **tanpa garis tepi**, bayangan sangat lembut (±`0 1px 2px` + `0 4px 16px`, opasitas ±6%). Judul kartu ±16 px semibold di kiri, tombol info bulat kecil (ikon "i" berlatar aksen muda) dan tombol lipat (chevron) di kanan.

**Komponen berulang.**
- **Toggle segmen:** tiga opsi sejajar (Terang / Ortho / Gelap), teks tanpa latar; opsi aktif berwarna aksen dengan garis bawah tebal pendek.
- **Chip:** pil penuh, tinggi ±20–24 px, teks ±12 px. Dua keadaan: aktif (isi aksen penuh, teks putih) dan tidak aktif (isi aksen sangat muda, teks aksen). Chip kategori bertinta pastel (jingga, ungu, teal) dengan ikon dan angka kecil; chip nonaktif memudar (±45% opasitas).
- **Switch:** trek pil berwarna aksen saat aktif, kenop putih.
- **Tombol ikon:** bulat, putih, bayangan lembut; ikon garis 1,5–1,75 px berujung membulat.
- **Panel yang bisa dilipat:** judul + chevron; isi dikunci tingginya saat tertutup.
- **Kartu data (DT2):** judul, subjudul abu, angka besar (±36 px), chip status kecil di kanan atas, grafik garis tipis.

**Tipografi.** Sans geometris humanis (mirip Plus Jakarta Sans/Inter). Judul kartu ±16 px semibold; isi ±12–13 px; angka besar ±36 px bobot 600; label kecil ±11 px. Hierarki dibuat dari bobot dan ukuran, bukan huruf kapital.

**Warna (perkiraan).** Latar halaman ≈ `#F3F5FA`; kartu `#FFFFFF`; aksen biru ≈ `#1F6FE5`; chip muda ≈ `#DCE8FB`; teks utama ≈ `#1B2330`; teks sekunder abu kebiruan; peta dasar terang dengan bangunan putih/abu dan tekstur foto.

## 2. Inventaris UI spectra saat ini

| Area | Berkas | Isi |
|---|---|---|
| Shell | `App.vue` | Grid `header + (panel kiri 296 px / peta / panel kanan 320 px)`; `xl` (1280 px) = panel ikut alur, di bawahnya overlay satu per satu; panel kanan otomatis terbuka saat objek dipilih |
| Header | `layout/AppHeader.vue` | Tombol panel kiri/kanan, judul "Digital Twin Bontang", status model (memuat/siap/galat), catatan "Terrain dan atribut bangunan belum tersedia" |
| Panel kiri | `panels/LayerControl.vue` | Peta dasar (Citra satelit ArcGIS / OpenStreetMap), `DisplaySettings` (Hemat/Seimbang/Kualitas + pemberitahuan otomatis), Lapisan (Bangunan 3D, Batas kelurahan, Batas RT, Sungai dan drainase; "Terrain DTM" dan "Orthophoto" = Segera hadir), `GeoportalPanel`, Navigasi (Tampilkan seluruh kota + daftar 15 kelurahan), `SimulationPanel` |
| Geoportal | `panels/GeoportalPanel.vue`, `RemoteLayerItem.vue`, `stores/remoteLayerStore.js`, `composables/useRemoteLayers.js`, `services/geoportalApi.js` | Inspect URL WFS/CSW, tambah, nonaktif, warna, refresh, hapus |
| Peta | `map/CesiumCanvas.vue`, `composables/useCesium.js` | Viewer, status memuat/galat + "Coba lagi", teardown berurutan, `requestRenderMode` |
| Panel kanan | `panels/ObjectInfoPanel.vue`, `stores/objectStore.js`, `services/buildingAttributes.js` | Atribut bangunan terpilih dari tile (semua properti), lokasi titik klik, sumber data, status memuat/galat |
| Legenda | `map/MapLegend.vue`, `composables/useLegend.js` | Kartu lipat kiri bawah peta: geoportal, batas, hidrologi, bangunan, simulasi |
| Simulasi | `simulation/SimulationPanel.vue`, `useSimulation.js`, `simulations/` | Registry (kosong), daftar rencana "Segera hadir" |
| Tile/peta | `use3DTiles.js` (560 baris), `useVectorLayers.js`, `useLayers.js`, `useRenderQuality.js`, `usePerfDebug.js` | Master tileset, kotak ikhtisar, `flyToKelurahan`, picking `LEFT_CLICK`, sorotan, layer vektor, basemap (2 provider), mode tampilan, `?debug=perf` |
| State | `mapStore`, `settingsStore`, `objectStore`, `remoteLayerStore`, `simulationStore` | Pinia setup store |
| Gaya | `tailwind.config.js`, `assets/main.css`, `utils/mapColors.js` | Token `bontang.*` (hanya gelap), warna peta tunggal untuk peta dan legenda |

Catatan: seluruh gaya sekarang hanya **gelap**, memakai kelas `*-bontang-*` Tailwind; font Public Sans.

## 3. Pemetaan elemen referensi → spectra

| Elemen referensi | Fitur spectra | Keputusan |
|---|---|---|
| Logo | Identitas spectra | **Dibuat sendiri:** penanda ikon sederhana + wordmark "spectra" dan "Digital Twin Kota Bontang"; bukan logo referensi |
| Pil navigasi (Home / Digital Twin / Catalog) | Aplikasi hanya punya satu halaman | **Tidak dibuat.** Di posisi itu tampil **judul aplikasi** "Digital Twin Kota Bontang"; pil navigasi ditambahkan nanti saat ada halaman kedua |
| Pencarian | Daftar kelurahan + `flyToKelurahan` | **Diganti:** "Cari kelurahan…" (saran bawah, panah/Enter). Pencarian bangunan tidak dibuat (tidak ada indeks) |
| Ganti bahasa | UI hanya Bahasa Indonesia | **Tidak dibuat** |
| Toggle tema (bulan) | — | **Dibuat:** Sistem / Terang / Gelap (`ThemeToggle`) |
| Peta dasar Terang / Ortho / Gelap | Basemap ArcGIS dan OSM | **Diganti:** Otomatis (ikut tema), Terang, Gelap, Citra satelit, OpenStreetMap |
| Ortho + epok 2022/2023/2026 | "Orthophoto 5 cm" direncanakan | **Segera hadir** (tanpa tahun/angka) |
| 3D View: LOD 1–4, GS, PC | Hanya LOD2 | **Dibuat:** satu chip "LOD2" aktif; LOD lain tidak ditampilkan |
| "Tekstur foto LOD 2" | Tidak ada tekstur | **Tidak dibuat** |
| (di referensi tidak ada) Mode tampilan | Hemat/Seimbang/Kualitas | **Dipertahankan**, masuk kartu "Tampilan 3D" |
| Fasilitas & Utilitas (Parkiran, CCTV, Sensor, …) | Tidak ada datanya | **Tidak dibuat** |
| (Layer vektor) | Batas kelurahan, RT, sungai; Terrain DTM | **Dibuat** kartu "Layer" (toggle); Terrain DTM = Segera hadir |
| (Navigasi) | Seluruh kota + 15 kelurahan | **Dibuat** kartu "Navigasi" (tombol + chip kelurahan, tanpa angka) |
| (Data geoportal) | Panel geoportal lengkap | **Dipertahankan**, dibuat ulang sebagai kartu (logika tidak berubah) |
| Toggle 2D / 3D | Kamera Cesium | **Dibuat sebagai "3D \| Atas"** lewat kamera (lihat §9); bukan mode peta datar |
| Kontrol zoom +/− | — | **Dibuat** |
| Kompas | Heading kamera | **Dibuat** (klik = utara) |
| "Seluruh Kota" | `zoomToKota` | **Dibuat** (tombol di kontrol peta) |
| Penggaris, lokasi saya | Tidak ada fitur | **Tidak dibuat** |
| Street view, asisten chat | Tidak ada | **Tidak dibuat** |
| Pil "Tren lingkungan" | Tidak ada data | **Tidak dibuat**; kiri bawah dipakai pil status model |
| Pil skala + koordinat | — | **Dibuat** (skala dari kamera, koordinat kursor, lihat §9) |
| Rail ikon kanan | Panel kanan | **Dibuat:** tombol buka/tutup, lalu Objek, Simulasi, Legenda. Ikon sensor/hujan/muka air/CCTV tidak dibuat |
| Kartu Sensor, Rainfall, Water Level, CCTV, hitungan kendaraan | Tidak ada data | **Tidak dibuat**, tidak juga sebagai placeholder berangka |
| Panel kanan (kartu bertumpuk) | Info bangunan, simulasi, legenda | **Dibuat:** kartu "Objek terpilih", "Simulasi", "Legenda" |

## 4. Token desain (mode terang dan gelap)

Memperluas namespace **`bontang.*`** yang ada (nama kelas tidak berubah, jadi semua komponen lama tetap bekerja). Nilai menjadi CSS variable per tema (`html[data-theme]`) dan Tailwind membacanya: `bontang-ink: rgb(var(--bontang-ink) / <alpha-value>)` (opasitas seperti `bg-bontang-ink/85` tetap bisa dipakai).

| Token | Gelap | Terang | Peran |
|---|---|---|---|
| `ink` | `#0D1820` | `#EEF3F6` | latar aplikasi |
| `panel` | `#122230` | `#FFFFFF` | permukaan kartu/panel |
| `raised` | `#19303F` | `#E3EBF0` | kontrol aktif, hover, bidang kedua |
| `line` | `#284556` | `#D3DEE5` | garis pemisah (dekoratif) |
| `edge` | `#557688` | `#6B8493` | batas kontrol interaktif |
| `text` | `#E4ECF0` | `#0F1E29` | teks utama |
| `muted` | `#9DB2BE` | `#425C6B` | teks sekunder |
| `subtle` | `#869EAC` | `#506A78` | teks tersier (≥ 12 px) |
| `accent` | `#6AA8FF` | `#1D5BC8` | **aksen UI biru:** tombol/segmen aktif, toggle, tautan, fokus |
| `accent-ink` | `#0A1424` | `#FFFFFF` | teks di atas aksen |
| `danger` | `#F08A7E` | `#B42318` | galat |
| `ok` | `#7FD1A8` | `#0F7B4B` | sukses |
| `warn` (baru) | `#F0B43C` | `#8F5E00` | peringatan (amber; teks `#8F5E00` di terang lulus 5,6) |
| `highlight` (baru) | `#F0B43C` | `#F0B43C` | **sorotan objek terpilih di peta: tetap amber/oranye** (kontras hue terhadap bangunan abu dan aksen biru) |
| `shadow` (baru) | `0 0 0 / .45` | `15 32 43 / .10` | warna bayangan |

Aksen UI **biru** (mengikuti referensi) menggantikan amber di seluruh UI (tombol/segmen aktif, switch, tautan, cincin fokus). Amber hanya tersisa sebagai **sorotan peta** (`highlight`) dan status peringatan (`warn`), sehingga tidak bertabrakan dengan aksen biru.

**Bentuk (sama di kedua tema):** `rounded-card` 20 px, `rounded-map` 24 px, `rounded-control` 12 px, `rounded-full` untuk chip/pil/tombol bulat. Jarak: gutter halaman 12 px, antarkartu 12 px, padding kartu 16 px. Bayangan kartu terang `0 1px 2px shadow, 0 4px 16px shadow`; di gelap kartu memakai garis tepi 1 px `line` (bayangan hampir tak terlihat). Tipografi: **Public Sans tetap** (sudah dimuat; tanpa font baru), ukuran dinaikkan: `body` 13→14, `title` 15→16, `display` 17→20; `caption`/`small` tetap.

### Kontras (dihitung, WCAG 2.x)

Gelap: teks/panel 13,5; teks/ink 15,0; muted/panel 7,4; subtle/raised 4,9; edge/panel 3,3 (UI ≥ 3); **aksen biru `#6AA8FF`/panel 6,7, /ink 7,4, /raised 5,6; teks-di-aksen `#0A1424` 7,6**; danger/panel 6,7; ok/panel 8,9 — **semua lulus AA**.
Terang: teks/panel 17,0; teks/ink 15,2; muted/panel 7,1, muted/raised 5,9; subtle/ink 5,1, subtle/raised 4,7; edge/panel 3,9 (UI ≥ 3); **aksen biru `#1D5BC8`/panel 6,2, /ink 5,6, /raised 5,2; teks putih di aksen 6,2**; warn `#8F5E00`/panel 5,6; danger/panel 6,6; ok/ink 4,8 — **semua lulus AA**. (Kandidat biru `#2563EB` gagal 4,3 di atas `raised`; `#4C8DFF` gelap gagal 4,3 di atas `raised`. Percobaan amber `#9A6700` gagal 4,35.)

## 5. Perilaku tema

- **Bawaan:** mengikuti `prefers-color-scheme`. **Pilihan pengguna:** Sistem / Terang / Gelap, disimpan di `localStorage` (kunci `spectra.theme`, semua akses dibungkus `try/catch`; tanpa penyimpanan tetap berfungsi).
- Diterapkan sebagai `data-theme="light|dark"` + `color-scheme` pada `<html>`. Skrip kecil di `index.html` menerapkannya **sebelum render pertama** (tanpa kilatan). Perubahan tema sistem saat pilihan = Sistem langsung diikuti.
- **Peta dasar** (bawaan **Otomatis**) mengikuti tema: terang→`terang`, gelap→`gelap`. Pilihan **manual** pengguna (Terang, Gelap, Citra satelit, OpenStreetMap) **disimpan** (`spectra.basemap`) dan **tidak tertimpa saat tema berganti**; memilih "Otomatis" mengembalikan perilaku mengikuti tema.
- Perubahan tema yang memengaruhi peta (basemap, warna garis, warna bangunan, warna dasar globe) memanggil `requestRender()`.

## 6. Peta dasar terang dan gelap (DIPUTUSKAN: opsi A, Esri Canvas)

Sebelumnya: **ArcGIS World_Imagery** (satelit) dan **OpenStreetMap standar**. Sekarang daftar basemap berada di **satu berkas konfigurasi** (`frontend/src/config/basemaps.js`); komponen dan composable hanya membaca daftar itu, jadi mengganti penyedia berarti mengubah entri konfigurasi, bukan komponen.

| id | Label | Sumber | Atribusi |
|---|---|---|---|
| `terang` | Terang | Esri `Canvas/World_Light_Gray_Base` + label `Canvas/World_Light_Gray_Reference` | Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community |
| `gelap` | Gelap | Esri `Canvas/World_Dark_Gray_Base` + label `Canvas/World_Dark_Gray_Reference` | sama |
| `satelit` | Citra satelit | Esri `World_Imagery` (sudah dipakai) | Esri dan sumber citra (teks dari layanan) |
| `osm` | OpenStreetMap | `tile.openstreetmap.org` (sudah dipakai) | © OpenStreetMap contributors |

- **Atribusi** diberikan eksplisit lewat opsi `credit` penyedia Cesium dan tampil di kontainer kredit Cesium untuk basemap yang sedang terlihat (kontainer kredit tetap dipindah ke kanan bawah dan mengikuti tema).
- Pembuatan penyedia **malas** (hanya saat dipilih pertama kali) agar tidak menambah permintaan jaringan saat startup. Bila satu basemap gagal dimuat, konfigurasi menyebut `fallback` (mis. `osm`) dan UI tidak rusak.
- **Hutang ketentuan (dicatat di STATUS.md):** ketentuan pemakaian layanan basemap Esri (terang/gelap **dan citra satelit yang sudah dipakai**) **belum diverifikasi** dan harus diperiksa sebelum dipakai publik; metadata Light Gray menyebut "mature support, no longer updated". **Alternatif:** CARTO Positron/Dark Matter dengan kunci API gratis. Rancangannya: entri `carto-terang`/`carto-gelap` di `basemaps.js` membaca kunci dari `import.meta.env.VITE_CARTO_KEY` (berkas `frontend/.env.local`, di-ignore git; contoh di `frontend/.env.example`). Perlu diingat kunci `VITE_*` ikut masuk bundel (kunci publik; batasi domain di sisi penyedia). Entri CARTO **tidak diaktifkan** sebelum Anda menyetujuinya.

## 7. Warna peta per tema

Warna peta dan legenda tetap satu sumber (`utils/mapColors.js`), kini berupa fungsi tema.

| Elemen | Gelap | Terang | Kontras vs peta dasar |
|---|---|---|---|
| Bangunan (warna material tile `#D9DEE2`) | tetap | **gelapkan lewat style tileset** ≈ `#9FB0BC` | terang: 1,08 → 1,77; gelap vs `#2B2F33`: 9,9 |
| Batas kelurahan | `#FFFFFF` | `#0D1820` | 13,5 / 14,3 |
| Batas RT | `#C3D3DC` | `#5B7385` | 8,8 / 3,9 |
| Sungai | `#38BDF8` | `#0284C7` | 6,3 / 3,3 |
| Drainase | `#5EEAD4` | `#0F766E` | 9,1 / 4,3 (percobaan `#0D9488` gagal 2,97) |
| Kotak ikhtisar kelurahan | `#CFE0E8` | `#4F6B7D` | — / 4,5 |
| Sorotan objek | `#F0B43C` (amber) | `#F0B43C` | hue berbeda dari bangunan abu **dan** dari aksen biru UI; **dinilai visual di Tahap 4** (rasio luminans amber vs abu hanya ±1,2–1,4) |

Penyesuaian bangunan di tema terang dilakukan **hanya lewat penyusun style tileset** (§7a), dan dicek bersama sorotan serta FPS. Warna layer geoportal buatan pengguna tidak diubah. `globe.baseColor` dan `scene.backgroundColor` mengikuti tema agar tidak ada kilatan biru bawaan Cesium saat tile peta dasar belum datang.

### 7a. Penyusun style tileset (satu tempat)

`frontend/src/composables/tilesetStyle.js` adalah **satu-satunya** tempat yang mengatur gaya warna tileset bangunan. Fitur lain (picking, tema, simulasi) **tidak** boleh menyentuh `tileset.style` atau `feature.color` langsung; mereka memanggil API penyusun:

| API | Dipanggil oleh | Efek |
|---|---|---|
| `attachTileset(tileset)` / `detachTileset()` | `use3DTiles` | menyimpan referensi tileset biasa (bukan `ref`) dan menerapkan gaya |
| `setTheme(theme)` | `useTheme` | warna bangunan per tema (terang: ≈`#9FB0BC`; gelap: tanpa style) |
| `setSimulationStyle(spec \| null)` | simulasi nanti (ADR-006) | **slot**: daftar kondisi gaya Cesium berbasis properti `id` (mis. `['${id} === "BTG-BLD-…"', 'color("#…")']`); `null` = tidak ada |
| `highlightFeature(feature)` / `clearHighlight()` | picking di `use3DTiles` | sorotan amber pada satu fitur, dan memulihkan warnanya dari gaya yang berlaku |

**Prioritas: sorotan > simulasi > tema.** Gaya dasar disusun sebagai `{ color: { conditions: [...kondisi simulasi, ['true', warna tema]] } }` (kondisi simulasi menang atas warna tema; tanpa simulasi hanya warna tema). Sorotan memakai `feature.color` per fitur (murah, tanpa menyusun ulang gaya seluruh tileset) dan **diterapkan ulang** setelah gaya berubah (mis. ganti tema saat ada objek terpilih). Penyusunan spesifikasi gaya adalah fungsi murni (`utils/tilesetStyleSpec.js`) yang diuji unit. Setiap perubahan memanggil `requestRender()`.

## 8. Tata letak dan responsivitas

```
≥ 1280 px:  [ header melayang: logo spectra | JUDUL APLIKASI | cari kelurahan | tema ]
            [ kolom kiri 288 | PETA (fleksibel, sudut 24) | panel kanan 320* | rail 56 ]
            * panel kanan hanya terbuka bila ada objek dipilih atau rail diklik
768–1279:   header + peta penuh; panel kiri & kanan = overlay laci (satu per satu), rail 56 px tetap di tepi kanan
< 768:      header ringkas (ikon logo, cari→ikon, tema); laci lebar 92vw; rail jadi dua tombol di header (Layer, Info);
            kontrol peta hanya zoom + kompas; pil koordinat disembunyikan (skala tetap)
```

- Laci overlay memakai `Transition` transform/opacity (sudah ada pola `panel-left/right`); `prefers-reduced-motion` dihormati; fokus dikembalikan ke tombol pembuka saat ditutup; `Esc` menutup laci.
- Panel kanan di ≥ 1280 px **tidak lagi selalu terbuka**: terbuka saat objek dipilih (perilaku sekarang) atau lewat rail. Peta lebih lebar saat idle (±830 px di 1280 px) seperti referensi.
- Cesium: wadah peta berubah ukuran lewat grid; viewer sudah menyesuaikan ukuran sendiri dan `requestRenderMode` merender ulang saat ukuran berubah.

## 9. Peta: 2D/3D, kontrol, skala, koordinat

- **2D/3D:** Cesium punya `scene.morphTo2D`, tetapi saya **tidak mengusulkannya**: 3D Tiles dengan `requestRenderMode`, kotak ikhtisar, picking, dan sorotan belum teruji di mode 2D/Columbus dan berisiko merusak fitur lain. Usulan: toggle **"3D | Atas"** yang mengubah **pitch kamera** (miring ±−45° ↔ menghadap bawah −90°) dengan `camera.flyTo`/`setView` dan `requestRender()`. Label "Atas" jujur: ini bukan peta datar 2D. Bila Anda tetap ingin mode 2D sungguhan, saya uji dulu di Tahap 4 dan hanya aktifkan bila semua fitur lolos.
- **Kontrol (kanan atas):** zoom +/− (`camera.zoomIn/zoomOut`, `requestRender`), kompas (ikon berputar menurut heading kamera; klik = utara), **Seluruh Kota** (`zoomToKota`). Tidak ada penggaris/lokasi saya.
- **Skala (kanan bawah):** jarak nyata per ±100 px di tengah bawah layar (dua `pickEllipsoid`), dibulatkan ke 1/2/5×10ⁿ; diperbarui saat kamera berhenti bergerak (`camera.changed`).
- **Koordinat kursor (DISETUJUI):** `pointermove` DOM biasa (bukan handler Cesium) + `camera.pickEllipsoid`, di-throttle (±100 ms atau per `requestAnimationFrame`). **Tanpa `scene.pick`/`drillPick`**, hanya mengubah teks di DOM, dan **tidak memanggil `requestRender()`** saat mouse bergerak. Teks UI menjelaskan bahwa koordinat adalah **posisi di permukaan bumi (elipsoid)**, bukan di atas bangunan. Aturan AGENTS.md §4 diperbarui: `scene.pick`/`drillPick` dilarang pada pergerakan mouse; `pickEllipsoid` ber-throttle untuk koordinat diperbolehkan. Di layar sentuh yang ditampilkan koordinat pusat peta.

## 10. Komponen

**Baru** (`frontend/src/`): `components/ui/` — `UiCard.vue` (judul, info, lipat), `UiSegmented.vue`, `UiSwitch.vue`, `UiChip.vue`, `UiIconButton.vue`, `UiIcon.vue` (ikon garis inline); `layout/ThemeToggle.vue`, `layout/KelurahanSearch.vue`, `layout/AppRail.vue`, `layout/BrandMark.vue`; `map/MapFrame.vue` (wadah bersudut), `map/MapControls.vue`, `map/ViewModeToggle.vue`, `map/MapStatusBar.vue`; `panels/BasemapCard.vue`, `panels/View3DCard.vue`, `panels/LayersCard.vue`, `panels/NavigationCard.vue`.
**Store/composable/util baru:** `stores/themeStore.js` (preferensi, tema terpakai, pilihan basemap), `composables/useTheme.js` (menerapkan ke DOM dan Cesium), `composables/useMapControls.js`, `composables/useMapReadout.js` (skala, koordinat, heading), `utils/theme.js`, `utils/coords.js` (format koordinat, pembulatan skala), `utils/search.js` (penyaringan kelurahan).
**Diubah:** `App.vue` (grid baru), `layout/AppHeader.vue` (diganti), `panels/LayerControl.vue` (dipecah ke kartu), `DisplaySettings.vue`, `GeoportalPanel.vue`, `RemoteLayerItem.vue`, `ObjectInfoPanel.vue`, `SimulationPanel.vue`, `map/MapLegend.vue` (menjadi kartu panel kanan), `map/CesiumCanvas.vue` (hanya overlay memuat/galat), `composables/useLayers.js` (basemap per tema), `stores/mapStore.js`, `utils/mapColors.js` (per tema), `use3DTiles.js`/`useVectorLayers.js` (hanya membaca warna tema dan merespons perubahan tema; logika picking/dispose tidak berubah), `tailwind.config.js`, `assets/main.css`, `index.html`.
**Tidak diubah:** semua store/composable data (`objectStore`, `remoteLayerStore`, `useRemoteLayers`, `services/*`, `simulations/*`), `useRenderQuality`, `usePerfDebug`.

## 11. Performa

Tidak memakai `backdrop-filter`/blur di atas kanvas peta (permukaan buram atau semiburam solid). Bayangan statis (`box-shadow`) pada elemen di atas kanvas murah. Tidak ada animasi terus-menerus di atas kanvas (`prefers-reduced-motion` dihormati). Wadah bersudut membulat (`overflow:hidden` + `border-radius` di atas kanvas WebGL) akan **diukur** (FPS/GPU, Seimbang, kamera diam dan bergerak) dibanding baseline uji impor resmi: lama 56,7 FPS/GPU 68,5% vs v2 58,1 FPS/65,3%, Hemat 30 FPS/±19%, diam 0 frame/1%.

## 12. Rencana tahap

1. **Tahap 2 — fondasi tema:** token (CSS variable + Tailwind), `themeStore`, `ThemeToggle`, skrip pra-render, basemap per tema (sesuai penyedia yang Anda setujui), warna peta per tema, `globe.baseColor`. Semua perubahan peta memanggil `requestRender()`.
2. **Tahap 3 — tata letak:** (a) shell grid + header + pencarian kelurahan; (b) kartu panel kiri; (c) peta bersudut + kontrol + skala/koordinat + toggle 3D/Atas; (d) panel kanan + rail + legenda; (e) responsivitas. Logika fitur tidak diubah; logika Cesium tetap di composable.
3. **Tahap 4 — verifikasi:** `npm test` (tes baru: tema, koordinat, skala, penyaringan kelurahan), `npm run build` (hapus `dist/`), uji Chromium terang+gelap (konsol, klik bangunan, layer, geoportal, mode tampilan, tema tersimpan setelah reload), kontras, FPS/GPU, tangkapan layar sebelum/sesudah di 1440 dan 1280 px.

## 13. Keputusan pemilik proyek (2026-11-20)

1. **Basemap:** opsi A (Esri Canvas Light/Dark Gray) dengan atribusi yang benar; hutang ketentuan Esri (termasuk citra satelit) dicatat di STATUS.md; alternatif CARTO dengan kunci di `.env`; sumber basemap lewat konfigurasi (§6).
2. **Koordinat kursor:** `pointermove` DOM + `pickEllipsoid` ber-throttle, tanpa `scene.pick`, tanpa `requestRender()`; AGENTS.md diperbarui; UI menjelaskan koordinat permukaan bumi (§9).
3. **"3D | Atas"** lewat pitch kamera (§9).
4. **Tanpa pil navigasi**; judul aplikasi di posisi itu (§3, §8).
5. **Basemap bawaan "Otomatis"**; pilihan manual tersimpan dan tidak tertimpa saat tema berganti (§5, §6).
6. **Legenda di panel kanan.**
7. **Aksen UI biru** (tombol/segmen aktif, switch, tautan, fokus; AA di kedua tema); **sorotan bangunan tetap amber**; **font tetap Public Sans** (§4).
8. **Penyusun style tileset** di satu tempat, prioritas sorotan > simulasi > tema, dengan slot simulasi ADR-006 (§7a).
9. **Panel kanan** terbuka hanya saat objek dipilih atau lewat rail (§8).

## 14. Hasil uji browser Tahap 2 (2026-11-20; Chromium headless, GPU AMD Radeon/radeonsi)

Perubahan nilai setelah uji: **`edge` gelap `#557688` -> `#5F8194`** (di atas `raised` hanya 2,82; kini 3,29). **Warna bangunan tema terang `#A9B7C2` -> `#7C8E9C`** (kontras median terhadap basemap terang naik dari 3,3 ke 5,1 di kawasan padat). Tabel kontras batas kontrol (WCAG 1.4.11, >= 3:1), dihitung dari nilai di `main.css`:

| Tema | edge | di atas ink | di atas panel | di atas raised |
|---|---|---|---|---|
| Gelap | `#5F8194` | 4,33 | 3,90 | 3,29 |
| Terang | `#6C8593` | 3,35 | 3,88 | 3,57 |

Bukti tangkapan layar ada di `docs/desain/uji-tema/`.

**Ditinjau di Tahap 4:** pada tema gelap, kontras bangunan terhadap basemap di kawasan padat bernilai median 4,5 tetapi **persentil ke-10 hanya 1,8** (sisi bangunan yang membelakangi cahaya). Tidak diubah di Tahap 2; opsi yang akan dinilai: warna dasar bangunan tema gelap (saat ini tanpa gaya, warna tile `#B1BAC2`) atau pencahayaan. Putusan memakai tangkapan layar pembanding.

**Skrip uji ulang:** `frontend/tests/browser/` (lihat README di sana).

## 15. Tahap 3: penyimpangan dari rencana §10 (2026-11-20)

Komponen digabung agar lebih ringkas: `map/MapOverlay.vue` memuat toggle 3D/Atas, kontrol peta, skala, dan koordinat; `composables/useMapControls.js` memuat kontrol dan pembacaan kamera (kompas, skala, koordinat); `ui/UiCard.vue` + `ui/UiIcon.vue` menggantikan `UiSegmented/UiSwitch/UiChip/UiIconButton/BasemapCard/View3DCard/LayersCard/NavigationCard` (kartu dibuat langsung di `LayerControl.vue`). `layout/AppRail.vue` kini berisi satu tombol (panel informasi + legenda); `BrandMark` berupa SVG inline di `AppHeader.vue`. Tangkapan layar: `docs/desain/tahap3/`.

## 16. Hasil Tahap 4 (2026-11-20)

**Performa** (`frontend/tests/browser/ukur_performa.cjs`; Loktuan 700 m, pitch −35°, tile v2, Chromium GPU AMD radeonsi; sebelum = UI di `main`, sesi dan skrip sama; data di `docs/desain/tahap4/performa_*.json`):

| Mode | Kondisi | Sebelum (kanvas 784×798) | Sesudah terang / gelap (kanvas 1006×780) |
|---|---|---|---|
| Hemat | memutar | 29,9 fps / GPU 20,8% | 29,9 / 21,8% — 30,0 / 21,8% |
| Seimbang | memutar | 58,0 fps / GPU 67,3% | 57,7 / 71,7% — 57,3 / 72,3% |
| Keduanya | diam | 0 fps / ±2% | 0 fps / ±2,4% |

fps tidak turun. Beban GPU Seimbang naik ±5 poin karena kanvas 26% lebih luas (panel kanan tertutup); per megapiksel justru lebih rendah (107,6 → 91,8 %/MP). Tema terang dan gelap sama. Wadah bersudut dan overlay tidak menambah beban yang terukur. Batasan: GPU tidak linear terhadap piksel, dan tidak dilakukan uji pembeda (radius 0) karena angka sudah dalam toleransi.

**Kontras tema gelap, kawasan padat** (`ukur_kontras.cjs`; tampilan Loktuan, selisih piksel dengan/tanpa tileset): dasar median 2,27, p10 1,32. Intensitas cahaya matahari ×3: median 2,50, p10 1,33; ×6: median 3,01, p10 1,35 (atap makin putih dan bayangan rata). `lightColor` tidak berefek dan faktor IBL dibatasi ≤ 1 oleh Cesium. **Putusan: tidak diubah**; p10 rendah berasal dari sisi bangunan di bayangan di atas dasar gelap, dan memperbaikinya lewat cahaya hanya meratakan bentuk 3D. Dicatat sebagai batasan (STATUS #38). Angka ini memakai tampilan dan ambang berbeda dari Tahap 2 (4,5/1,8), jadi tidak dapat dibandingkan langsung; yang sebanding hanyalah antar kandidat. Gambar: `docs/desain/tahap4/kontras_gelap_*`.

**Uji otomatis:** `npm run test:browser` (`uji_tema.cjs` 16 uji, `uji_tata_letak.cjs` 52 uji: klik dan sorotan termasuk setelah ganti tema, panel/laci 1440/1024/390, pencarian, 3D/Atas, zoom, kompas, geoportal saat backend 500 dipalsukan). Pembandingan sorotan memakai selisih piksel (ambang sorotan > 150 px; kembali ke dasar: gaya tileset sama dengan tema + selisih < 1.200 px, karena derau LOD tile dan basemap ±5–410 px). **Header 390 px:** nama spectra tetap tampil, judul "Digital Twin Kota Bontang" disembunyikan secara visual (tetap `h1` untuk pembaca layar) di bawah 640 px. Screenshot gelap 1024/390: `docs/desain/tahap3/`.
