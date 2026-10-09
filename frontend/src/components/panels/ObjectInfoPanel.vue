<template>
  <div v-if="objectStore.selectedObject" class="bg-slate-900/95 border border-slate-700/80 backdrop-blur-md rounded-xl p-4 w-80 shadow-2xl text-xs space-y-3">
    <div class="flex items-center justify-between border-b border-slate-700 pb-2">
      <div>
        <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-500/20 text-sky-400 border border-sky-400/30">
          {{ objectStore.selectedObject.identity.id }}
        </span>
        <h4 class="font-bold text-slate-100 text-sm mt-1">
          {{ objectStore.selectedObject.identity.name }}
        </h4>
      </div>
      <button @click="objectStore.clearSelection" class="text-slate-400 hover:text-slate-200 text-lg">✕</button>
    </div>

    <div class="space-y-1.5 text-slate-300">
      <div class="flex justify-between py-1 border-b border-slate-800">
        <span class="text-slate-400">Tingkat Detail:</span>
        <span class="font-medium text-slate-200">LOD {{ objectStore.selectedObject.source.lod }}</span>
      </div>
      <div class="flex justify-between py-1 border-b border-slate-800">
        <span class="text-slate-400">Tinggi Estimasi:</span>
        <span class="font-medium text-slate-200">± {{ objectStore.selectedObject.source.height }} meter</span>
      </div>
      <div class="flex justify-between py-1 border-b border-slate-800">
        <span class="text-slate-400">Kategori:</span>
        <span class="font-medium text-slate-200">{{ objectStore.selectedObject.identity.category }}</span>
      </div>
    </div>

    <div class="p-2 rounded bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-300/90 leading-tight">
      Elevasi lantai dasar (FFL) masih mengacu pada estimasi DTM lokal, belum diverifikasi survei FFL definitif.
    </div>
  </div>
</template>

<script setup>
import { useObjectStore } from '@/stores/objectStore';

const objectStore = useObjectStore();
</script>
