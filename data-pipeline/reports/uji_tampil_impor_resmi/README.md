# Uji tampil impor resmi (2026-11-20)

Tile v2 15 kelurahan di frontend (`frontend/public/tiles/`, master v2) diuji di Chromium headless **dengan GPU sungguhan** (AMD Radeon Renoir via ANGLE/EGL) tanpa mengubah kode `frontend/` atau `backend/`. Skrip: `scripts/citygml/uji_impor_resmi.cjs`; target: `targets.json` (dipilih dari PostGIS per kategori).

## Cara mengulang
1. Cadangkan `frontend/public/tiles/` ke `data-pipeline/processed/backup_public_tiles/` dan uji pengembaliannya (lihat `data-pipeline/README.md` bagian 6); sinkron master v2: `04_build_master.py --v2 <semua slug> --master-out … --sync`.
2. Jalankan frontend (`cd frontend && npm run dev`) dan backend (`backend/.venv/bin/uvicorn app.main:app --app-dir backend --port 8100`).
3. `node data-pipeline/scripts/citygml/uji_impor_resmi.cjs klik` (klik per kategori; `?debug=perf` mengekspos viewer) dan `... fps` (tile lama disajikan dari cadangan lewat `page.route`; beban GPU dari `/sys/class/drm/card1/device/gpu_busy_percent`). `GPU_ARGS=swiftshader` untuk software.
PNG tidak di-commit (di-ignore); `log_klik.json` dan `log_fps.json` di-commit.

## Klik bangunan (renderer: ANGLE (AMD, AMD Radeon Graphics (radeonsi renoir ACO), OpenGL ES 3.2))

| Kategori | ID | Panel: jumlah_lantai | luas_tapak | tinggi | ID di panel cocok |
|---|---|---|---|---|---|
| Berebas Tengah, `jumlah_lantai` kosong (noData) di tile yang punya kolomnya | BTG-BLD-014435 | *(baris tidak ada)* | 131,46 | 6,562 | ya |
| Berebas Tengah, tile tanpa kolom `jumlah_lantai` | BTG-BLD-011807 | *(baris tidak ada)* | 103,88 | 7,043 | ya |
| Berebas Tengah, `jumlah_lantai` diisi dari duplikat (flag `atribut_dari_duplikat`) | BTG-BLD-014442 | 1 | 76,42 | 6,81 | ya |
| Api Api, tanpa footprint (`luas_tapak` kosong) | BTG-BLD-000490 | 1 | *(baris tidak ada)* | 6,175 | ya |
| Satimpo (EPSG dan Z dikoreksi) | BTG-BLD-041374 | 1 | 152,72 | 5,55 | ya |
| Guntung Part I (EPSG dikoreksi) | BTG-BLD-023932 | 1 | 151,63 | 6,411 | ya |
| Gunung Elai Part I (dulu hilang di tile lama) | BTG-BLD-026016 | 1 | 192,51 | 6,263 | ya |
| Kanaan (kelurahan biasa) | BTG-BLD-034436 | 1 | 93,01 | 5,796 | ya |
| Api Api, `duplikat_kepercayaan_rendah` | BTG-BLD-000046 | 1 | 571,81 | 8,278 | ya |
| Gunung Elai Part III, `duplikat_kepercayaan_rendah` | BTG-BLD-026756 | 1 | 104,76 | 7,525 | ya |
| Loktuan, di luar batas kelurahan | BTG-BLD-039618 | 1 | 120,98 | 5,787 | ya |
| Bontang Lestari Part VII, di luar batas | BTG-BLD-022085 | 1 | 22,56 | 4,817 | ya |
| Bontang Kuala, di luar batas | BTG-BLD-021678 | 2 | 218,64 | 10,395 | ya |
| Guntung Part II, di luar batas | BTG-BLD-024066 | 1 | 81,09 | 7,072 | ya |

Konsol: 0 galat halaman, 0 permintaan gagal; 52 peringatan, semuanya `WebGL: INVALID_VALUE: uniform3fv: no array` yang muncul hanya setelah klik (sorotan fitur) di GPU AMD (tidak di SwiftShader, tidak saat memuat atau menggerakkan kamera).

## Temuan nilai kosong (butir 1) dan perbaikannya
- **Sebelum perbaikan** (`log_klik_sebelum_perbaikan.json`): `noData` tampil sebagai teks **`undefined`** pada baris atribut (`jumlah_lantai` di tile yang punya kolomnya, `luas_tapak` pada bangunan tanpa footprint), sedangkan tile tanpa kolom tidak menampilkan baris sama sekali (inkonsisten). Tidak ada `null`, `NaN`, atau `2147483647`.
- **Perbaikan (satu-satunya perubahan frontend dalam pekerjaan pipeline ini):** `readFeatureProperties` (kini di `frontend/src/utils/tileMeta.js`, dipakai `use3DTiles.js`) melewati properti bernilai `undefined`/`null`; angka 0 dan string kosong tetap disimpan. Tes: `npm test` 19 lulus (2 baru), `npm run build` sukses.
- **Sesudah perbaikan** (tabel di atas): `BTG-BLD-014435` (`jumlah_lantai` kosong) dan `BTG-BLD-000490` (`luas_tapak` kosong) tidak lagi menampilkan barisnya; tidak ada teks `undefined` di panel mana pun (14 klik). Pada tile tanpa kolom, perilakunya sama (baris tidak muncul).

