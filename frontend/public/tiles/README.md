# frontend/public/tiles/ — salinan dev 3D Tiles (TIDAK ada di repo, dapat dibuat ulang)

Aset yang dilayani dev server di `/tiles/…`. **Hanya salinan** dari `data-pipeline/processed/3dtiles/`; jangan dijadikan sumber kebenaran atau di-commit.

## Isi (156 berkas, 74 MB)
`master-tileset.json` (dimuat frontend sebagai `/tiles/master-tileset.json`) dan folder `<slug>/` (15 kelurahan) dengan `tileset.json` + `t/…/*.glb`. `tileset_unpruned.json` tidak disalin.

## Asal data
Turunan pipeline CityGML (lihat `data-pipeline/processed/3dtiles/README.md`).

## Cara membuat ulang (dari root repo)
```
python3 data-pipeline/scripts/04_build_master.py --sync      # inkremental, idempoten; hanya menyentuh folder kelurahan + master
```
Prasyarat: `data-pipeline/processed/3dtiles/` sudah terisi.

## Keutuhan
`(cd frontend/public/tiles && sha256sum -c --quiet ../../../data-pipeline/reports/hash_baseline_public_tiles_v2.txt)` (156 hash). Aturan: boleh dihapus dan dibuat ulang; jangan di-commit. Catatan: `npm run build` menyalin folder ini ke `dist/` (STATUS hutang #9).
