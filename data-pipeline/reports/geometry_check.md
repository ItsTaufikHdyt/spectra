# Laporan QC Geometri — batas kelurahan, batas RT, sungai

Dibuat oleh `data-pipeline/scripts/check_geometry.py` (read-only terhadap `raw/`).
Hitungan metrik di EPSG:32650 (UTM 50N); luas kelurahan juga geodesik WGS84.

## 1. Validitas geometri

| file | fitur | tidak valid | ring tidak tertutup | per jenis |
|---|---|---|---|---|
| batas-kelurahan.json | 15 | 1 | 0 | {'Ring Self-intersection': 1} |
| batas-rt.json | 526 | 20 | 0 | {'Ring Self-intersection': 11, 'Self-intersection': 9} |
| sungai_ln_5k.json | 5 | 0 | 0 | - |

**batas-kelurahan.json** — geometri bermasalah:

| index | label | jenis | alasan |
|---|---|---|---|
| 13 | Berbas Pantai | Ring Self-intersection | Ring Self-intersection[117.48411931 0.11269972] |

**batas-rt.json** — geometri bermasalah:

| index | label | jenis | alasan |
|---|---|---|---|
| 2 | API-API RT 042 | Ring Self-intersection | Ring Self-intersection[117.49777852 0.1237051] |
| 12 | API-API RT 005 | Self-intersection | Self-intersection[117.48694619 0.12987039] |
| 23 | API-API RT 024 | Ring Self-intersection | Ring Self-intersection[117.49182925 0.13430453] |
| 26 | API-API RT 009 | Self-intersection | Self-intersection[117.48694619 0.12987039] |
| 72 | BELIMBING RT 027 | Self-intersection | Self-intersection[117.47186883 0.14885565] |
| 101 | BERBAS PANTAI RT 015 | Ring Self-intersection | Ring Self-intersection[117.48697138 0.10898215] |
| 106 | BERBAS PANTAI RT 001 | Ring Self-intersection | Ring Self-intersection[117.47964883 0.11265499] |
| 107 | BERBAS PANTAI RT 003 | Ring Self-intersection | Ring Self-intersection[117.48411788 0.11269939] |
| 116 | BERBAS PANTAI RT 014 | Self-intersection | Self-intersection[117.485798837352 0.110277793947728] |
| 134 | BEREBAS TENGAH RT 062 | Self-intersection | Self-intersection[117.47964883 0.11265499] |
| 156 | BEREBAS TENGAH RT 046 | Ring Self-intersection | Ring Self-intersection[117.47740072 0.11599402] |
| 178 | BEREBAS TENGAH RT 037 | Self-intersection | Self-intersection[117.47546864 0.11774691] |
| 260 | GUNTUNG RT 014 | Self-intersection | Self-intersection[117.484690040262 0.168800189808901] |
| 283 | GUNTUNG RT 018 | Ring Self-intersection | Ring Self-intersection[117.47821675 0.17304223] |
| 330 | GUNUNG TELIHAN RT 005 | Self-intersection | Self-intersection[117.46459542 0.13792351] |
| 403 | LOKTUAN RT 046 | Ring Self-intersection | Ring Self-intersection[117.47518572 0.17367147] |
| 414 | LOKTUAN RT 026 | Self-intersection | Self-intersection[117.48474338 0.16889155] |
| 439 | SATIMPO RT 025 | Ring Self-intersection | Ring Self-intersection[117.48062158 0.12855509] |
| 444 | SATIMPO RT 021 | Ring Self-intersection | Ring Self-intersection[117.47209533 0.12997893] |
| 517 | TANJUNG LAUT INDAH RT 023 | Ring Self-intersection | Ring Self-intersection[117.49167367 0.12280445] |

## 2. Tumpang tindih RT dalam kelurahan yang sama (> 0.1 m²): 20 pasangan

