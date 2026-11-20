# Verifikasi impor resmi dan tile v2 (seluruh kota)

Dihasilkan oleh `scripts/citygml/laporan_verifikasi.py`; angka lengkap di `impor_resmi_verifikasi.json`.

## Tabel per kelurahan

| Kelurahan | Sumber (staging) | Duplikat dikecualikan | PostGIS | < 0,1 m (tidak masuk tile) | Diharapkan di tile | Fitur v2 | Fitur tile lama | v2 − lama |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| api_api | 5.142 | 1 | 5.141 | 4 | 5.137 | 5.137 | 5.142 | -5 |
| belimbing | 4.645 | 0 | 4.645 | 1 | 4.644 | 4.644 | 3.296 | +1.348 |
| berebas_pantai | 2.022 | 2 | 2.020 | 5 | 2.015 | 2.015 | 2.024 | -9 |
| berebas_tengah | 3.390 | 0 | 3.390 | 4 | 3.386 | 3.386 | 3.390 | -4 |
| bontang_baru | 4.147 | 3 | 4.144 | 6 | 4.138 | 4.138 | 4.147 | -9 |
| bontang_kuala | 2.366 | 0 | 2.366 | 0 | 2.366 | 2.366 | 2.366 | +0 |
| bontang_lestari | 2.219 | 0 | 2.219 | 4 | 2.215 | 2.215 | 774 | +1.441 |
| guntung | 2.059 | 8 | 2.051 | 0 | 2.051 | 2.051 | 2.057 | -6 |
| gunung_elai | 4.469 | 1 | 4.468 | 6 | 4.462 | 4.462 | 2.571 | +1.891 |
| gunung_telihan | 3.989 | 0 | 3.989 | 10 | 3.979 | 3.979 | 3.989 | -10 |
| kanaan | 1.837 | 0 | 1.837 | 3 | 1.834 | 1.834 | 1.834 | +0 |
| loktuan | 5.010 | 0 | 5.010 | 5 | 5.005 | 5.005 | 4.923 | +82 |
| satimpo | 2.502 | 0 | 2.502 | 1 | 2.501 | 2.501 | 2.504 | -3 |
| tanjung_laut | 4.340 | 0 | 4.340 | 7 | 4.333 | 4.333 | 4.340 | -7 |
| tanjung_laut_indah | 3.751 | 0 | 3.751 | 1 | 3.750 | 3.750 | 3.751 | -1 |
| **Total** | **51.888** | **15** | **51.873** | **57** | **51.816** | **51.816** | **47.108** | **+4.708** |

Alasan dikeluarkan dari tile: `tinggi < 0,1 m` (qc_flag `tinggi_kurang_0_1m`; tetap di PostGIS). Duplikat dikecualikan: ADR-007 (tidak mendapat ID).

## Segitiga

- Total v2 **5.033.543**; tile lama **9.338.212**.
- Pada **46.911** bangunan yang cocok satu-ke-satu (pusat ≤ 2 m, timbal balik): lama 9.293.658 vs v2 4.572.155 = **2.03×**.

## Kontrak frontend

| Kelurahan | 3D Tiles | region | transform | refine | glb | maks glb (MB) | ≤ 3 MB | EXT_* di semua glb | 6 properti | ID unik | ID = PostGIS | atribut beda |
|---|---|---|---|---|---:|---:|---|---|---|---|---|---:|
| api_api | 1.1 | ya | ya | REPLACE | 19 | 1.14 | ya | ya | ya | ya | ya | 0 |
| belimbing | 1.1 | ya | ya | REPLACE | 15 | 1.16 | ya | ya | ya | ya | ya | 0 |
| berebas_pantai | 1.1 | ya | ya | REPLACE | 4 | 1.08 | ya | ya | ya | ya | ya | 0 |
| berebas_tengah | 1.1 | ya | ya | REPLACE | 7 | 1.24 | ya | ya | ya | ya | ya | 0 |
| bontang_baru | 1.1 | ya | ya | REPLACE | 15 | 1.20 | ya | ya | ya | ya | ya | 0 |
| bontang_kuala | 1.1 | ya | ya | REPLACE | 3 | 1.10 | ya | ya | ya | ya | ya | 0 |
| bontang_lestari | 1.1 | ya | ya | REPLACE | 4 | 0.75 | ya | ya | ya | ya | ya | 0 |
| guntung | 1.1 | ya | ya | REPLACE | 7 | 0.89 | ya | ya | ya | ya | ya | 0 |
| gunung_elai | 1.1 | ya | ya | REPLACE | 14 | 0.95 | ya | ya | ya | ya | ya | 0 |
| gunung_telihan | 1.1 | ya | ya | REPLACE | 7 | 1.26 | ya | ya | ya | ya | ya | 0 |
| kanaan | 1.1 | ya | ya | REPLACE | 6 | 0.76 | ya | ya | ya | ya | ya | 0 |
| loktuan | 1.1 | ya | ya | REPLACE | 12 | 1.17 | ya | ya | ya | ya | ya | 0 |
| satimpo | 1.1 | ya | ya | REPLACE | 10 | 1.00 | ya | ya | ya | ya | ya | 0 |
| tanjung_laut | 1.1 | ya | ya | REPLACE | 12 | 1.08 | ya | ya | ya | ya | ya | 0 |
| tanjung_laut_indah | 1.1 | ya | ya | REPLACE | 4 | 1.27 | ya | ya | ya | ya | ya | 0 |

- ID unik seluruh kota: 51.816 dari 51.816 fitur (ganda 0); himpunan ID tile = PostGIS (tinggi ≥ 0,1 m): True.
- `jumlah_lantai`/`luas_tapak` kosong disimpan sebagai `noData` (bukan 0). tyler menghilangkan kolom dari tile yang tidak punya satu pun nilai (mis. 6 dari 7 tile Berebas Tengah tanpa `jumlah_lantai`).

## qc_flag seluruh kota (core.bangunan)

| Flag | Bangunan |
|---|---:|
| z_dasar_tidak_nol_di_sumber | 10.745 |
| epsg_dikoreksi | 4.335 |
| gml_id_bentrok | 207 |
| footprint_kurang_2m2 | 205 |
| footprint_diperbaiki | 86 |
| tanpa_footprint | 73 |
| tinggi_kurang_0_1m | 57 |
| kelurahan_beda_dengan_sumber | 30 |
| tanpa_atap | 29 |
| footprint_mikro | 22 |
| tinggi_sumber_nol | 22 |
| tinggi_lebih_40m | 9 |
| atribut_dari_duplikat | 2 |
| duplikat_kepercayaan_rendah | 2 |
