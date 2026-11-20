# data-pipeline/processed/3dtiles/ — 3D Tiles 15 kelurahan (TIDAK ada di repo, dapat dibuat ulang)

## Isi
`<slug>/tileset.json` + `<slug>/t/…/*.glb` untuk 15 kelurahan, plus `master-tileset.json` (15 anak, external tileset). Total **170 berkas, 74 MB**: 139 `.glb` (maks 1,33 MB), 15 `tileset.json`, 15 `tileset_unpruned.json` (perantara tyler; tidak disalin ke frontend), 1 master.
OGC 3D Tiles 1.1, `boundingVolume.region`, transform ECEF, `.glb` meshopt + kuantisasi dengan `EXT_mesh_features` dan `EXT_structural_metadata` (enam atribut: `id`, `gml_id`, `nama`, `tinggi`, `jumlah_lantai`, `luas_tapak`; kosong = `noData`), Z dasar 0, 51.816 fitur, warna `#B1BAC2`. Asal dan perintah tyler tercatat di `tileset.json` → `asset.extras.spectra`.

## Asal data
Turunan: CityGML → PostGIS → CityJSONSeq → tyler. Tidak ada data eksternal; tile lama dari jalur CityJSON sudah dihapus.

## Cara membuat ulang
Prasyarat: `../buildings/<slug>.city.jsonl` (lihat `../buildings/README.md`), Docker dengan image `3dgi/tyler:latest` (tyler 1.0.0-alpha1).
```
data-pipeline/.venv/bin/python data-pipeline/scripts/citygml/buat_tile.py --slug <slug>     # ulangi untuk 15 slug (±2 detik tiap kelurahan)
python3 data-pipeline/scripts/04_build_master.py                                            # master + validasi; --sync menyalin ke frontend/public/tiles/
```
Warna dibaca dari `../../config/citygml_sources.yaml` (`umum.warna_bangunan_tyler`).

## Keutuhan dan aturan
Verifikasi lengkap: `scripts/citygml/verifikasi_tile.cjs` + `laporan_verifikasi.py` (`reports/impor_resmi_verifikasi.md`: ID unik = PostGIS, atribut identik). Hash salinan frontend: `../../reports/hash_baseline_public_tiles_v2.txt`. Boleh dibuat ulang; jangan di-commit.
