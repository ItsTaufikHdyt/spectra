<template>
  <div class="relative w-screen h-screen overflow-hidden bg-slate-950 font-sans">
    <!-- Cesium 3D Viewport -->
    <CesiumCanvas />

    <!-- Topbar Header -->
    <header class="absolute top-4 left-4 z-40 bg-slate-900/90 border border-slate-700/80 backdrop-blur-md px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-3">
      <div class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></div>
      <div>
        <h1 class="text-sm font-bold text-slate-100 tracking-wide uppercase">Digital Twin Kota Bontang</h1>
        <p class="text-[10px] text-slate-400 font-medium">3D Web GIS Platform &bull; CesiumJS & Vue 3</p>
      </div>
    </header>

    <!-- Floating UI Panels -->
    <div class="absolute top-20 left-4 z-40">
      <LayerControl />
    </div>

    <div class="absolute bottom-6 right-4 z-40">
      <ObjectInfoPanel />
    </div>
  </div>
</template>

<script setup>
import CesiumCanvas from '@/components/map/CesiumCanvas.vue';
import LayerControl from '@/components/panels/LayerControl.vue';
import ObjectInfoPanel from '@/components/panels/ObjectInfoPanel.vue';
</script>
