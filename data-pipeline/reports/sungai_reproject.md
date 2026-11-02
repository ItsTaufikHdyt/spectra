# Laporan proyeksi sungai (EPSG:32650 → EPSG:4326)

Sumber: `raw/geojson/sungai_ln_5k.json` (CRS `urn:ogc:def:crs:EPSG::32650`). Output: `processed/geojson/sungai_ln.wgs84.geojson`.

| id | nama | panjang_km atribut | panjang UTM (m) | selisih vs panjang_m (%) | di dalam batas kota (%) | catatan |
|---|---|---|---|---|---|---|
| 1 | Sungai Bontang | 13.3071 | 13317.279 | 0.0764 | 99.86 | - |
| 2 | Sungai Nyerakat | 17.4194 | 17419.382 | 0.0 | 100.0 | - |
| 3 | Sungai Kanibungan | 3.7114 | 3709.848 | -0.0408 | 95.85 | - |
| 4 | Sungai Guntung | 4.7263 | 4726.862 | 0.0126 | 79.42 | Alur hampir lurus (sinuositas 1,093) dan 20,6% panjang di luar batas kota: cek apakah alur sungai sebenarnya atau garis bantu/kanal/alur laut. |
| 0 | Drainase Dahllia | 6.9847 | 7011.144 | 0.3782 | 96.82 | Kandidat koreksi ejaan: 'Dahllia' kemungkinan 'Dahlia' (belum diputuskan).<br>Kandidat koreksi kategori: drainase, bukan sungai (belum diputuskan).<br>id = 0, berbeda dari pola id 1–4 fitur lain.<br>Panjang hitung ulang berbeda > 0,1% dari atribut. |

Extent output: [117.428014, 0.030858, 117.517358, 0.206011] — diharapkan [117.39, 0.02, 117.57, 0.21] ±0.01° → **sesuai**.

Penanda file:

- Nama file 'sungai_ln_5k.json' memuat '_5k', sedangkan sungai terpanjang 17.4 km. Bila '_5k' berarti 5 km, nama tidak sesuai isi; bila berarti skala peta 1:5.000 (lazim pada data RBI), nama sesuai. Belum diputuskan; output memakai nama tanpa '_5k'.
