# ADR-006: Tile statis, hasil simulasi sebagai data

- **Status:** Diterima
- **Tanggal:** 2026-11-19
- **Terkait:** ADR-001, ADR-003, `docs/simulation-contract.md`

> Skema `sim`, endpoint hasil, dan styling per fitur untuk simulasi **direncanakan**; tidak ada yang diimplementasikan. Saat ini hanya registri simulasi kosong dan slot UI "Segera hadir" yang ada.

## Konteks
- Simulasi banjir/rob dan analisis lain akan menghasilkan nilai per bangunan (mis. kedalaman genangan) untuk banyak skenario.
- Membangun ulang tile 3D (±51.888 bangunan, 125 berkas `.glb`) untuk setiap skenario mahal dan memperbesar penyimpanan.
- AGENTS.md melarang menghitung atau memuat data berat mentah di browser; kontrak simulasi sudah menyatakan hasil skala kota disajikan dari backend/storage.
- ID bangunan yang stabil (ADR-003) memungkinkan hasil dirujuk tanpa menyentuh geometri.

## Keputusan
1. **Tile bangunan bersifat statis**: dibangun dari basis data sekali (per versi data bangunan), bukan per skenario.
2. **Hasil simulasi disimpan sebagai data di skema `sim`** pada PostGIS, dirujuk dengan ID bangunan (`BTG-BLD-xxxxxx`), per skenario dan per versi.
3. **Frontend menampilkan hasil lewat styling per fitur** (mis. warna bangunan menurut nilai) dengan mencocokkan properti `id` pada tile terhadap hasil dari backend, melalui kontrak `SimulationLayer` yang sudah ada. Tidak ada perubahan geometri tile.
4. Hasil dalam bentuk lain (mis. raster genangan atau grid) tetap disajikan dari backend/storage, bukan dihitung di browser.

## Alternatif yang dipertimbangkan
- **Tile per skenario:** pembangunan ulang mahal, penyimpanan berlipat, dan sulit membandingkan skenario. Ditolak.
- **Menghitung simulasi di browser:** melanggar aturan data berat (AGENTS.md §3) dan tidak dapat diaudit. Ditolak.
- **Menyimpan hasil di berkas per skenario:** tidak dapat di-query bersama atribut bangunan. Ditolak.

## Konsekuensi
- Tile baru **wajib** membawa properti `id` (ADR-003/004) agar styling per fitur dapat mencocokkan hasil; tanpa metadata (tile lama) styling per fitur tidak mungkin.
- Frontend perlu helper styling per fitur dan pengambilan hasil dari backend (**direncanakan**, belum ada) dan harus tetap memanggil `requestRender()` saat gaya berubah.
- Backend perlu endpoint hasil yang membatasi ukuran respons (data per bangunan untuk 51.888 bangunan perlu dipadatkan atau dipaginasi; **belum dirancang**).
- Perubahan data bangunan (versi baru) mengharuskan hasil lama ditandai versinya.
