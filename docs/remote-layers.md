# Layer geoportal (WFS/CSW) di spectra

Pengguna bisa menempelkan link WFS atau CSW geoportal, memilih layer, lalu menampilkannya di peta.
Fitur ini terdiri dari backend kecil (`backend/`, FastAPI) dan panel **Data geoportal** di panel kiri.

```
Browser (Vue + Cesium) ──/api──► Vite proxy ──► backend/ (FastAPI) ──https, hanya-baca──► geoportal (WFS/CSW)
        │                                            │
        └── mode WMS: gambar GetMap langsung ──►     └── processed/user_layers/registry.json + <id>/data.geojson
            dari geoportal (butuh CORS)
```

Browser **tidak** memanggil WFS atau CSW secara langsung. Backend memakai ulang adapter di
`data-pipeline/scripts/sources/` (diimpor, bukan disalin), jadi normalisasi CRS dan urutan sumbu
sama dengan `fetch_sources.py`.

## Menjalankan

Sekali saja:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
```

Setiap kali bekerja, di dua terminal (dari root repo):

```bash
backend/.venv/bin/uvicorn app.main:app --app-dir backend --port 8100
cd frontend && npm run dev          # http://localhost:3000, /api diteruskan ke 127.0.0.1:8100
```

Port backend lain: jalankan `SPECTRA_API_URL=http://127.0.0.1:<port> npm run dev`.
Dokumentasi API interaktif: `http://127.0.0.1:8100/api/docs`. Tes: `backend/.venv/bin/pytest backend -q`.

Jalankan uvicorn dengan **satu worker**: registry berupa satu file JSON dengan lock di dalam proses.

## Endpoint

| Metode | Path | Fungsi |
|---|---|---|
| POST | `/api/sources/inspect` | `{url}` → deteksi WFS/CSW, daftar layer: judul, jumlah fitur (`resultType=hits`), SRS, bbox, ketersediaan WMS, `besar` |
| GET | `/api/layers` | Daftar layer tersimpan (aktif, sumber, jumlah fitur, waktu ambil, mode) |
| POST | `/api/layers` | `{wfs_url, typename, judul?, mode: geojson\|wms, field_nama?}` → ambil, normalisasi, simpan |
| PATCH | `/api/layers/{id}` | Ubah `aktif`, `judul`, `warna`, `opasitas`, `urutan`, `field_nama` |
| POST | `/api/layers/{id}/refresh` | Tarik ulang dari geoportal; bila gagal, data lama tetap dipakai dan pesan disimpan |
| DELETE | `/api/layers/{id}` | Hapus dari registry **dan** cache lokal. Tidak ada request apa pun ke geoportal |
| GET | `/api/layers/{id}/data` | GeoJSON hasil normalisasi (EPSG:4326, lon/lat) |

## Menambah host ke allowlist

Edit `backend/config/allowed_hosts`, satu host per baris (tanpa `https://` dan port). File dibaca ulang
di setiap request. Aturan yang tetap berlaku untuk host apa pun:

- hanya `https` di port 443, tanpa nama pengguna/kata sandi di URL;
- `localhost` dan IP privat/loopback/link-local ditolak, termasuk host di allowlist yang DNS-nya
  mengarah ke IP privat;
- setiap redirect diperiksa ulang; redirect ke host di luar allowlist ditolak;
- hanya operasi GetCapabilities, DescribeFeatureType, GetFeature, GetRecords, dan GetRecordById.
  Transaction (WFS-T), Harvest, LockFeature, dan sejenisnya ditolak sebelum request dikirim.

Celah yang diketahui: DNS diperiksa sebelum request, lalu di-resolve ulang saat koneksi (DNS rebinding).
Risikonya kecil selama allowlist hanya berisi host milik Pemkot.

Jika suatu saat geoportal butuh login, simpan kredensial di `.env` (sudah di-ignore) dan baca dari
lingkungan; jangan menaruhnya di `allowed_hosts` atau URL.

## Batas ukuran

| Batas | Nilai | Ubah lewat |
|---|---|---|
| Jumlah fitur untuk mode GeoJSON | 20.000 | env `SPECTRA_MAX_FITUR` |
| Ukuran satu respons dari geoportal | 50 MB | env `SPECTRA_MAX_BYTES` |
| Timeout per request | 30 detik, 3 percobaan (jeda 1 s, 2 s) | `TIMEOUT_S` di `backend/app/geoportal.py` |

Jumlah fitur selalu dihitung dulu dengan `resultType=hits`. Layer di atas batas tidak diunduh;
panel menampilkan badge **Besar — WMS** dan tombol **Tambahkan WMS**.

## Mode GeoJSON vs WMS

| | GeoJSON | WMS |
|---|---|---|
| Data | Diunduh backend (GetFeature, paging), disimpan di `processed/user_layers/<id>/data.geojson` | Tidak diunduh; browser meminta gambar GetMap |
| Request browser | Hanya ke `/api` | Langsung ke geoportal (pengecualian aturan di atas) |
| Gaya | Warna dan opasitas diatur di spectra; polygon diisi transparan + garis batas di permukaan tanah | Gaya dari GeoServer; spectra hanya mengatur opasitas |
| Klik fitur | Atribut tampil di panel informasi | Belum (GetFeatureInfo belum dipakai) |
| Cocok untuk | ≤ 20.000 fitur | Layer besar (mis. rawan karhutla, 79.167 fitur) |

**Status WMS saat ini:** GeoServer geoportal hanya mengizinkan CORS dari domainnya sendiri; request
gambar dari domain spectra dibalas 403, sehingga layer WMS tidak tampil dan panel menampilkan pesan
"Gambar WMS gagal dimuat dari geoportal…". Pilihan perbaikan: izinkan origin spectra di filter CORS
GeoServer, atau tambahkan proxy GetMap di backend (perlu menambah GetMap ke daftar operasi yang diizinkan).

## Nama fitur

Mode generik menebak kolom nama dari `nama`, `name`, `judul`, `keterangan` (persis, tanpa peduli kapital),
lalu kolom berawalan sama (mis. `nama_edt`). Pengguna bisa menggantinya di **Atur → Kolom nama**;
perubahan ini hanya menulis ulang cache lokal, tanpa request ke geoportal.
