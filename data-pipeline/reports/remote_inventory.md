# Inventaris Geoportal Kota Bontang (WFS + CSW)

Akses read-only, tanpa autentikasi. Respons mentah ada di
`raw/remote/wfs_geoportal/20261102T052937Z/` dan `raw/remote/csw_geoportal/20261102T052952Z/` (URL dan parameter tiap request ada di `requests.json`).

## WFS (GeoServer)

- Versi didukung: 2.0.0
- Operasi yang diiklankan: GetCapabilities, DescribeFeatureType, GetFeature, GetPropertyValue, ListStoredQueries, DescribeStoredQueries, CreateStoredQuery, DropStoredQuery, LockFeature, GetFeatureWithLock, Transaction
- **Yang dipakai pipeline hanya** GetCapabilities, DescribeFeatureType, dan GetFeature. Transaction, LockFeature,
  GetFeatureWithLock, CreateStoredQuery, dan DropStoredQuery diiklankan server, tetapi ditolak oleh
  `sources/remote_http.py` sebelum request dikirim.
- Paging: ImplementsResultPaging = TRUE, CountDefault = None, PagingIsTransactionSafe = FALSE
- Jumlah FeatureType: 23

| FeatureType | Judul | SRS default | Jumlah fitur | Atribut | Padanan lokal |
|---|---|---|---|---|---|
| `geonode:banjir_ar_25k_delineasi2026` | Banjir Kota Bontang Awal Tahun 2026 | 32650 | 327 | 15 | - |
| `geonode:banjir_ar_25k_2019_2020_final` | Banjir Kota Bontang Tahun 2019 - 2020 | 32650 | 41 | 9 | - |
| `geonode:banjir_ar_25k_2021_final` | Banjir Kota Bontang Tahun 2021 | 32650 | 80 | 11 | - |
| `geonode:banjir_ar_25k_2022_final` | Banjir Kota Bontang Tahun 2022 | 32650 | 206 | 9 | - |
| `geonode:banjir_ar_25k_2023_final` | Banjir Kota Bontang Tahun 2023 | 32650 | 144 | 13 | - |
| `geonode:banjir_ar_25k_2024_final` | Banjir Kota Bontang Tahun 2024 | 32650 | 129 | 11 | - |
| `geonode:banjir_ar_25k_890c6bb9af555d3221c4e453f9f5e32e` | Banjir Kota Bontang Tahun 2025 | 32650 | 201 | 23 | - |
| `geonode:batas_administrasi_kecamatan_13072026` | Batas Kecamatan Kota Bontang | 9480 | 3 | 28 | - |
| `geonode:batas_administrasi_kelurahan_0906202604e2ca2ef6fa` | Batas Kelurahan Kota Bontang | 9480 | 15 | 28 | `raw/geojson/batas-kelurahan.json` |
| `geonode:batas_administrasi_kelurahan_rt_08062026` | Batas RT Kota Bontang | 32650 | 526 | 8 | `raw/geojson/batas-rt.json` |
| `geonode:kolam_pt_5k` | Peta Kolam Kota Bontang | 9480 | 139 | 10 | - |
| `geonode:rwnbanjir_ar_25k` | Rawan Banjir | 9480 | 8297 | 15 | - |
| `geonode:kebakaranhutla_ar_10k` | Rawan Kebakaran Hutan dan Lahan | 9480 | 79167 | 23 | - |
| `geonode:tanahlongsor_ar_10k` | Rawan Tanah Longsor | 9480 | 6640 | 23 | - |
| `geonode:puskeswan_ar_5k` | Sebaran Bangunan Puskeswan Kota Bontang | 9480 | 1 | 13 | - |
| `geonode:klinik_pt_5k` | Sebaran Klinik di Kota Bontang | 9480 | 6 | 11 | - |
| `geonode:posyandu_pt_5k` | Sebaran Posyandu di Kota Bontang | 9480 | 123 | 22 | - |
| `geonode:puskesmas_pt_5k` | Sebaran Puskesmas di Kota Bontang | 9480 | 6 | 11 | - |
| `geonode:rumahsakit_pt_5k` | Sebaran Rumah Sakit di Kota Bontang | 9480 | 5 | 11 | - |
| `geonode:saranaibadah_pt_5k` | Sebaran Sarana Ibadah Kota Bontang | 9480 | 101 | 9 | - |
| `geonode:unittransfusidarah_pt_5k` | Sebaran Unit Transfusi Darah Kota Bontang | 9480 | 1 | 8 | - |
| `geonode:jalan_ln_rdtr` | Status Jalan Kota Bontang | 32650 | 4348 | 15 | - |
| `geonode:sungai_ln_5k` | Sungai Kota Bontang | 32650 | 5 | 7 | `raw/geojson/sungai_ln_5k.json` |

