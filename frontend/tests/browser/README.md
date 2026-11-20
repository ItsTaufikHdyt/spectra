# Uji browser tema (regresi)

Menguji tema terang/gelap/sistem dan basemap di Chromium headless dengan GPU sungguhan. Tidak ikut `npm test` (butuh browser dan dev server).

## Prasyarat
- Dev server frontend di `http://localhost:3000` (`cd frontend && npm run dev`). Backend tidak wajib (galat 500 `/api/layers` disaring).
- `frontend/public/tiles/` terisi (`04_build_master.py --sync`) agar model 3D termuat.
- Playwright dan Chromium. Atur `PLAYWRIGHT_DIR` dan `CHROME_PATH` bila bukan lokasi bawaan skrip. `GPU_ARGS=swiftshader` untuk perender perangkat lunak.

## Menjalankan (uji tema)
```
node frontend/tests/browser/uji_tema.cjs
SHOT_DIR=/tmp/x node frontend/tests/browser/uji_tema.cjs   # + tangkapan layar
```
Kode keluar 1 bila ada uji gagal.

**Semua uji sekaligus:** `cd frontend && npm run test:browser` (menjalankan `uji_tema.cjs` lalu `uji_tata_letak.cjs`; backend tidak perlu, `/api` dipalsukan 500).

Pengukuran (bukan lulus/gagal): `ukur_performa.cjs` (FPS/GPU, env `TEMA`, `MODE`, `VIEWPORT`, `APP_URL`; `--keluar x.json`) dan `ukur_kontras.cjs` (kontras bangunan vs basemap per kandidat).

## Yang diuji
1. Kontras `edge` terhadap ink/panel/raised, kedua tema, >= 3:1 (dihitung dari `src/assets/main.css`).
2. Tema awal tanpa kedipan (OS terang, OS gelap, pilihan gelap tersimpan di OS terang); mode Sistem mengikuti perubahan OS lewat CDP tanpa reload; pilihan bertahan setelah reload; `localStorage` diblokir tetap jalan.
3. Basemap: Esri terang/gelap termuat; Otomatis mengikuti tema; pilihan manual (satelit) tidak tertimpa; fallback OSM dengan atribusi saat `arcgisonline.com` diblokir; konsol tanpa galat baru.

## Belum tercakup
Uji sorotan bangunan dan warna campuran (klik bangunan, ganti tema, batalkan) serta kontras bangunan terhadap basemap diukur manual di Tahap 2 (bukti: `docs/desain/uji-tema/`); skrip otomatisnya belum ada. Mengandalkan label tombol UI (`Tema terang/gelap/mengikuti perangkat`, `Citra satelit`); ubah skrip bila label berubah.
