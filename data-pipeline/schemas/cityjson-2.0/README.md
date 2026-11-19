# Skema CityJSON 2.0 (salinan lokal untuk validasi pipeline)

| | |
|---|---|
| Versi | CityJSON **2.0.2** (tag `2.0.2`, commit `877ee49e16c82a4bc7ab598926efcb9ba1075374`) |
| Sumber | https://github.com/cityjson/specs (repositori spesifikasi resmi yang ditautkan dari https://www.cityjson.org/schemas/), folder `schemas/`, berkas `*.min.schema.json` (mandiri, tanpa `$ref` eksternal) |
| Alasan bukan dari host biasa | Indeks https://www.cityjson.org/schemas/ menautkan ke `3d.bk.tudelft.nl/schemas/cityjson/`, yang timeout saat diunduh (2026-11-20); isi yang sama diambil dari repositori GitHub yang sama pada tag `2.0.2`. |
| Diunduh | 2026-11-20, sekali; tidak diunduh ulang saat validasi |
| Lisensi | CC0 1.0 Universal (berkas `LICENSE` di folder ini, salinan dari repositori `cityjson/specs`) |
| Draft JSON Schema | draft-07 |

| Berkas | SHA-256 |
|---|---|
| `cityjson.min.schema.json` | `74e128f4505429775fb97da4132a06e2fb3b88116332d7f6893529841fb3505e` |
| `cityjsonfeature.min.schema.json` | `7374a31db91c1ddb59d3021573932739eeb3c8c96f737c2c2f9ed1fc69e1dd0a` |
| `LICENSE` | `a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499` |

Dipakai oleh `data-pipeline/scripts/citygml/validasi_cityjson.py` (paket `jsonschema`): baris pertama CityJSONSeq divalidasi
dengan `cityjson.min.schema.json`, baris berikutnya dengan `cityjsonfeature.min.schema.json`.
Mengganti versi = ganti kedua berkas, perbarui tabel ini, dan jalankan ulang validasi.