EPSG:9480 = SRGI2013 / UTM zone 50N. Bedanya dengan WGS 84 / UTM 50N (EPSG:32650) di bawah 1 m, jadi untuk QC
keduanya diperlakukan setara.

### Atribut FeatureType yang punya padanan lokal

- **kelurahan** (`geonode:batas_administrasi_kelurahan_0906202604e2ca2ef6fa`): `fid` (int), `objectid` (long), `metadata` (string), `tipadm` (double), `wadmkc` (string), `namobj` (string), `wadmkd` (string), `kdcbps` (string), `wiadkd` (string), `srs_id` (string), `kdpumkab` (string), `wadmpr` (string), `shape_area` (double), `kdpbps` (string), `fcode` (string), `wiadpr` (string), `kdbbps` (string), `wiadkc` (string), `remark` (string), `kdpumdes` (string), `wadmkk` (string), `kdebps` (string), `wiadkk` (string), `kdpumkec` (string), `shape_leng` (double), `luaswh` (double), `kdpumprov` (string), `geom` (MultiSurfacePropertyType)

- **rt** (`geonode:batas_administrasi_kelurahan_rt_08062026`): `fid` (int), `objectid` (long), `kecamatan` (string), `kelurahan` (string), `rt` (string), `keterangan` (string), `luas` (double), `geom` (MultiSurfacePropertyType)

- **sungai** (`geonode:sungai_ln_5k`): `fid` (int), `id` (int), `nama` (string), `panjang` (double), `panjang_m` (double), `panjang_km` (double), `geom` (MultiCurvePropertyType)

## CSW (pycsw)

- Total record ISO 19139 (`gmd:MD_Metadata`): **25**
- Server juga mengiklankan Transaction dan Harvest; keduanya tidak dipakai.

Sampel GetRecordById:

| id | Judul | Tipe | bbox WGS84 | Layer terkait (OGC:WMS/WFS) |
|---|---|---|---|---|
| `91f1748d-bbeb-46ee-95d7-0f602e8409ff` | Banjir Kota Bontang Tahun 2023 | dataset | [117.4379, 0.0347, 117.5188, 0.1974] | `geonode:banjir_ar_25k_2023_final` |
| `531641b9-e35c-4ab9-ac44-331c1661a096` | Batas RT Kota Bontang | dataset | [117.3883, 0.0225, 117.5659, 0.206] | `geonode:batas_administrasi_kelurahan_rt_08062026` |
| `cbcda8fb-ae6f-4cf5-a8b9-d8f9b53d959a` | Banjir Kota Bontang Tahun 2024 | dataset | [117.4477, 0.0347, 117.5188, 0.1974] | `geonode:banjir_ar_25k_2024_final` |

- Abstrak `91f1748d`: Peta Banjir Kota Bontang Berdasarkan Pendataan Tahun 2023
- Abstrak `531641b9`: Batas adminsitrasi RT Kota Bontang hasil perbaikan melalui proses delineasi citra LiDAR dari data sebelumnya yang bersumber dari RTRW Kota Bontang Tahun 20219
- Abstrak `cbcda8fb`: Peta Banjir Kota Bontang Berdasarkan Pendataan Tahun 2024

## Pencocokan dengan GeoJSON lokal

| Layer lokal | File lokal | FeatureType WFS | Jumlah fitur WFS |
|---|---|---|---|
| kelurahan | `raw/geojson/batas-kelurahan.json` | `geonode:batas_administrasi_kelurahan_0906202604e2ca2ef6fa` | 15 |
| rt | `raw/geojson/batas-rt.json` | `geonode:batas_administrasi_kelurahan_rt_08062026` | 526 |
| sungai | `raw/geojson/sungai_ln_5k.json` | `geonode:sungai_ln_5k` | 5 |

FeatureType tanpa padanan lokal (20): `banjir_ar_25k_delineasi2026`, `banjir_ar_25k_2019_2020_final`, `banjir_ar_25k_2021_final`, `banjir_ar_25k_2022_final`, `banjir_ar_25k_2023_final`, `banjir_ar_25k_2024_final`, `banjir_ar_25k_890c6bb9af555d3221c4e453f9f5e32e`, `batas_administrasi_kecamatan_13072026`, `kolam_pt_5k`, `rwnbanjir_ar_25k`, `kebakaranhutla_ar_10k`, `tanahlongsor_ar_10k`, `puskeswan_ar_5k`, `klinik_pt_5k`, `posyandu_pt_5k`, `puskesmas_pt_5k`, `rumahsakit_pt_5k`, `saranaibadah_pt_5k`, `unittransfusidarah_pt_5k`, `jalan_ln_rdtr`
