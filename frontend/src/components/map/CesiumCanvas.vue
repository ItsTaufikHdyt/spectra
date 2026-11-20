<template>
  <div class="relative w-full h-full">
    <div id="cesiumContainer" ref="containerEl" class="w-full h-full"></div>

    <div v-if="status === 'loading'" class="absolute inset-0 z-40 flex items-center justify-center bg-bontang-ink/85" role="status">
      <div class="flex flex-col items-center gap-3">
        <div class="w-8 h-8 rounded-full border-2 border-bontang-line border-t-bontang-accent motion-safe:animate-spin" aria-hidden="true"></div>
        <p class="text-body text-bontang-muted">Menyiapkan peta 3D Kota Bontang…</p>
      </div>
    </div>

    <div v-else-if="status === 'error'" role="alert" class="absolute inset-0 z-40 flex items-center justify-center bg-bontang-ink/95">
      <div class="max-w-sm text-center space-y-3 p-6">
        <p class="text-title font-semibold">Peta 3D gagal dimuat</p>
        <p class="text-body text-bontang-muted">
          Penampil 3D tidak dapat dijalankan. Pastikan browser mendukung WebGL dan akselerasi
          grafis aktif, lalu coba lagi.
        </p>
        <p class="text-small text-bontang-subtle break-words">{{ errorMessage }}</p>
        <button
          type="button"
          @click="start"
          class="px-4 py-2 rounded-lg bg-bontang-accent text-bontang-accent-ink font-semibold text-body hover:brightness-110"
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
import { releaseTheme, startTheme } from '@/composables/useTheme';
import { use3DTiles } from '@/composables/use3DTiles';
import { releaseSimulation } from '@/composables/useSimulation';
import { useVectorLayers } from '@/composables/useVectorLayers';
import { useRemoteLayers } from '@/composables/useRemoteLayers';
import { releasePerfDebug, setupPerfDebug } from '@/composables/usePerfDebug';
import { releaseRenderQuality, startRenderQuality } from '@/composables/useRenderQuality';
import { useSimulationStore } from '@/stores/simulationStore';

const status = ref('loading'); // 'loading' | 'ready' | 'error'
const errorMessage = ref('');
const containerEl = ref(null); // elemen DOM biasa, bukan objek Cesium

const { initViewer, destroyViewer } = useCesium();
const { initBasemaps, releaseLayers } = useLayers();
const { load3DTiles, unload3DTiles, setupTilePicking, zoomToBontangKuala } = use3DTiles();
const simulationStore = useSimulationStore();
const { startVectorLayers, releaseVectorLayers } = useVectorLayers();
const { startRemoteLayers, releaseRemoteLayers } = useRemoteLayers();

let disposed = false;

/** Lepas resource Cesium: layer simulasi, lalu tileset, viewer terakhir (WebGL context). */
const teardown = () => {
  releasePerfDebug();
  releaseRenderQuality();
  releaseTheme();
  releaseLayers();
  releaseSimulation();
  simulationStore.reset();
  releaseVectorLayers();
  releaseRemoteLayers();
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
    startTheme(); // warna globe/latar dan gaya bangunan mengikuti tema
    startRenderQuality(); // resolusi, anti-aliasing, efek sesuai Mode tampilan
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

  // Layer vektor dimuat paralel dengan tileset (tidak saling bergantung); gagal tidak fatal.
  startVectorLayers();
  // Layer geoportal tersimpan (backend /api); backend mati -> pesan di panel, peta tetap jalan.
  startRemoteLayers();

  // Kegagalan tileset tidak fatal: load3DTiles mengembalikan null dan mengisi loadError.
  const tileset = await load3DTiles();
  if (disposed) return;

  startRenderQuality(tileset); // SSE tileset ikut Mode tampilan
  setupTilePicking();
  setupPerfDebug(tileset); // no-op tanpa ?debug=perf
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
