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
import { onMounted, ref } from 'vue';
import { useCesium } from '@/composables/useCesium';
import { useLayers } from '@/composables/useLayers';
import { use3DTiles } from '@/composables/use3DTiles';

const isLoading = ref(true);
const { initViewer } = useCesium();
const { initBasemaps } = useLayers();
const { load3DTiles, setupTilePicking, zoomToBontangKuala } = use3DTiles();

onMounted(async () => {
  await initViewer('cesiumContainer');
  await initBasemaps();
  const tileset = await load3DTiles('/tiles/bontang_kuala/tileset.json');
  setupTilePicking();
  // Arahkan kamera ke tileset Bontang Kuala jika berhasil dimuat.
  if (tileset) {
    zoomToBontangKuala();
  }
  isLoading.value = false;
});
</script>
