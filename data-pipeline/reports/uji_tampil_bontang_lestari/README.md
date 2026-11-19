# Uji tampil tile v2 Bontang Lestari (2026-11-20, uji coba)

Membandingkan tile lama (`processed/3dtiles/`) dan tile v2 (`processed/3dtiles_v2/`, dari CityGML → PostGIS → tyler) untuk kelurahan
Bontang Lestari di frontend yang sama, **tanpa mengubah kode `frontend/` atau `backend/`**.

## Yang diuji
- Master hibrida: v2 untuk `bontang_lestari`, tile lama untuk 14 kelurahan lain (`04_build_master.py --v2 bontang_lestari`).
- Tangkapan layar sebelum/sesudah pada kamera identik: area perumahan (Part I), kawasan PLTU (Part VII), atap miring, atap datar,
  bangunan tinggi, dan tampak atas atap datar.
- Klik tiga bangunan: atap miring `BTG-BLD-001072`, atap datar `BTG-BLD-001082`, bangunan 49,1 m `BTG-BLD-000700`; isi panel info dicatat.
- Konsol browser (galat/peringatan, permintaan HTTP ≥ 400), dan warna material terhadap legenda.

## Cara mengulang
1. Cadangkan `frontend/public/tiles/` (dibutuhkan mode `sebelum` dan untuk pengembalian):
   `rsync -a frontend/public/tiles/ data-pipeline/processed/backup_public_tiles/`
2. Bangun master hibrida dan sinkron:
   `python3 data-pipeline/scripts/04_build_master.py --v2 bontang_lestari --master-out data-pipeline/processed/3dtiles_v2/master-tileset.json --sync`
3. Jalankan frontend (`cd frontend && npm run dev`, port 3000) dan backend (`backend/.venv/bin/uvicorn app.main:app --app-dir backend --port 8100`).
4. `node data-pipeline/scripts/citygml/uji_tampil.cjs sesudah`, lalu `... sebelum` (mode `sebelum` menyajikan tile lama dari cadangan lewat
   `page.route`, jadi tidak mengubah berkas). Butuh Playwright dan Chromium (`PLAYWRIGHT_DIR`, `CHROME_PATH`; lihat kepala skrip).
5. Kembalikan: `rsync -a --delete data-pipeline/processed/backup_public_tiles/ frontend/public/tiles/` lalu
   `(cd frontend/public/tiles && sha256sum -c --quiet ../../../data-pipeline/reports/hash_baseline_public_tiles.txt)`.

Keluaran: `{sebelum,sesudah}_*.png` (tidak di-commit; di-ignore git) dan `log_{sebelum,sesudah}.json` (di-commit).

## Ringkasan hasil
- **Konsol bersih:** 0 galat, 0 peringatan, 0 permintaan gagal (mode sebelum dan sesudah).
- **Atribut tampil:** panel info menampilkan `id`, `gml_id`, `nama`, `tinggi`, `jumlah_lantai`, `luas_tapak` untuk ketiga bangunan
  (`BTG-BLD-001072`: 6,901 m, 1 lantai, 88,21 m²; `BTG-BLD-001082`: 3,16 m, 1 lantai, 119,17 m²; `BTG-BLD-000700`: 49,1 m, 9 lantai, 18,07 m²).
- **Bentuk:** atap miring (limas/pelana) dan dinding tampil utuh; tidak ada lubang yang terlihat. Di kawasan PLTU, v2 menampilkan jauh lebih
  banyak bangunan (2.215 vs 774 di tile lama).
- **Segitiga:** tile lama 774 fitur bukan hanya Part VII (cocok dengan Part VII 430, I 212, II 50, V 80, + 2 fitur bertinggi ≈ 0 m). Pada 772
  pasangan cocok: 50.136 vs 24.917 segitiga = **2,01×**, jadi pipeline lama tidak membuang permukaan terbalik.
- **Warna:** tyler memperlakukan hex sebagai nilai linear: `#D9DEE2` menghasilkan `baseColorFactor` 0,851/0,871/0,886 (≈ sRGB 238,240,242),
  ±9% lebih terang dari legenda (217,222,226). Hue sama. Perbaikan: `#B1BAC2` (sudah di `config/citygml_sources.yaml`, dipakai impor resmi).
- **Pengembalian terbukti:** setelah uji, `frontend/public/tiles/` kembali ke 142 berkas dengan semua hash cocok `hash_baseline_public_tiles.txt`;
  `processed/3dtiles/` (156 berkas) dan 8 berkas CityGML Bontang Lestari juga cocok baseline.
- **Batasan:** Chromium headless dengan WebGL SwiftShader (≈1–3 FPS), bukan GPU nyata; bukan uji performa; satu kelurahan.
