<template>
  <div class="bg-slate-900/90 border border-slate-700/80 backdrop-blur-md rounded-xl p-4 w-72 shadow-2xl text-xs space-y-4">
    <div class="border-b border-slate-700 pb-2">
      <h3 class="font-bold text-sm text-sky-400 tracking-wide">PENGELOLAAN LAYER</h3>
      <p class="text-slate-400 text-[11px]">Digital Twin Kota Bontang</p>
    </div>

    <!-- Basemap Switcher -->
    <div class="space-y-2">
      <span class="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Basemap Satelit</span>
      <div class="grid grid-cols-2 gap-2">
        <button
          @click="mapStore.setBasemap('arcgis')"
          :class="mapStore.activeBasemap === 'arcgis' ? 'bg-sky-500 text-white font-semibold' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'"
          class="px-2.5 py-1.5 rounded-lg border border-slate-700 transition"
        >
          ArcGIS Satellite
        </button>
        <button
          @click="mapStore.setBasemap('osm')"
          :class="mapStore.activeBasemap === 'osm' ? 'bg-sky-500 text-white font-semibold' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'"
          class="px-2.5 py-1.5 rounded-lg border border-slate-700 transition"
        >
          OpenStreetMap
        </button>
      </div>
    </div>

    <!-- Toggle Terrain & 3D Tiles -->
    <div class="space-y-2">
      <span class="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Model & Medan 3D</span>
      <div class="space-y-1.5">
        <label class="flex items-center justify-between p-2 rounded-lg bg-slate-800/80 border border-slate-700/60 cursor-pointer">
          <span class="text-slate-200">DTM Terrain 3D</span>
          <input type="checkbox" v-model="mapStore.isTerrainActive" class="rounded text-sky-500 focus:ring-0 w-4 h-4" />
        </label>
        <label class="flex items-center justify-between p-2 rounded-lg bg-slate-800/80 border border-slate-700/60 cursor-pointer">
          <span class="text-slate-200">Model 3D Tiles Bangunan</span>
          <input type="checkbox" v-model="mapStore.is3DTilesActive" class="rounded text-sky-500 focus:ring-0 w-4 h-4" />
        </label>
      </div>
    </div>

    <!-- Quick Navigation Button -->
    <button
      @click="flyToBontang"
      class="w-full py-2 bg-slate-800 hover:bg-sky-600/90 border border-slate-600 text-slate-100 rounded-lg font-medium transition text-center shadow"
    >
      Fokus ke Kawasan Bontang
    </button>

    <!-- Fokus ke Tileset Bontang Kuala -->
    <button
      @click="zoomToBontangKuala"
      class="w-full py-2 bg-sky-600/90 hover:bg-sky-500 border border-sky-500 text-white rounded-lg font-semibold transition text-center shadow"
    >
      Fokus ke Bontang Kuala
    </button>
  </div>
</template>

<script setup>
import { useMapStore } from '@/stores/mapStore';
import { useCesium } from '@/composables/useCesium';
import { use3DTiles } from '@/composables/use3DTiles';

const mapStore = useMapStore();
const { flyToBontang } = useCesium();
const { zoomToBontangKuala } = use3DTiles();
</script>
