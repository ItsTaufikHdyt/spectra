<template>
  <div class="relative w-full h-full">
    <div id="cesiumContainer" class="w-full h-full"></div>
    <div v-if="isLoading" class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="flex flex-col items-center gap-3">
        <div class="w-10 h-10 border-4 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
        <p class="text-sky-300 font-medium text-sm">Menyiapkan Digital Twin Bontang...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { useCesium } from '@/composables/useCesium';
import { useLayers } from '@/composables/useLayers';
import { use3DTiles } from '@/composables/use3DTiles';

const isLoading = ref(true);
const { initViewer, destroyViewer } = useCesium();
const { initBasemaps } = useLayers();
const { load3DTiles, unload3DTiles, setupTilePicking, zoomToBontangKuala } = use3DTiles();

let disposed = false;

onMounted(async () => {
  await initViewer('cesiumContainer');

  // Basemap bersifat sekunder (butuh jaringan ke ArcGIS/OSM): kegagalannya
  // tidak boleh menghalangi pemuatan model 3D maupun menahan layar loading.
  try {
    await initBasemaps();
  } catch (err) {
    console.warn('[CesiumCanvas] Basemap gagal dimuat:', err.message);
  }
  if (disposed) return;

  const tileset = await load3DTiles();
  if (disposed) return;

  setupTilePicking();
  // Awal: fokus ke Bontang Kuala (instan, tanpa animasi terbang).
  if (tileset) zoomToBontangKuala({ duration: 0 });
  isLoading.value = false;
});

onBeforeUnmount(() => {
  disposed = true;
  unload3DTiles(); // handler picking, marker, watcher, tileset
  destroyViewer(); // terakhir: WebGL context
});
</script>
