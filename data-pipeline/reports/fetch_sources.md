# Laporan sumber data (fetch_sources.py)

Run: `20261102T053649Z` (UTC). Konfigurasi: `config/sources.yaml`.

## Status sumber

| id | tipe | layer | prioritas | status | jumlah | halaman | output | catatan |
|---|---|---|---|---|---|---|---|---|
| `geojson_lokal_kelurahan` | geojson_lokal | kelurahan | 1 | ok | 15 | - | `processed/sources/geojson_lokal_kelurahan.geojson` |  |
| `geojson_lokal_rt` | geojson_lokal | rt | 1 | ok | 526 | - | `processed/sources/geojson_lokal_rt.geojson` |  |
| `geojson_lokal_sungai` | geojson_lokal | sungai | 1 | ok | 5 | - | `processed/sources/geojson_lokal_sungai.geojson` |  |
| `wfs_kelurahan` | wfs | kelurahan | 2 | ok | 15 | 1 | `processed/sources/wfs_kelurahan.geojson` | urutan sumbu: lonlat (IoU extent 1,0000) |
| `wfs_rt` | wfs | rt | 2 | ok | 526 | 3 | `processed/sources/wfs_rt.geojson` | urutan sumbu: lonlat (IoU extent 1,0000) |
| `wfs_sungai` | wfs | sungai | 2 | ok | 5 | 1 | `processed/sources/wfs_sungai.geojson` | urutan sumbu: lonlat (IoU extent 1,0000) |
| `csw_geoportal` | csw | - | 1 | ok | 25 | 3 | `processed/catalog/records.json` |  |

## Uji identik GeoJSON lokal vs jalur lama

Dibandingkan per fitur, dengan urutan yang sama: geometri (koordinat persis), slug, dan nama kelurahan ternormalisasi
(sungai: nama).

| sumber | file lama | jumlah (baru / lama) | geometri sama | nama & slug sama | identik |
|---|---|---|---|---|---|
| `geojson_lokal_kelurahan` | `processed/geojson/batas-kelurahan.norm.geojson` | 15 / 15 | ya | ya | **ya** |
| `geojson_lokal_rt` | `processed/geojson/batas-rt.norm.geojson` | 526 / 526 | ya | ya | **ya** |
| `geojson_lokal_sungai` | `processed/geojson/sungai_ln.wgs84.geojson` | 5 / 5 | ya | ya | **ya** |

## Katalog CSW (25 record)

| Judul | Tipe | Layer terkait | Status | id |
|---|---|---|---|---|
| Banjir Kota Bontang Awal Tahun 2026 | dataset / vector | 1 | completed | `b6f2762d-aadc-43cf-ab59-2730b777a888` |
| Banjir Kota Bontang Tahun 2019 - 2020 | dataset / vector | 1 | completed | `d44c451f-b05c-42eb-8d52-dd5c53b23861` |
| Banjir Kota Bontang Tahun 2021 | dataset / vector | 1 | completed | `93c7cf91-f7a0-4354-a3ef-3dfa8598aa30` |
| Banjir Kota Bontang Tahun 2022 | dataset / vector | 1 | completed | `cd3d72a1-d071-4107-ab7c-08a341317406` |
| Banjir Kota Bontang Tahun 2023 | dataset / vector | 1 | completed | `91f1748d-bbeb-46ee-95d7-0f602e8409ff` |
| Banjir Kota Bontang Tahun 2024 | dataset / vector | 1 | completed | `cbcda8fb-ae6f-4cf5-a8b9-d8f9b53d959a` |
| Banjir Kota Bontang Tahun 2025 | dataset | 1 | completed | `9c18cbfd-4479-4e00-b39a-b8393859bb4c` |
| Batas Kecamatan Kota Bontang | dataset / vector | 1 | completed | `d57a7d6d-94a4-44b9-a792-b798e7e2caa9` |
| Batas Kelurahan Kota Bontang | dataset / vector | 1 | completed | `9847caf8-3c9c-4f56-851c-69c734878b34` |
| Batas RT Kota Bontang | dataset / vector | 1 | completed | `531641b9-e35c-4ab9-ac44-331c1661a096` |
| Peta Bangunan Pemerintahan Kota Bontang | dataset / vector | 1 | completed | `1641b78d-24ce-42ce-9434-dcbfe7500984` |
| Peta Kolam Kota Bontang | dataset / vector | 1 | completed | `720fcf9d-ed59-4a3a-a287-63145f5ad490` |
| Peta Kolam Kota Bontang | dataset / vector | 1 | completed | `d52667de-847b-4a63-96f4-285a863224b6` |
| Rawan Banjir | dataset | 1 | completed | `842e85a6-49de-4311-b3b3-914af89280e2` |
| Rawan Kebakaran Hutan dan Lahan | dataset | 1 | completed | `75f64bb5-00cc-47fc-8254-ce9fb06eb8f0` |
| Rawan Tanah Longsor | dataset | 1 | completed | `b4d7b0d8-0211-41ea-bde4-1057ba9ff2fa` |
| Sebaran Bangunan Puskeswan Kota Bontang | dataset / vector | 1 | completed | `5e6873ba-d049-4435-af59-909134f3ea0e` |
| Sebaran Klinik di Kota Bontang | dataset / vector | 1 | completed | `c8dcf3fb-e6b4-4348-8ce8-3cb141b5be10` |
| Sebaran Posyandu di Kota Bontang | dataset / vector | 1 | completed | `64bf07f7-bc0c-4afe-9d62-1003d19cd5d2` |
| Sebaran Puskesmas di Kota Bontang | dataset / vector | 1 | completed | `0dd62b7e-e01c-4305-b96a-524832c96d02` |
| Sebaran Rumah Sakit di Kota Bontang | dataset / vector | 1 | completed | `5635c86f-9792-4bb6-a1c1-44760969de09` |
| Sebaran Sarana Ibadah Kota Bontang | dataset / vector | 1 | completed | `7b114ec7-feb1-4e65-bcf2-f6590b549347` |
| Sebaran Unit Transfusi Darah Kota Bontang | dataset / vector | 1 | completed | `bf59ae80-c978-48f5-84fa-319f6e852a02` |
| Status Jalan Kota Bontang | dataset / vector | 1 | completed | `e6777672-2f93-41f4-835f-5b9fa82f8a98` |
| Sungai Kota Bontang | dataset / vector | 1 | completed | `524c22e2-84f4-46eb-9895-9dc6e9888afb` |

