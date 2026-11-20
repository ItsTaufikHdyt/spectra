# Validasi skema CityJSON 2.0.2 — impor resmi (2026-11-20)

`scripts/citygml/validasi_cityjson.py` pada `processed/buildings/<slug>.city.jsonl` (skema lokal `schemas/cityjson-2.0/`).

| Kelurahan | Fitur | Galat skema | Peringatan: titik berulang berurutan |
|---|---:|---:|---:|
| api_api | 5.137 | 0 | 588 |
| belimbing | 4.644 | 0 | 235 |
| berebas_pantai | 2.015 | 0 | 597 |
| berebas_tengah | 3.386 | 0 | 447 |
| bontang_baru | 4.138 | 0 | 660 |
| bontang_kuala | 2.366 | 0 | 134 |
| bontang_lestari | 2.215 | 0 | 15 |
| guntung | 2.051 | 0 | 59 |
| gunung_elai | 4.462 | 0 | 433 |
| gunung_telihan | 3.979 | 0 | 299 |
| kanaan | 1.834 | 0 | 495 |
| loktuan | 5.005 | 0 | 525 |
| satimpo | 2.501 | 0 | 406 |
| tanjung_laut | 4.333 | 0 | 775 |
| tanjung_laut_indah | 3.750 | 0 | 923 |
| **Total** | **51.816** | **0** | **6.591** |

Peringatan lain yang dihitung (vertex tidak dipakai, vertex kembar dalam fitur, cincin < 3 titik): **0** di semua kelurahan. Titik berulang berurutan berasal dari pembulatan koordinat ke 1 mm; tidak melanggar skema. Validasi geometri (solid/`ST_IsValid`) belum dilakukan (hutang STATUS).
