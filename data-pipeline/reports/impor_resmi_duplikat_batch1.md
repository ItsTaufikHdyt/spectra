# Duplikat dalam batch impor resmi (batch 1) — daftar kasus dan USULAN

Dihasilkan dari `reports/impor_resmi_analisis_batch1.json` (aturan: pusat footprint ≤ 2 m dan IoU ≥ 0,5; ditambah `gml_id` sama dengan pusat ≤ 2 m).
**Ini usulan, bukan keputusan.** Tidak ada ID yang sudah diterbitkan. Inventaris hanya mencatat 1 kasus (Gunung Elai Part II/III); analisis ini menemukan **17 kasus**, 13 di antaranya **antar kelurahan** (tidak tercakup inventaris, yang hanya memeriksa keunikan dalam satu kelurahan).

| # | Kategori | Bangunan A | Bangunan B | Jarak/IoU | Tinggi A / B (m) | Usulan |
|---|---|---|---|---|---|---|
| 1 | berkas sama | urut 1023 · api_api · Api Api · …1-0765762 | urut 4000 · api_api · Api Api · …1-0765762 | 0.307 m / 0.979 | 6.366 / 8.278 | **kecualikan yang lebih rendah** |
| 2 | antar kelurahan | urut 18799 · bontang_baru · GABUNGAN BONTANG BARU · …2-91C74BD | urut 19465 · bontang_kuala · Bontang Kuala · …1-7580705 | 0.064 m / 0.954 | 9.569 / 9.783 | **kecualikan salinan berkas kelurahan lain** |
| 3 | antar kelurahan | urut 18800 · bontang_baru · GABUNGAN BONTANG BARU · …2-BEFDAD1 | urut 19464 · bontang_kuala · Bontang Kuala · …1-8499682 | 0.051 m / 0.978 | 8.168 / 10.457 | **kecualikan salinan berkas kelurahan lain** |
| 4 | antar kelurahan | urut 25873 · guntung · Guntung - Part III · …9-57C305F | urut 43028 · satimpo · Satimpo · …2-91DC09F | 0.174 m / 0.973 | 10.407 / 10.479 | **kecualikan salinan berkas kelurahan lain** |
| 5 | antar kelurahan | urut 25874 · guntung · Guntung - Part III · …9-252DBFA | urut 43029 · satimpo · Satimpo · …2-3E2D131 | 0.133 m / 0.947 | 8.37 / 8.296 | **kecualikan salinan berkas kelurahan lain** |
| 6 | antar kelurahan | urut 25878 · guntung · Guntung - Part III · …9-18D0483 | urut 43030 · satimpo · Satimpo · …2-889139B | 0.16 m / 0.954 | 6.49 / 6.471 | **kecualikan salinan berkas kelurahan lain** |
| 7 | antar kelurahan | urut 25883 · guntung · Guntung - Part III · …9-F9F25CD | urut 42613 · satimpo · Satimpo · …2-E2364A5 | 0.52 m / 0.952 | 8.287 / 7.899 | **kecualikan salinan berkas kelurahan lain** |
| 8 | antar kelurahan | urut 25884 · guntung · Guntung - Part III · …9-A1F0419 | urut 43025 · satimpo · Satimpo · …2-68EBAA4 | 0.3 m / 0.965 | 7.176 / 6.989 | **kecualikan salinan berkas kelurahan lain** |
| 9 | antar kelurahan | urut 25885 · guntung · Guntung - Part III · …9-C1F09E3 | urut 43024 · satimpo · Satimpo · …2-5A828DB | 0.155 m / 0.875 | 4.812 / 4.362 | **kecualikan salinan berkas kelurahan lain** |
| 10 | antar kelurahan | urut 25888 · guntung · Guntung - Part III · …9-F1C2551 | urut 42602 · satimpo · Satimpo · …2-D8C7D3B | 0.257 m / 0.972 | 8.861 / 9.027 | **kecualikan salinan berkas kelurahan lain** |
| 11 | antar kelurahan | urut 25890 · guntung · Guntung - Part III · …9-E8ABE9E | urut 43022 · satimpo · Satimpo · …2-F707A56 | 0.133 m / 0.949 | 5.099 / 4.767 | **kecualikan salinan berkas kelurahan lain** |
| 12 | antar kelurahan | urut 10524 · berebas_pantai · Berebas Pantai · …1-9E58453 | urut 14444 · berebas_tengah · Berebas Tengah · …1-511877C | 1.727 m / 0.604 | 5.888 / 6.81 | **kecualikan salinan berkas kelurahan lain** |
| 13 | antar kelurahan | urut 18808 · bontang_baru · GABUNGAN BONTANG BARU · …2-03CA862 | urut 19419 · bontang_kuala · Bontang Kuala · …1-8101379 | 0.055 m / 0.969 | 1.04 / 3.967 | **kecualikan salinan berkas kelurahan lain** |
| 14 | antar kelurahan | urut 10947 · berebas_pantai · Berebas Pantai · …1-B82148E | urut 14418 · berebas_tengah · Berebas Tengah · …1-A072030 | 0.116 m / 0.91 | 5.939 / 5.438 | **kecualikan salinan berkas kelurahan lain** |
| 15 | satu kelurahan, berkas/part berbeda | urut 27248 · gunung_elai · Gunung Elai - Part II · …2-E5C4D86 | urut 29904 · gunung_elai · Gunung Elai - Part III · …3-E4B758B | 0.135 m / 0.937 | 6.445 / 7.525 | **kecualikan Part II (simpan Part III)** |
| 16 | berkas sama | urut 967 · api_api · Api Api · …1-6684057 | urut 978 · api_api · Api Api · …1-6684057 | 1.542 m / — | 6.936 / 0 | **pertahankan keduanya (tidak dikecualikan)** |
| 17 | berkas sama | urut 38167 · loktuan · Loktuan - Part I · …1-8994618 | urut 38218 · loktuan · Loktuan - Part I · …1-8994618 | 0.974 m / — | 4.929 / 2.294 | **pertahankan keduanya (tidak dikecualikan)** |