## FeatureType WFS (23)

Dari `reports/remote_inventory.json` (inventaris `raw/remote/wfs_geoportal/20261102T052937Z`).

| FeatureType | Jumlah fitur | SRS default | Padanan lokal |
|---|---|---|---|
| `banjir_ar_25k_delineasi2026` | 327 | 32650 | - |
| `banjir_ar_25k_2019_2020_final` | 41 | 32650 | - |
| `banjir_ar_25k_2021_final` | 80 | 32650 | - |
| `banjir_ar_25k_2022_final` | 206 | 32650 | - |
| `banjir_ar_25k_2023_final` | 144 | 32650 | - |
| `banjir_ar_25k_2024_final` | 129 | 32650 | - |
| `banjir_ar_25k_890c6bb9af555d3221c4e453f9f5e32e` | 201 | 32650 | - |
| `batas_administrasi_kecamatan_13072026` | 3 | 9480 | - |
| `batas_administrasi_kelurahan_0906202604e2ca2ef6fa` | 15 | 9480 | raw/geojson/batas-kelurahan.json (sama) |
| `batas_administrasi_kelurahan_rt_08062026` | 526 | 32650 | raw/geojson/batas-rt.json (sama) |
| `kolam_pt_5k` | 139 | 9480 | - |
| `rwnbanjir_ar_25k` | 8.297 | 9480 | - |
| `kebakaranhutla_ar_10k` | 79.167 | 9480 | - |
| `tanahlongsor_ar_10k` | 6.640 | 9480 | - |
| `puskeswan_ar_5k` | 1 | 9480 | - |
| `klinik_pt_5k` | 6 | 9480 | - |
| `posyandu_pt_5k` | 123 | 9480 | - |
| `puskesmas_pt_5k` | 6 | 9480 | - |
| `rumahsakit_pt_5k` | 5 | 9480 | - |
| `saranaibadah_pt_5k` | 101 | 9480 | - |
| `unittransfusidarah_pt_5k` | 1 | 9480 | - |
| `jalan_ln_rdtr` | 4.348 | 32650 | - |
| `sungai_ln_5k` | 5 | 32650 | raw/geojson/sungai_ln_5k.json (sama) |

## Perbandingan WFS vs GeoJSON lokal

Besaran metrik dihitung di EPSG:32650. Beda simetris = luas (gabungan lokal XOR gabungan WFS) / luas gabungan lokal.
Status: **sama** bila jumlah sama dan selisih ≤ 0,01%; **beda kecil** bila ≤ 1%; selain itu **beda signifikan**.

| Layer | Jumlah lokal | Jumlah WFS | Besaran | Lokal | WFS | Selisih (%) | Beda geometri | Geser extent maks. (m) | Status |
|---|---|---|---|---|---|---|---|---|---|
| kelurahan | 15 | 15 | luas total (m², EPSG:32650) | 161.877.237,7 | 161.877.237,7 | 0,0000 | 0,0000% (0,0 m²) | 0,00 | **sama** |
| rt | 526 | 526 | luas total (m², EPSG:32650) | 161.877.301,7 | 161.877.301,7 | 0,0000 | 0,0000% (0,0 m²) | 0,00 | **sama** |
| sungai | 5 | 5 | panjang total (m) | 46.184,5 | 46.184,5 | 0,0000 | Hausdorff 0,000 m | 0,00 | **sama** |

Detail nama, kunci, dan atribut:

- **kelurahan**: fid cocok 15; kunci hanya di lokal: tidak ada; hanya di WFS: tidak ada; kelurahan WFS tanpa padanan slug: tidak ada; kolom atribut beda nilai (jumlah fitur): tidak ada; beda tipe saja, mis. "261" vs 261: {'objectid': 15}.
- **rt**: fid cocok 526; kunci hanya di lokal: tidak ada; hanya di WFS: tidak ada; kelurahan WFS tanpa padanan slug: tidak ada; kolom atribut beda nilai (jumlah fitur): tidak ada; beda tipe saja, mis. "261" vs 261: {'objectid': 526}.
- **sungai**: fid cocok 5; kunci hanya di lokal: tidak ada; hanya di WFS: tidak ada; kelurahan WFS tanpa padanan slug: tidak ada; kolom atribut beda nilai (jumlah fitur): tidak ada; beda tipe saja, mis. "261" vs 261: tidak ada.

## Determinisme

File di `processed/sources/` dan `processed/catalog/records.json` tidak memuat timestamp. File yang berubah tiap run hanya
folder `raw/remote/<id>/<timestamp>/` (respons server memuat `timeStamp` / `SearchStatus timestamp`) dan laporan ini
(`timestamp_utc`, path folder raw).
