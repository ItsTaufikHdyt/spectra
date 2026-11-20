# data-pipeline/raw/ — data mentah (TIDAK ada di repo)

Isi folder ini di-ignore git (`.gitignore`; hanya `README.md` dan `.gitkeep` yang dilacak). **Read-only:** jangan ubah, pindahkan, atau ganti nama berkas.
Pipeline hanya membaca dari sini; semua keluaran ada di `../processed/`.

| Subfolder | Isi | Ukuran | Panduan |
|---|---|---|---|
| `citygml/` | Model 3D bangunan CityGML, 15 kelurahan (**sumber tunggal data bangunan**, ADR-004) | 3,5 GB, 31 berkas `.gml` | [`citygml/README.md`](citygml/README.md) |
| `geojson/` | Batas kelurahan, batas RT, dan sungai (GeoJSON) | 2,8 MB, 3 berkas | [`geojson/README.md`](geojson/README.md) |
| `remote/` | Respons mentah geoportal (WFS/CSW) per run `fetch_sources.py` | 22 MB, 127 berkas | [`remote/README.md`](remote/README.md) |

Catatan: CityJSON lama (`raw/3d/`) sudah **diarsipkan di luar repo** dan tidak dipakai lagi (ADR-004; STATUS.md).
Bila folder ini kosong (repo baru di-clone), salinan data harus diminta dari pemilik proyek; lihat README tiap subfolder dan README root.