## Alasan per kasus
- **#1** gml_id sama, footprint hampir identik (IoU 0,979), tinggi beda 6,37 vs 8,28 m; kepercayaan RENDAH, alternatif: pertahankan keduanya.
- **#2** Kedua salinan jatuh di batas kelurahan bontang_kuala; simpan salinan dari berkas bontang_kuala, kecualikan salinan dari bontang_baru.
- **#3** Kedua salinan jatuh di batas kelurahan bontang_kuala; simpan salinan dari berkas bontang_kuala, kecualikan salinan dari bontang_baru.
- **#4** Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari guntung.
- **#5** Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari guntung.
- **#6** Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari guntung.
- **#7** Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari guntung.
- **#8** Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari guntung.
- **#9** Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari guntung.
- **#10** Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari guntung.
- **#11** Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari guntung.
- **#12** Kedua salinan jatuh di batas kelurahan berebas_tengah; simpan salinan dari berkas berebas_tengah, kecualikan salinan dari berebas_pantai.
- **#13** Kedua salinan jatuh di batas kelurahan bontang_kuala; simpan salinan dari berkas bontang_kuala, kecualikan salinan dari bontang_baru.
- **#14** Kedua salinan jatuh di batas kelurahan berebas_tengah; simpan salinan dari berkas berebas_tengah, kecualikan salinan dari berebas_pantai.
- **#15** Berkas Part III lebih baru (diubah 2025-06-15 18:41 vs 18:15) dan lebih tinggi (7,525 vs 6,445 m); kepercayaan RENDAH.
- **#16** gml_id bentrok pada objek berbeda (footprint tidak tumpang tindih / salah satu tanpa footprint); bukan salinan.
- **#17** gml_id bentrok pada objek berbeda (footprint tidak tumpang tindih / salah satu tanpa footprint); bukan salinan.

## Ringkasan usulan
- **Kecualikan 15**, pertahankan semua bangunan lain: 13 salinan antar kelurahan (3 Bontang Baru→Bontang Kuala, 8 Guntung Part III→Satimpo, 2 Berebas Pantai→Berebas Tengah), 1 Gunung Elai Part II, 1 Api Api (yang lebih rendah).
- **Pertahankan keduanya** pada 2 kasus `gml_id` bentrok objek berbeda (Api Api 967/978, Loktuan Part I 38167/38218).
- Konsekuensi: 51.888 − 15 = **51.873 ID resmi** (bila usulan diterima). Catatan Berebas Tengah: salinan yang disimpan (berkas Berebas Tengah, CityGML 3.0) tidak punya `jumlah_lantai`/`measuredHeight`, sedangkan salinan Berebas Pantai punya `jumlah_lantai` = 1; usulan tetap mengikuti batas kelurahan.

## Draf `config/keputusan_duplikat.yaml` (baru dipakai bila usulan disetujui)

