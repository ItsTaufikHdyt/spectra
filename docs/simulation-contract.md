# Kontrak Simulasi — Digital Twin Kota Bontang

Dokumen ini menjelaskan cara menambah simulasi (banjir/rob menjadi yang pertama) **tanpa
mengubah inti aplikasi**. Inti aplikasi = store, composable, panel kiri, dan legenda; semuanya
sudah membaca registry secara generik.

## 1. Gambaran alur

```
src/simulations/<id>/index.js   ──defineSimulation()──►  src/simulations/index.js (SIMULATIONS)
                                                                  │
         SimulationPanel.vue  ◄── daftar & tombol Jalankan ───────┤
         useSimulation.js     ── activate(id) → createLayer() ────┤──► SimulationLayer (objek Cesium)
         simulationStore.js   ◄── activeId, params, status         │
         useLegend.js         ◄── legend(params) ──────────────────┘──► MapLegend.vue
```

| Bagian | Berkas | Isi |
|---|---|---|
| Kontrak & validasi | `frontend/src/simulations/contract.js` | `defineSimulation`, `validateRegistry`, `assertSimulationLayer` |
| Registry | `frontend/src/simulations/index.js` | `SIMULATIONS`, `PLANNED_SIMULATIONS`, `getSimulation` |
| State (data biasa) | `frontend/src/stores/simulationStore.js` | `activeId`, `params`, `status`, `error`, `visible` |
| Siklus hidup layer | `frontend/src/composables/useSimulation.js` | `activate`, `deactivate`, `updateParams`, `setVisible`, `releaseSimulation` |
| UI | `frontend/src/components/simulation/SimulationPanel.vue` | daftar simulasi di panel kiri + panel parameter aktif |

Satu simulasi aktif pada satu waktu. Mengaktifkan simulasi lain otomatis melepas yang lama.

## 2. Kontrak `SimulationDefinition`

| Properti | Tipe | Keterangan |
|---|---|---|
| `id` | `string` | kebab-case unik, mis. `banjir-rob`. |
| `name` | `string` | Nama tampilan, mis. "Simulasi banjir". |
| `description` | `string` | Satu-dua kalimat untuk pengguna. |
| `ParameterPanel` | komponen Vue | Props `{ params, disabled }`; emit `update:params` berisi **patch** (hanya field yang berubah). |
| `defaultParams()` | `() => object` | Parameter awal. **Hanya nilai polos** (angka, string, boolean, array/objek polos). |
| `legend(params)` | `(params) => LegendSection[]` | Bagian legenda untuk parameter saat ini. |
| `createLayer(ctx, params)` | `async ({ viewer, Cesium }, params) => SimulationLayer` | Membuat layer hasil di viewer. |

### `SimulationLayer` (hasil `createLayer`)

| Fungsi | Keterangan |
|---|---|
| `update(params)` | Terapkan parameter baru (boleh async). |
| `setVisible(visible)` | Tampilkan/sembunyikan hasil tanpa menghapusnya. |
| `destroy()` | Lepas **semua** resource Cesium (primitive, entity, data source, imagery, listener). Dipanggil tepat sekali. |

### `LegendSection` (dipakai bersama layer dan simulasi)

```js
// Kategorikal
{ id: 'kelas-genangan', title: 'Kelas genangan', type: 'categorical',
  items: [{ label: 'Rendah', color: '#9ecae1', shape: 'fill' }] }   // shape: fill | outline | dot

// Skala warna — stops urut naik, label min/maks diformat id-ID otomatis
{ id: 'kedalaman', title: 'Kedalaman genangan', type: 'gradient', unit: 'm',
  stops: [{ value: 0, color: '#deebf7' }, { value: 2.5, color: '#08306b' }] }
```

## 3. Aturan wajib

1. **Objek Cesium tidak boleh masuk Pinia atau `ref()`.** Simpan di dalam closure `createLayer`
   (lihat contoh). `simulationStore` hanya berisi data polos.
2. **Data berat tidak dihitung atau dimuat mentah di browser.** Hasil simulasi skala kota
   disajikan dari backend/storage (raster tiles, 3D Tiles, atau grid terkompresi). Konversi CRS
   (EPSG:32650 → 4326/4978) dilakukan di ETL/backend, bukan di klien.
3. **`destroy()` harus lengkap.** `CesiumCanvas.vue` memanggil `releaseSimulation()` sebelum
   `unload3DTiles()` dan `destroyViewer()`; layer yang bocor akan mengakses viewer yang sudah mati.
4. **Parameter selalu polos.** `useSimulation` mengirim salinan polos ke `createLayer`/`update`;
   jangan menyimpan referensi ke store di dalam layer.
5. **Teks UI berbahasa Indonesia**, angka diformat dengan `@/utils/format` (koma desimal).

## 4. Menambah simulasi baru

1. Buat folder `frontend/src/simulations/<id>/` berisi `index.js` dan `ParameterPanel.vue`.
2. Ekspor definisi lewat `defineSimulation({...})`. Kesalahan kontrak langsung melempar error
   saat modul dimuat.
3. Daftarkan di `frontend/src/simulations/index.js`:
   ```js
   import banjir from './banjir/index.js';
   export const SIMULATIONS = validateRegistry([banjir]);
   ```
   lalu hapus entri yang sama dari `PLANNED_SIMULATIONS`.
4. Jalankan `npm test` dan `npm run build`.

Tidak ada perubahan yang dibutuhkan di store, composable, `SimulationPanel.vue`, maupun legenda.

## 5. Contoh singkat (kerangka, BUKAN implementasi banjir)

```js
// frontend/src/simulations/banjir/index.js
import { defineSimulation } from '../contract.js';
import ParameterPanel from './ParameterPanel.vue';

export default defineSimulation({
  id: 'banjir',
  name: 'Simulasi banjir',
  description: 'Genangan banjir dan rob berdasarkan ketinggian muka air.',
  ParameterPanel,
  defaultParams: () => ({ mukaAir: 1.0 }), // meter di atas MSL (contoh)

  legend: (params) => [
    {
      id: 'kedalaman',
      title: `Kedalaman genangan (muka air ${params.mukaAir} m)`,
      type: 'gradient',
      unit: 'm',
      stops: [
        { value: 0, color: '#deebf7' },
        { value: 2.5, color: '#08306b' }
      ]
    }
  ],

  async createLayer({ viewer, Cesium }, params) {
    // Objek Cesium hidup di closure ini, bukan di Pinia/ref.
    const source = new Cesium.CustomDataSource('simulasi-banjir');
    await viewer.dataSources.add(source);

    const render = async (p) => {
      // TODO: ambil hasil dari backend/storage untuk p.mukaAir lalu gambar ke `source`.
    };
    await render(params);

    return {
      update: render,
      setVisible: (visible) => { source.show = visible; },
      destroy: () => {
        if (!viewer.isDestroyed()) viewer.dataSources.remove(source, true);
      }
    };
  }
});
```

```vue
<!-- frontend/src/simulations/banjir/ParameterPanel.vue -->
<template>
  <label class="block space-y-1 text-small">
    <span class="text-bontang-muted">Muka air (m)</span>
    <input
      type="range" min="0" max="3" step="0.1"
      :value="params.mukaAir" :disabled="disabled"
      @change="$emit('update:params', { mukaAir: Number($event.target.value) })"
    />
  </label>
</template>

<script setup>
defineProps({ params: { type: Object, required: true }, disabled: Boolean });
defineEmits(['update:params']);
</script>
```

Gunakan event `change` (bukan `input`) bila `update()` mahal, agar tidak memicu render ulang
di setiap pergeseran slider.
