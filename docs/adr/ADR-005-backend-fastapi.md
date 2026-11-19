# ADR-005: Backend FastAPI

- **Status:** Diterima
- **Tanggal:** 2026-11-19
- **Terkait:** ADR-001 (PostGIS), `docs/remote-layers.md`

## Konteks
- PRD dan STATUS sebelumnya menulis "Laravel atau FastAPI, belum diputuskan".
- Backend FastAPI kecil sudah ada di `backend/` (layer geoportal: inspect WFS/CSW, daftar/tambah/ubah/hapus layer; 20 tes pytest) dan memakai ulang adapter `data-pipeline/scripts/sources/` (Python).
- Pipeline data (parser CityGML, ekspor, adapter sumber) berbahasa Python; skema dan migrasi PostGIS akan dikelola dari repo yang sama.
- Frontend sudah menyiapkan lookup atribut `GET {VITE_API_BASE_URL}/buildings/{buildingId}/attributes` (`services/buildingAttributes.js`).

## Keputusan
1. **Backend tetap FastAPI** (Python). Keputusan Laravel vs FastAPI ditutup.
2. Backend yang direncanakan menambah: akses PostGIS, endpoint atribut bangunan `GET /buildings/{id}/attributes` (kontrak sudah ada di frontend), dan, kemudian, endpoint hasil simulasi (ADR-006) dan autentikasi. **Semuanya direncanakan**; saat ini hanya layer geoportal yang ada.
3. Browser tetap tidak memanggil layanan eksternal langsung; semua lewat `/api` (AGENTS.md §5).

## Alternatif yang dipertimbangkan
- **Laravel (PHP):** tidak dapat memakai ulang adapter dan parser Python; dua bahasa untuk satu alur data. Ditolak.
- **Django:** lebih berat dari kebutuhan; ORM tidak menambah nilai untuk data spasial yang dikelola lewat SQL/migrasi. Ditolak.
- **Node.js (Express/Fastify):** konsisten dengan frontend, tetapi memecah ekosistem data Python. Ditolak.

## Konsekuensi
- Autentikasi dan pembatasan hak belum ada (STATUS hutang #17); perlu diputuskan sebelum deployment.
- Registri layer masih berkas JSON dan hanya aman untuk satu worker; pindah ke PostGIS mengikuti ADR-001.
- Dependensi backend dikunci di `backend/requirements.txt` (mencakup `data-pipeline/requirements.txt`).
- Dokumentasi menjalankan backend ada di `docs/remote-layers.md`.