```yaml
kecualikan:
  - {slug: api_api, sumber_file: "Model 3D - Kelurahan Api Api.gml", gml_id: "AA_13082025-AAAA-00047-GEOAIBTG01-0765762", pusat: [554713.126, 14557.738], alasan: "gml_id sama, footprint hampir identik (IoU 0,979), tinggi beda 6,37 vs 8,28 m; kepercayaan RENDAH, alternatif:"}
  - {slug: bontang_baru, sumber_file: "GABUNGAN BONTANG BARU.gml", gml_id: "BB_15062025-AAAA-00507-GeoAI02-91C74BD", pusat: [555444.478, 16080.296], alasan: "Kedua salinan jatuh di batas kelurahan bontang_kuala; simpan salinan dari berkas bontang_kuala, kecualikan sal"}
  - {slug: bontang_baru, sumber_file: "GABUNGAN BONTANG BARU.gml", gml_id: "BB_15062025-AAAA-00508-GeoAI02-BEFDAD1", pusat: [555441.063, 16072.79], alasan: "Kedua salinan jatuh di batas kelurahan bontang_kuala; simpan salinan dari berkas bontang_kuala, kecualikan sal"}
  - {slug: guntung, sumber_file: "Model 3D - Kelurahan Guntung - Part III.gml", gml_id: "LK_14082025-AAAA-00198-GeoAI09-57C305F", pusat: [551708.376, 11899.146], alasan: "Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari gu"}
  - {slug: guntung, sumber_file: "Model 3D - Kelurahan Guntung - Part III.gml", gml_id: "LK_14082025-AAAA-00199-GeoAI09-252DBFA", pusat: [551707.605, 11878.464], alasan: "Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari gu"}
  - {slug: guntung, sumber_file: "Model 3D - Kelurahan Guntung - Part III.gml", gml_id: "LK_14082025-AAAA-00201-GeoAI09-18D0483", pusat: [551717.801, 11851.199], alasan: "Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari gu"}
  - {slug: guntung, sumber_file: "Model 3D - Kelurahan Guntung - Part III.gml", gml_id: "LK_14082025-AAAA-00206-GeoAI09-F9F25CD", pusat: [551931.201, 11859.591], alasan: "Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari gu"}
  - {slug: guntung, sumber_file: "Model 3D - Kelurahan Guntung - Part III.gml", gml_id: "LK_14082025-AAAA-00207-GeoAI09-A1F0419", pusat: [551837.118, 11842.775], alasan: "Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari gu"}
  - {slug: guntung, sumber_file: "Model 3D - Kelurahan Guntung - Part III.gml", gml_id: "LK_14082025-AAAA-00208-GeoAI09-C1F09E3", pusat: [551991.921, 11836.616], alasan: "Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari gu"}
  - {slug: guntung, sumber_file: "Model 3D - Kelurahan Guntung - Part III.gml", gml_id: "LK_14082025-AAAA-00210-GeoAI09-F1C2551", pusat: [551916.62, 11808.328], alasan: "Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari gu"}
  - {slug: guntung, sumber_file: "Model 3D - Kelurahan Guntung - Part III.gml", gml_id: "LK_14082025-AAAA-00212-GeoAI09-E8ABE9E", pusat: [551997.537, 11756.491], alasan: "Kedua salinan jatuh di batas kelurahan satimpo; simpan salinan dari berkas satimpo, kecualikan salinan dari gu"}
  - {slug: berebas_pantai, sumber_file: "Model 3D - Kelurahan Berebas Pantai.gml", gml_id: "BP_27052025-AAAA-00168-GeoAI01-9E58453", pusat: [553411.984, 12366.012], alasan: "Kedua salinan jatuh di batas kelurahan berebas_tengah; simpan salinan dari berkas berebas_tengah, kecualikan s"}
  - {slug: bontang_baru, sumber_file: "GABUNGAN BONTANG BARU.gml", gml_id: "BB_15062025-AAAA-00515-GeoAI02-03CA862", pusat: [555396.058, 16046.504], alasan: "Kedua salinan jatuh di batas kelurahan bontang_kuala; simpan salinan dari berkas bontang_kuala, kecualikan sal"}
  - {slug: berebas_pantai, sumber_file: "Model 3D - Kelurahan Berebas Pantai.gml", gml_id: "BP_27052025-AAAA-00209-GeoAI01-B82148E", pusat: [553382.904, 12430.099], alasan: "Kedua salinan jatuh di batas kelurahan berebas_tengah; simpan salinan dari berkas berebas_tengah, kecualikan s"}
  - {slug: gunung_elai, sumber_file: "Model 3D - Kelurahan Gunung Elai - Part II.gml", gml_id: "GE_15062025-AAAA-01081-GeoAI02-E5C4D86", pusat: [554071.973, 16025.411], alasan: "Berkas Part III lebih baru (diubah 2025-06-15 18:41 vs 18:15) dan lebih tinggi (7,525 vs 6,445 m); kepercayaan"}
```