| a | b | luas_irisan_m2 | persen_dari_rt_terkecil |
|---|---|---|---|
| BELIMBING RT 003 (#42) | BELIMBING RT 034 (#78) | 0.4 | 0.0 |
| BELIMBING RT 015 (#51) | BELIMBING RT 037 (#52) | 18.33 | 0.15 |
| BELIMBING RT 039 (#53) | BELIMBING RT 030 (#64) | 0.33 | 0.0 |
| BELIMBING RT 027 (#72) | BELIMBING RT 032 (#76) | 3.12 | 0.02 |
| BERBAS PANTAI RT 008 (#93) | BERBAS PANTAI RT 006 (#115) | 3.55 | 0.04 |
| BERBAS PANTAI RT 012 (#109) | BERBAS PANTAI RT 010 (#113) | 0.12 | 0.0 |
| BERBAS PANTAI RT 012 (#109) | BERBAS PANTAI RT 014 (#116) | 0.12 | 0.0 |
| BERBAS PANTAI RT 010 (#113) | BERBAS PANTAI RT 014 (#116) | 0.12 | 0.0 |
| BEREBAS TENGAH RT 035 (#127) | BEREBAS TENGAH RT 032 (#138) | 2.44 | 0.02 |
| BEREBAS TENGAH RT 003 (#129) | BEREBAS TENGAH RT 004 (#130) | 0.19 | 0.01 |
| BEREBAS TENGAH RT 024 (#144) | BEREBAS TENGAH RT 055 (#170) | 1.6 | 0.01 |
| BONTANG BARU RT 028 (#200) | BONTANG BARU RT 007 (#202) | 10.31 | 0.02 |
| GUNTUNG RT 004 (#276) | GUNTUNG RT 002 (#281) | 0.33 | 0.0 |
| GUNUNG ELAI RT 032 (#285) | GUNUNG ELAI RT 036 (#289) | 15.3 | 0.05 |
| GUNUNG ELAI RT 015 (#317) | GUNUNG ELAI RT 017 (#319) | 1.17 | 0.01 |
| LOKTUAN RT 046 (#403) | LOKTUAN RT 045 (#408) | 0.34 | 0.0 |
| LOKTUAN RT 039 (#422) | LOKTUAN RT 037 (#423) | 0.15 | 0.0 |
| LOKTUAN RT 039 (#422) | LOKTUAN RT 038 (#424) | 0.24 | 0.0 |
| TANJUNG LAUT INDAH RT 033 (#501) | TANJUNG LAUT INDAH RT 016 (#508) | 5.78 | 0.02 |
| TANJUNG LAUT INDAH RT 014 (#507) | TANJUNG LAUT INDAH RT 016 (#508) | 3.77 | 0.0 |

## 3. Tumpang tindih RT antar kelurahan (> 0.1 m²): 24 pasangan

| a | b | luas_irisan_m2 | persen_dari_rt_terkecil |
|---|---|---|---|
| API-API RT 032 (#1) | BONTANG KUALA RT 016 (#207) | 0.32 | 0.0 |
| API-API RT 018 (#4) | TANJUNG LAUT RT 036 (#454) | 2.76 | 0.02 |
| API-API RT 017 (#5) | TANJUNG LAUT RT 036 (#454) | 0.25 | 0.0 |
| API-API RT 001 (#7) | TANJUNG LAUT RT 003 (#462) | 0.16 | 0.0 |
| API-API RT 026 (#17) | BONTANG BARU RT 002 (#204) | 0.29 | 0.0 |
| BELIMBING RT 027 (#72) | GUNUNG ELAI RT 032 (#285) | 0.7 | 0.0 |
| BELIMBING RT 006 (#80) | GUNUNG TELIHAN RT 006 (#342) | 0.15 | 0.0 |
| BELIMBING RT 044 (#89) | GUNUNG ELAI RT 021 (#326) | 0.88 | 0.0 |
| BERBAS PANTAI RT 001 (#106) | BEREBAS TENGAH RT 036 (#126) | 0.32 | 0.0 |
| BERBAS PANTAI RT 003 (#107) | BEREBAS TENGAH RT 036 (#126) | 1.02 | 0.0 |
| BEREBAS TENGAH RT 005 (#128) | SATIMPO RT 010 (#451) | 0.13 | 0.0 |
| BEREBAS TENGAH RT 045 (#158) | SATIMPO RT 010 (#451) | 0.33 | 0.0 |
| BEREBAS TENGAH RT 042 (#159) | SATIMPO RT 010 (#451) | 0.1 | 0.0 |
| BEREBAS TENGAH RT 039 (#167) | SATIMPO RT 010 (#451) | 0.31 | 0.0 |
| BEREBAS TENGAH RT 038 (#177) | SATIMPO RT 010 (#451) | 0.53 | 0.01 |
| BONTANG BARU RT 022 (#186) | GUNUNG ELAI RT 004 (#303) | 0.15 | 0.0 |
| BONTANG BARU RT 021 (#190) | GUNUNG ELAI RT 004 (#303) | 0.61 | 0.0 |
| GUNTUNG RT 014 (#260) | LOKTUAN RT 048 (#404) | 6.34 | 0.01 |
| GUNUNG ELAI RT 020 (#321) | SATIMPO RT 021 (#444) | 1.19 | 0.0 |
| KANAAN RT 011 (#362) | SATIMPO RT 021 (#444) | 0.2 | 0.0 |
| KANAAN RT 008 (#368) | SATIMPO RT 021 (#444) | 2.05 | 0.0 |
| SATIMPO RT 010 (#451) | TANJUNG LAUT RT 017 (#485) | 0.5 | 0.01 |
| SATIMPO RT 010 (#451) | TANJUNG LAUT RT 016 (#486) | 1.18 | 0.01 |
| TANJUNG LAUT RT 032 (#455) | TANJUNG LAUT INDAH RT 006 (#490) | 0.18 | 0.0 |

## 4. RT di dalam kelurahan induk

- Dicek: 526 RT; keluar induk (< 99% luas di dalam): **0 (0.0%)**; tanpa induk: 0.

_(tidak ada)_

## 5. RT duplikat: 10 grup (kelurahan, RT), 68 pasangan

Status per pasangan: beririsan (irisan > 0.1 m²), berdampingan (jarak ≤ 1 m), terpisah.

### Ringkasan per grup

| kelurahan | rt | jumlah_poligon | jumlah_pasangan | keterangan | status | jarak_min_m | jarak_maks_m |
|---|---|---|---|---|---|---|---|
| BONTANG KUALA | 013 | 7 | 21 | Pulau Badak-Badak Timur / Pulau Badak-Badak Barat / No Name / Pulau Segajah / No Name / No Name / Bontang Kuala | terpisah 21 | 52.4 | 4822.5 |
| BONTANG KUALA | 018 | 5 | 10 | Pulau Agar-Agar / No Name / No Name / No Name / Bontang Kuala | terpisah 10 | 63.7 | 1290.9 |
| BONTANG LESTARI | 013 | 2 | 1 | Pulau Siacca / Bontang Lestari | terpisah 1 | 172.9 | 172.9 |
| BONTANG LESTARI | 016 | 2 | 1 | Pulau Panjang / Selangan | terpisah 1 | 299.0 | 299.0 |
| BONTANG LESTARI | 017 | 3 | 3 | Tihi-Tihi / Pulau Tihi-Tihi / Pulau Beras Basah | berdampingan 1, terpisah 2 | 0.0 | 3315.6 |
| GUNTUNG | 003 | 7 | 21 | Pulau Karangkiampau / Pulau Gusung / Pulau Selokia Dalam / Gusung / No Name / No Name / Pulau Selokia Luar | terpisah 21 | 7.2 | 2625.4 |
| LOKTUAN | 003 | 2 | 1 | (kosong) / (kosong) | terpisah 1 | 28.7 | 28.7 |
| LOKTUAN | 004 | 2 | 1 | (kosong) / (kosong) | terpisah 1 | 21.4 | 21.4 |
| SATIMPO | 004 | 3 | 3 | Satimpo / Pulau Kedindingan / Pulau Kedindingan | terpisah 3 | 187.4 | 6364.5 |
| TANJUNG LAUT INDAH | 030 | 4 | 6 | Pulau Melahing / Pulau Melahing / Melahing / No Name | terpisah 6 | 53.2 | 2880.1 |

### Rincian per pasangan

| kelurahan | rt | index_a | index_b | keterangan_a | keterangan_b | status | luas_irisan_m2 | jarak_m | jarak_centroid_m |
|---|---|---|---|---|---|---|---|---|---|
| BONTANG KUALA | 013 | 209 | 210 | Pulau Badak-Badak Timur | Pulau Badak-Badak Barat | terpisah | 0.0 | 275.2 | 780.4 |
| BONTANG KUALA | 013 | 209 | 211 | Pulau Badak-Badak Timur | No Name | terpisah | 0.0 | 1969.5 | 2294.4 |
| BONTANG KUALA | 013 | 209 | 212 | Pulau Badak-Badak Timur | Pulau Segajah | terpisah | 0.0 | 4817.2 | 5084.2 |
| BONTANG KUALA | 013 | 209 | 216 | Pulau Badak-Badak Timur | No Name | terpisah | 0.0 | 911.7 | 1121.0 |
| BONTANG KUALA | 013 | 209 | 217 | Pulau Badak-Badak Timur | No Name | terpisah | 0.0 | 868.2 | 1091.8 |
| BONTANG KUALA | 013 | 209 | 229 | Pulau Badak-Badak Timur | Bontang Kuala | terpisah | 0.0 | 52.4 | 1015.9 |
| BONTANG KUALA | 013 | 210 | 211 | Pulau Badak-Badak Barat | No Name | terpisah | 0.0 | 1498.6 | 1933.9 |
| BONTANG KUALA | 013 | 210 | 212 | Pulau Badak-Badak Barat | Pulau Segajah | terpisah | 0.0 | 3981.8 | 4305.9 |
| BONTANG KUALA | 013 | 210 | 216 | Pulau Badak-Badak Barat | No Name | terpisah | 0.0 | 225.6 | 522.4 |
| BONTANG KUALA | 013 | 210 | 217 | Pulau Badak-Badak Barat | No Name | terpisah | 0.0 | 84.6 | 423.5 |
| BONTANG KUALA | 013 | 210 | 229 | Pulau Badak-Badak Barat | Bontang Kuala | terpisah | 0.0 | 742.0 | 1740.1 |
| BONTANG KUALA | 013 | 211 | 212 | No Name | Pulau Segajah | terpisah | 0.0 | 3687.8 | 3995.2 |
| BONTANG KUALA | 013 | 211 | 216 | No Name | No Name | terpisah | 0.0 | 1235.6 | 1421.8 |
| BONTANG KUALA | 013 | 211 | 217 | No Name | No Name | terpisah | 0.0 | 1338.5 | 1542.8 |
| BONTANG KUALA | 013 | 211 | 229 | No Name | Bontang Kuala | terpisah | 0.0 | 2036.4 | 3246.7 |
| BONTANG KUALA | 013 | 212 | 216 | Pulau Segajah | No Name | terpisah | 0.0 | 3983.3 | 4053.4 |
| BONTANG KUALA | 013 | 212 | 217 | Pulau Segajah | No Name | terpisah | 0.0 | 3963.3 | 4033.1 |
| BONTANG KUALA | 013 | 212 | 229 | Pulau Segajah | Bontang Kuala | terpisah | 0.0 | 4822.5 | 6019.8 |
| BONTANG KUALA | 013 | 216 | 217 | No Name | No Name | terpisah | 0.0 | 69.6 | 130.0 |
| BONTANG KUALA | 013 | 216 | 229 | No Name | Bontang Kuala | terpisah | 0.0 | 1357.4 | 2135.2 |
| BONTANG KUALA | 013 | 217 | 229 | No Name | Bontang Kuala | terpisah | 0.0 | 1323.6 | 2097.8 |
| BONTANG KUALA | 018 | 208 | 213 | Pulau Agar-Agar | No Name | terpisah | 0.0 | 227.1 | 569.2 |
| BONTANG KUALA | 018 | 208 | 214 | Pulau Agar-Agar | No Name | terpisah | 0.0 | 63.7 | 390.9 |
| BONTANG KUALA | 018 | 208 | 215 | Pulau Agar-Agar | No Name | terpisah | 0.0 | 852.8 | 1079.2 |
| BONTANG KUALA | 018 | 208 | 236 | Pulau Agar-Agar | Bontang Kuala | terpisah | 0.0 | 688.6 | 1874.3 |
| BONTANG KUALA | 018 | 213 | 214 | No Name | No Name | terpisah | 0.0 | 794.2 | 938.6 |
| BONTANG KUALA | 018 | 213 | 215 | No Name | No Name | terpisah | 0.0 | 805.1 | 873.2 |
| BONTANG KUALA | 018 | 213 | 236 | No Name | Bontang Kuala | terpisah | 0.0 | 367.3 | 1318.9 |
| BONTANG KUALA | 018 | 214 | 215 | No Name | No Name | terpisah | 0.0 | 1290.9 | 1433.6 |
| BONTANG KUALA | 018 | 214 | 236 | No Name | Bontang Kuala | terpisah | 0.0 | 1270.1 | 2205.0 |
| BONTANG KUALA | 018 | 215 | 236 | No Name | Bontang Kuala | terpisah | 0.0 | 390.8 | 1710.1 |
| BONTANG LESTARI | 013 | 242 | 254 | Pulau Siacca | Bontang Lestari | terpisah | 0.0 | 172.9 | 2654.3 |
| BONTANG LESTARI | 016 | 240 | 241 | Pulau Panjang | Selangan | terpisah | 0.0 | 299.0 | 1076.8 |
| BONTANG LESTARI | 017 | 238 | 239 | Tihi-Tihi | Pulau Tihi-Tihi | berdampingan | 0.0 | 0.0 | 206.8 |
| BONTANG LESTARI | 017 | 238 | 243 | Tihi-Tihi | Pulau Beras Basah | terpisah | 0.0 | 3110.3 | 3377.3 |
| BONTANG LESTARI | 017 | 239 | 243 | Pulau Tihi-Tihi | Pulau Beras Basah | terpisah | 0.0 | 3315.6 | 3519.6 |
| GUNTUNG | 003 | 261 | 262 | Pulau Karangkiampau | Pulau Gusung | terpisah | 0.0 | 1777.9 | 1911.1 |
| GUNTUNG | 003 | 261 | 263 | Pulau Karangkiampau | Pulau Selokia Dalam | terpisah | 0.0 | 1624.7 | 1774.2 |
| GUNTUNG | 003 | 261 | 264 | Pulau Karangkiampau | Gusung | terpisah | 0.0 | 1338.2 | 1553.3 |
| GUNTUNG | 003 | 261 | 265 | Pulau Karangkiampau | No Name | terpisah | 0.0 | 1139.9 | 1256.3 |
| GUNTUNG | 003 | 261 | 266 | Pulau Karangkiampau | No Name | terpisah | 0.0 | 818.0 | 1092.4 |
| GUNTUNG | 003 | 261 | 267 | Pulau Karangkiampau | Pulau Selokia Luar | terpisah | 0.0 | 1186.0 | 1357.6 |
| GUNTUNG | 003 | 262 | 263 | Pulau Gusung | Pulau Selokia Dalam | terpisah | 0.0 | 7.2 | 161.7 |
| GUNTUNG | 003 | 262 | 264 | Pulau Gusung | Gusung | terpisah | 0.0 | 261.6 | 508.9 |
| GUNTUNG | 003 | 262 | 265 | Pulau Gusung | No Name | terpisah | 0.0 | 790.6 | 916.5 |
| GUNTUNG | 003 | 262 | 266 | Pulau Gusung | No Name | terpisah | 0.0 | 2625.4 | 2887.2 |
| GUNTUNG | 003 | 262 | 267 | Pulau Gusung | Pulau Selokia Luar | terpisah | 0.0 | 535.7 | 697.4 |
| GUNTUNG | 003 | 263 | 264 | Pulau Selokia Dalam | Gusung | terpisah | 0.0 | 66.6 | 349.9 |
| GUNTUNG | 003 | 263 | 265 | Pulau Selokia Dalam | No Name | terpisah | 0.0 | 585.9 | 755.0 |
| GUNTUNG | 003 | 263 | 266 | Pulau Selokia Dalam | No Name | terpisah | 0.0 | 2500.8 | 2770.8 |
| GUNTUNG | 003 | 263 | 267 | Pulau Selokia Dalam | Pulau Selokia Luar | terpisah | 0.0 | 467.6 | 635.9 |
| GUNTUNG | 003 | 264 | 265 | Gusung | No Name | terpisah | 0.0 | 215.3 | 413.6 |
| GUNTUNG | 003 | 264 | 266 | Gusung | No Name | terpisah | 0.0 | 2257.9 | 2601.7 |
| GUNTUNG | 003 | 264 | 267 | Gusung | Pulau Selokia Luar | terpisah | 0.0 | 558.6 | 710.0 |
| GUNTUNG | 003 | 265 | 266 | No Name | No Name | terpisah | 0.0 | 2084.2 | 2340.8 |
| GUNTUNG | 003 | 265 | 267 | No Name | Pulau Selokia Luar | terpisah | 0.0 | 752.6 | 878.0 |
| GUNTUNG | 003 | 266 | 267 | No Name | Pulau Selokia Luar | terpisah | 0.0 | 1966.1 | 2237.1 |
| LOKTUAN | 003 | 376 | 382 | None | None | terpisah | 0.0 | 28.7 | 240.4 |
| LOKTUAN | 004 | 372 | 375 | None | None | terpisah | 0.0 | 21.4 | 257.2 |
| SATIMPO | 004 | 425 | 426 | Satimpo | Pulau Kedindingan | terpisah | 0.0 | 4921.1 | 8500.2 |
| SATIMPO | 004 | 425 | 427 | Satimpo | Pulau Kedindingan | terpisah | 0.0 | 6364.5 | 9722.7 |
| SATIMPO | 004 | 426 | 427 | Pulau Kedindingan | Pulau Kedindingan | terpisah | 0.0 | 187.4 | 1475.2 |
| TANJUNG LAUT INDAH | 030 | 491 | 492 | Pulau Melahing | Pulau Melahing | terpisah | 0.0 | 53.2 | 263.3 |
| TANJUNG LAUT INDAH | 030 | 491 | 493 | Pulau Melahing | Melahing | terpisah | 0.0 | 821.8 | 987.4 |
| TANJUNG LAUT INDAH | 030 | 491 | 494 | Pulau Melahing | No Name | terpisah | 0.0 | 2494.5 | 2891.3 |
| TANJUNG LAUT INDAH | 030 | 492 | 493 | Pulau Melahing | Melahing | terpisah | 0.0 | 957.3 | 1126.4 |
| TANJUNG LAUT INDAH | 030 | 492 | 494 | Pulau Melahing | No Name | terpisah | 0.0 | 2310.2 | 2636.8 |
| TANJUNG LAUT INDAH | 030 | 493 | 494 | Melahing | No Name | terpisah | 0.0 | 2880.1 | 3234.2 |

## 6. Luas kelurahan & investigasi Guntung

| kelurahan | luaswh_ha | luas_utm_ha | luas_geodesik_ha | luas_gabungan_rt_ha | cakupan_rt_persen | selisih_persen_vs_utm | selisih_persen_vs_geodesik | jumlah_bagian | jumlah_hole |
|---|---|---|---|---|---|---|---|---|---|
| Guntung | 1109.87 | 1134.93 | 1135.75 | 1134.93 | 100.0 | -2.208 | -2.279 | 8 | 0 |
| Loktuan | 335.91 | 335.91 | 336.15 | 335.91 | 100.0 | 0.0 | -0.073 | 1 | 0 |
| Belimbing | 958.49 | 958.49 | 959.2 | 958.49 | 100.0 | 0.0 | -0.074 | 1 | 0 |
| Gunung Telihan | 228.89 | 228.89 | 229.06 | 228.89 | 100.0 | 0.0 | -0.074 | 1 | 0 |
| Gunung Elai | 501.5 | 501.5 | 501.86 | 501.5 | 100.0 | 0.0 | -0.073 | 1 | 0 |
| Kanaan | 603.31 | 603.31 | 603.76 | 603.31 | 100.0 | 0.0 | -0.074 | 1 | 0 |
| Bontang Baru | 221.57 | 221.57 | 221.73 | 221.57 | 100.0 | 0.0 | -0.073 | 1 | 0 |
| Api-Api | 216.09 | 216.09 | 216.24 | 216.08 | 100.0 | 0.0 | -0.073 | 1 | 0 |
| Tanjung Laut | 142.85 | 142.85 | 142.95 | 142.85 | 100.0 | 0.0 | -0.073 | 1 | 0 |
| Bontang Kuala | 894.67 | 894.67 | 895.31 | 894.67 | 100.0 | 0.0 | -0.072 | 11 | 0 |
| Tanjung Laut Indah | 252.11 | 252.11 | 252.29 | 252.11 | 100.0 | 0.0 | -0.072 | 5 | 0 |
| Satimpo | 1772.55 | 1772.55 | 1773.85 | 1772.55 | 100.0 | 0.0 | -0.073 | 3 | 0 |
| Berebas Tengah | 86.21 | 86.21 | 86.27 | 86.21 | 100.0 | 0.0 | -0.073 | 1 | 0 |
| Berbas Pantai | 56.24 | 56.24 | 56.28 | 56.24 | 100.0 | 0.0 | -0.073 | 1 | 0 |
| Bontang Lestari | 8782.41 | 8782.41 | 8788.91 | 8782.41 | 100.0 | 0.0 | -0.074 | 6 | 0 |

**luaswh = luas planar UTM 50N untuk 14 dari 15 kelurahan (selisih < 0,01%); selisih ~-0,07% terhadap geodesik hanyalah faktor skala UTM.** Tidak sama dengan UTM: ['Guntung'].

### Guntung: luaswh = 1109.872 ha, luas bagian kecil (selain bagian terbesar) = 12.53 ha

| luas_utm_ha | luas_geodesik_ha | jumlah_hole | luas_hole_ha |
|---|---|---|---|
| 1122.401 | 1123.217 | 0 | 0.0 |
| 3.88 | 3.883 | 0 | 0.0 |
| 2.406 | 2.408 | 0 | 0.0 |
| 1.463 | 1.464 | 0 | 0.0 |
| 1.444 | 1.445 | 0 | 0.0 |
| 1.286 | 1.287 | 0 | 0.0 |
| 1.273 | 1.274 | 0 | 0.0 |
| 0.778 | 0.778 | 0 | 0.0 |

Hipotesis (urut dari yang paling dekat dengan luaswh):

| hipotesis | luas_ha | selisih_dengan_luaswh_persen |
|---|---|---|
| hanya_bagian_terbesar_utm | 1122.401 | -1.116 |
| seluruh_geometri_utm | 1134.931 | -2.208 |
| seluruh_geometri_tanpa_mengurangi_hole_utm | 1134.931 | -2.208 |
| gabungan_poligon_rt_utm | 1134.93 | -2.208 |
| seluruh_geometri_geodesik | 1135.755 | -2.279 |

## 7. Atribut `luas` RT vs luas geometri (UTM)

- 144 dari 526 RT berbeda > 1%; selisih maksimum 40.73%.
- Cakupan gabungan RT terhadap poligon kelurahan: 100.0–100.0% (lihat bagian 6), jadi poligon kelurahan praktis = gabungan RT. Atribut `luas` RT kemungkinan berasal dari versi batas sebelumnya.

25 selisih terbesar:

| index | kelurahan | rt | luas_atribut_ha | luas_geometri_ha | selisih_persen |
|---|---|---|---|---|---|
| 107 | BERBAS PANTAI | 003 | 3.631 | 2.58 | 40.73 |
| 126 | BEREBAS TENGAH | 036 | 2.172 | 3.146 | -30.96 |
| 516 | TANJUNG LAUT INDAH | 022 | 1.874 | 1.715 | 9.28 |
| 400 | LOKTUAN | 051 | 3.341 | 3.659 | -8.71 |
| 419 | LOKTUAN | 032 | 1.003 | 1.098 | -8.66 |
| 116 | BERBAS PANTAI | 014 | 0.69 | 0.647 | 6.68 |
| 95 | BERBAS PANTAI | 017 | 1.004 | 0.941 | 6.62 |
| 283 | GUNTUNG | 018 | 2.77 | 2.598 | 6.62 |
| 515 | TANJUNG LAUT INDAH | 025 | 1.667 | 1.772 | -5.89 |
| 304 | GUNUNG ELAI | 005 | 2.191 | 2.076 | 5.56 |
| 142 | BEREBAS TENGAH | 058 | 1.505 | 1.591 | -5.38 |
| 164 | BEREBAS TENGAH | 041 | 0.608 | 0.577 | 5.35 |
| 503 | TANJUNG LAUT INDAH | 019 | 2.137 | 2.033 | 5.1 |
| 139 | BEREBAS TENGAH | 031 | 0.817 | 0.778 | 4.98 |
| 517 | TANJUNG LAUT INDAH | 023 | 1.627 | 1.55 | 4.97 |
| 76 | BELIMBING | 032 | 1.238 | 1.302 | -4.92 |
| 69 | BELIMBING | 028 | 1.185 | 1.247 | -4.91 |
| 115 | BERBAS PANTAI | 006 | 1.496 | 1.57 | -4.72 |
| 398 | LOKTUAN | 050 | 3.344 | 3.507 | -4.66 |
| 167 | BEREBAS TENGAH | 039 | 0.632 | 0.663 | -4.6 |
| 360 | KANAAN | 010 | 3.334 | 3.195 | 4.36 |
| 191 | BONTANG BARU | 016 | 2.29 | 2.393 | -4.31 |
| 114 | BERBAS PANTAI | 009 | 0.875 | 0.914 | -4.24 |
| 424 | LOKTUAN | 038 | 0.893 | 0.932 | -4.14 |
| 206 | BONTANG BARU | 004 | 2.644 | 2.539 | 4.13 |

## Bukti status pulau (jarak RT ke daratan utama)

Daratan utama = bagian terbesar dari gabungan seluruh RT. Jarak 0 = menyatu dengan daratan.

| keterangan | jumlah_rt | rt_terpisah_dari_daratan | jarak_min_m | jarak_maks_m |
|---|---|---|---|---|
| (kosong) | 386 | 0 | 0.0 | 0.0 |
| Bontang Kuala | 20 | 0 | 0.0 | 0.0 |
| Bontang Lestari | 17 | 0 | 0.0 | 0.0 |
| Guntung | 17 | 0 | 0.0 | 0.0 |
| Gusung | 1 | 1 | 123.0 | 123.0 |
| Melahing | 1 | 1 | 1370.7 | 1370.7 |
| No Name | 9 | 9 | 367.3 | 3798.5 |
| Pulau Agar-Agar | 1 | 1 | 688.6 | 688.6 |
| Pulau Badak-Badak Barat | 1 | 1 | 742.0 | 742.0 |
| Pulau Badak-Badak Timur | 1 | 1 | 52.4 | 52.4 |
| Pulau Beras Basah | 1 | 1 | 4865.9 | 4865.9 |
| Pulau Gusung | 1 | 1 | 256.9 | 256.9 |
| Pulau Karangkiampau | 1 | 1 | 1484.1 | 1484.1 |
| Pulau Kedindingan | 2 | 2 | 4236.7 | 5500.7 |
| Pulau Melahing | 2 | 2 | 2343.2 | 2466.7 |
| Pulau Panjang | 1 | 1 | 313.4 | 313.4 |
| Pulau Segajah | 1 | 1 | 4440.3 | 4440.3 |
| Pulau Selokia Dalam | 1 | 1 | 202.1 | 202.1 |
| Pulau Selokia Luar | 1 | 1 | 817.1 | 817.1 |
| Pulau Siacca | 1 | 1 | 172.9 | 172.9 |
| Pulau Tihi-Tihi | 1 | 1 | 1845.6 | 1845.6 |
| Satimpo | 25 | 0 | 0.0 | 0.0 |
| Selangan | 1 | 1 | 315.0 | 315.0 |
| Tanjung Laut Indah | 32 | 0 | 0.0 | 0.0 |
| Tihi-Tihi | 1 | 1 | 1903.9 | 1903.9 |