## 16 bangunan `luas_tapak` = 0 (butir 2)
Semua footprint **valid** (`ST_IsValid`), berluas nyata tetapi sangat kecil: **0,00014–0,0039 m²** (1,4–39 cm²; keliling 0,08–3,95 m; dimensi dari beberapa mm hingga ±1,9 m, sebagian sliver tipis, mis. 0,006 × 0,278 m) yang **terbulatkan** ke `luas_tapak` 0,00. Bukan degenerasi titik/garis (luas > 0). Tingginya 0,9–5,5 m (serpihan tegak), semuanya sudah berflag `footprint_kurang_2m2`. Rincian: Bontang Baru 6, Gunung Telihan 8, Berebas Tengah 1, Tanjung Laut Indah 1.
**Tindak lanjut (disetujui):** aturan QC `footprint_mikro` (luas mentah < 0,01 m²) ditambahkan ke pipeline dan diterapkan lewat `impor_resmi.py qc-ulang`: **22** bangunan berflag (ke-16 bangunan ber-`luas_tapak` 0,00, 2 ber-`luas_tapak` 0,01, dan 4 bertinggi < 0,1 m yang tidak masuk tile). Hanya `qc_flag` yang berubah; ID, registri, geometri, dan tile tidak berubah.

## Duplikat berkepercayaan rendah dan di luar batas (butir 3)
- `BTG-BLD-026756` (Gunung Elai Part III): bangunan berdiri sendiri di lahan terbuka; posisi wajar. `BTG-BLD-000046` (Api Api): kawasan padat; wajar.
- Di luar batas kelurahan: `BTG-BLD-039618` (Loktuan, tepi permukiman di sisi batas), `BTG-BLD-022085` (Bontang Lestari Part VII, bangunan terpencil di koridor jalan area PLTU), `BTG-BLD-021678` (Bontang Kuala, kelompok rumah panggung di atas air; garis batas memotong di dekatnya), `BTG-BLD-024066` (Guntung Part II, rumah panggung dengan perahu di tepi laut). Keempatnya **tampak wajar** (tepi laut/pulau/koridor), bukan kesalahan koordinat. Tangkapan layar `klik_luar_batas_*.png` dan `klik_dup_rendah_*.png` (lokal, tidak di-commit).

## FPS dan beban GPU (butir 4) — ANGLE (AMD, AMD Radeon Graphics (radeonsi renoir ACO), OpenGL ES 3.2)

Beban GPU sistem saat idle: rata-rata 1.3% (min 1, maks 3). Pandangan: Loktuan, jarak kamera 700 m, pitch -35 derajat; 'putar' = orbit 360 derajat selama 10 s; 'diam' = 10 s tanpa interaksi; tile lama disajikan dari cadangan.

| Tile | Mode | Diam: FPS / GPU rata-rata | Memutar: FPS / GPU rata-rata (maks) | Tile terpilih | Memori tileset |
|---|---|---|---|---:|---:|
| lama | hemat | 0 / 1% | 30 / 20.1% (28%) | 5 | 52 MB |
| lama | seimbang | 0 / 1% | 56.7 / 68.5% (87%) | 7 | 74 MB |
| v2 | hemat | 0 / 1% | 30 / 19.2% (27%) | 5 | 18 MB |
| v2 | seimbang | 0 / 1% | 58.1 / 65.3% (86%) | 7 | 26 MB |

- **Tidak lebih berat:** v2 (51.816 bangunan, segitiga ½ tile lama per bangunan) setara tile lama: Seimbang memutar 58,1 vs 56,7 FPS dan GPU 65,3% vs 68,5%; Hemat 30 vs 30 FPS dan 19,2% vs 20,1%. Memori tileset v2 18–26 MB vs 52–74 MB.
- **Kamera diam:** 0 frame dirender dan GPU 1% (`requestRenderMode` bekerja); catatan 15 November: ±8% (idle sistem saat itu).
- **Perbandingan dengan 15 November:** Seimbang memutar kamera ±80–82% pada catatan lama vs 65–68% (maks 86–87%) sekarang. Tidak sebanding persis: skrip lama tidak tersimpan, pandangan dan lamanya orbit berbeda, dan rata-rata di sini mencakup awal pengukuran. Perbandingan tile lama vs v2 pada prosedur yang sama di atas adalah yang valid.
- Batasan: satu pandangan, satu kali ukur, FPS dibatasi ±60 (vsync/headless), beban GPU sistem termasuk proses lain.
