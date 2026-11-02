<template>
  <div class="relative w-full h-full">
    <div id="cesiumContainer" ref="containerEl" class="w-full h-full"></div>

    <div v-if="status === 'loading'" class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="flex flex-col items-center gap-3">
        <div class="w-10 h-10 border-4 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
        <p class="text-sky-300 font-medium text-sm">Menyiapkan Digital Twin Bontang...</p>
      </div>
    </div>

    <div v-else-if="status === 'error'" role="alert" class="absolute inset-0 bg-slate-950/90 flex items-center justify-center z-50">
      <div class="max-w-sm text-center space-y-3 p-6">
        <p class="text-slate-100 font-semibold">Peta 3D gagal dimuat</p>
        <p class="text-slate-400 text-sm">
          Penampil 3D tidak dapat dijalankan. Pastikan browser mendukung WebGL dan akselerasi
          grafis aktif.
        </p>
        <p class="text-slate-500 text-xs font-mono break-words">{{ errorMessage }}</p>
        <button
          type="button"
          @click="start"
          class="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm"
        >
          Coba lagi
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { useCesium } from '@/composables/useCesium';
import { useLayers } from '@/composables/useLayers';
import { use3DTiles } from '@/composables/use3DTiles';

const status = ref('loading'); // 'loading' | 'ready' | 'error'
const errorMessage = ref('');
const containerEl = ref(null); // elemen DOM biasa, bukan objek Cesium

const { initViewer, destroyViewer } = useCesium();
const { initBasemaps } = useLayers();
const { load3DTiles, unload3DTiles, setupTilePicking, zoomToBontangKuala } = use3DTiles();

let disposed = false;

/** Lepas resource Cesium: tileset dulu, viewer terakhir (WebGL context). */
const teardown = () => {
  unload3DTiles();
  destroyViewer();
};

const start = async () => {
  status.value = 'loading';
  errorMessage.value = '';
  try {
    teardown(); // sisa percobaan sebelumnya (jika ada)
    containerEl.value?.replaceChildren(); // panel error/canvas parsial dari init yang gagal
    await initViewer(containerEl.value);
  } catch (err) {
    console.error('[CesiumCanvas] Viewer gagal diinisialisasi:', err);
    teardown();
    if (disposed) return;
    errorMessage.value = err?.message ?? String(err);
    status.value = 'error';
    return;
  }

  // Basemap bersifat sekunder (butuh jaringan ke ArcGIS/OSM): kegagalannya
  // tidak boleh menghalangi pemuatan model 3D maupun menahan layar loading.
  try {
    await initBasemaps();
  } catch (err) {
    console.warn('[CesiumCanvas] Basemap gagal dimuat:', err.message);
  }
  if (disposed) return;

  // Kegagalan tileset tidak fatal: load3DTiles mengembalikan null dan mengisi loadError.
  const tileset = await load3DTiles();
  if (disposed) return;

  setupTilePicking();
  // Awal: fokus ke Bontang Kuala (instan, tanpa animasi terbang).
  if (tileset) zoomToBontangKuala({ duration: 0 });
  status.value = 'ready';
};

onMounted(start);

onBeforeUnmount(() => {
  disposed = true;
  teardown(); // handler picking, marker, watcher, tileset -> lalu viewer
});
</script>
