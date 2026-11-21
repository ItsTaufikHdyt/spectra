# spectra — Digital Twin Kota Bontang

Platform **Web 3D GIS** (CesiumJS) untuk Digital Twin Kota Bontang: visualisasi 3D kota (51.873 bangunan LOD2), layer geoportal, dan fondasi simulasi banjir/rob.
Repo **privat**; data besar dan turunan **tidak ada di repo** (lihat tabel di bawah).

- **Status implementasi:** [`STATUS.md`](STATUS.md) · **Panduan kontributor/agent dan aturan keras:** [`AGENTS.md`](AGENTS.md) · **PRD:** [`PRD.md`](PRD.md) · **Keputusan arsitektur:** [`docs/adr/`](docs/adr/) (ADR-001–007)
- **Satu jalur data bangunan:** CityGML (`data-pipeline/raw/citygml/`) → PostGIS → CityJSONSeq → tyler → 3D Tiles. ID bangunan resmi `BTG-BLD-xxxxxx` sudah terbit (51.873 ID, 2026-11-20); registri di [`data-pipeline/config/registri_id.csv`](data-pipeline/config/registri_id.csv) (+ `.sha256`). Jangan dibuat ulang.

## Struktur
```
frontend/       Vue 3 + Vite + CesiumJS + Pinia + Tailwind (SPA)
backend/        FastAPI (layer geoportal WFS/CSW; atribut bangunan dari PostGIS: direncanakan)
data-pipeline/  ETL offline + PostGIS dev (Docker) + skrip impor/tile/verifikasi; panduan: data-pipeline/README.md
docs/           ADR, audit, dokumentasi layer remote dan kontrak simulasi
```

## Menjalankan (dev)
```
cd frontend && npm install && npm run dev                                   # http://localhost:3000
python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/uvicorn app.main:app --app-dir backend --port 8100        # API; Vite mem-proxy /api
cd frontend && npm test && npm run build ; backend/.venv/bin/pytest backend -q
# Kondisi Terkini (panel kanan): hotspot butuh kunci NASA FIRMS gratis (https://firms.modaps.eosdis.nasa.gov/api/map_key/).
#   cp backend/.env.example backend/.env   lalu isi FIRMS_MAP_KEY (ter-ignore git). Tanpa kunci, hanya kartu Hotspot yang nonaktif.
```
Frontend memuat 3D Tiles dari `frontend/public/tiles/` (data, tidak ada di repo): tanpa data itu peta tampil tetapi tanpa bangunan. Cara mengisinya ada di tabel di bawah.
Konfigurasi basis data pipeline: salin `data-pipeline/.env.example` ke `data-pipeline/.env` (di-ignore git) dan isi sandi acak; **jangan commit `.env`**.

## Data yang tidak ada di repo dan cara mendapatkannya
Semua folder ini di-ignore git; tiap folder punya `README.md` berisi isi, asal, struktur, cara membuat ulang, cara memeriksa keutuhan, dan aturannya.

| Lokasi | Isi | Ukuran | Cara mendapatkan | Panduan |
|---|---|---|---|---|
| `data-pipeline/raw/citygml/` | CityGML 15 kelurahan (31 `.gml`, 51.888 bangunan; **sumber tunggal**) | 3,5 GB | **Minta salinan dari pemilik proyek** (penyedia asli belum dicatat); periksa dengan `reports/hash_baseline_raw_citygml.txt` | [README](data-pipeline/raw/citygml/README.md) |
| `data-pipeline/raw/geojson/` | Batas kelurahan, RT, dan sungai | 2,8 MB | Minta salinan dari pemilik (asal belum dicatat) | [README](data-pipeline/raw/geojson/README.md) |
| `data-pipeline/raw/remote/` | Respons mentah WFS/CSW geoportal | 22 MB | `fetch_sources.py` (jaringan, hanya baca) | [README](data-pipeline/raw/remote/README.md) |
| `data-pipeline/backups/` | `pg_dump` PostGIS (data per bangunan, ID resmi) | 283 MB | Dibuat `db.sh dump`; **minta salinan dari pemilik** bila tidak ada | [README](data-pipeline/backups/README.md) |
| `data-pipeline/processed/buildings/` | CityJSONSeq per kelurahan | 109 MB | `ekspor.py --slug <slug>` dari PostGIS | [README](data-pipeline/processed/buildings/README.md) |
| `data-pipeline/processed/3dtiles/` | 3D Tiles 15 kelurahan + master | 74 MB | `buat_tile.py --slug <slug>` lalu `04_build_master.py` | [README](data-pipeline/processed/3dtiles/README.md) |
| `data-pipeline/processed/geojson/` | GeoJSON ternormalisasi | 2,8 MB | `normalize_names.py`, `reproject_sungai.py` | [README](data-pipeline/processed/geojson/README.md) |
| `data-pipeline/processed/{sources,catalog,user_layers,analisis}/` | Layer per sumber, katalog CSW, layer pengguna, keluaran antara | ±26 MB | `fetch_sources.py`; backend; skrip verifikasi | [README](data-pipeline/processed/README.md) |
| `frontend/public/tiles/` | Salinan dev 3D Tiles | 74 MB | `04_build_master.py --sync` | [README](frontend/public/tiles/README.md) |
| `frontend/public/geojson/` | Salinan dev GeoJSON | 2,8 MB | `sync_geojson.py` | [README](frontend/public/geojson/README.md) |
| `data-pipeline/.env` | Kredensial PostGIS dev | — | Salin dari `.env.example`, isi sandi acak | [pipeline README](data-pipeline/README.md) |

**Bukan untuk dipublikasikan bila repo dibuka:** `data-pipeline/config/registri_id.csv` (koordinat tiap bangunan), laporan per bangunan di `data-pipeline/reports/` (`impor_resmi_*`, `citygml_inventory.*`, `uji_tampil_*/log_*.json`), dan `config/keputusan_duplikat.yaml` (ID/koordinat bangunan, nama operator pembuat data).
