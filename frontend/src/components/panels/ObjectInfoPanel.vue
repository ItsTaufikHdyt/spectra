<template>
  <div v-if="selected" class="bg-slate-900/95 border border-slate-700/80 backdrop-blur-md rounded-xl p-4 w-80 shadow-2xl text-xs space-y-3">
    <div class="flex items-start justify-between border-b border-slate-700 pb-2">
      <div>
        <h4 class="font-bold text-slate-100 text-sm">{{ displayName }}</h4>
        <p class="text-slate-400 mt-0.5">Kel. {{ selected.identity.kelurahan }} · {{ selected.identity.category }}</p>
      </div>
      <button type="button" aria-label="Tutup informasi objek" @click="objectStore.clearSelection()" class="text-slate-400 hover:text-slate-200 text-lg">✕</button>
    </div>

    <!-- Atribut bangunan: tampilkan state, bukan baris "Tidak tersedia" berulang. -->
    <div v-if="objectStore.attributeStatus === 'ready'" class="space-y-1">
      <div v-for="row in attributeRows" :key="row.key" class="flex justify-between gap-3">
        <span class="text-slate-400">{{ row.key }}</span>
        <span class="text-slate-200 text-right break-all">{{ row.value }}</span>
      </div>
    </div>
    <p v-else-if="objectStore.attributeStatus === 'loading'" class="text-slate-400">Memuat atribut bangunan...</p>
    <div v-else-if="objectStore.attributeStatus === 'error'" class="p-2 rounded bg-red-500/10 border border-red-500/30 text-red-200 space-y-1">
      <p>Atribut gagal dimuat: {{ objectStore.attributeError }}</p>
      <button type="button" class="underline" @click="objectStore.retryAttributes()">Coba lagi</button>
    </div>
    <div v-else class="p-3 rounded-lg bg-slate-800/60 border border-slate-700 space-y-1">
      <p class="font-semibold text-slate-200">Data atribut belum tersedia</p>
      <p class="text-slate-400 leading-snug">
        Model 3D belum membawa nama, tinggi, dan fungsi bangunan. Informasi ini akan tampil di sini
        setelah data atribut tersambung.
      </p>
    </div>

    <div v-if="selected.location" class="space-y-1 text-slate-300">
      <div class="flex justify-between"><span class="text-slate-400">Bujur</span><span>{{ formatDegrees(selected.location.longitude) }}</span></div>
      <div class="flex justify-between"><span class="text-slate-400">Lintang</span><span>{{ formatDegrees(selected.location.latitude) }}</span></div>
      <div class="flex justify-between"><span class="text-slate-400">Elevasi titik klik</span><span>{{ formatWithUnit(selected.location.elevation, 'm') }}</span></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useObjectStore } from '@/stores/objectStore';
import { ATTRIBUTE_KEYS } from '@/services/buildingAttributes';
import { pickFirst } from '@/utils/tileMeta';
import { formatDegrees, formatNumber, formatWithUnit } from '@/utils/format';

const objectStore = useObjectStore();
const selected = computed(() => objectStore.selectedObject);

const displayName = computed(() => {
  const name = objectStore.attributes ? pickFirst(objectStore.attributes, ATTRIBUTE_KEYS.name) : undefined;
  return name ?? selected.value?.identity.name;
});

const attributeRows = computed(() =>
  Object.entries(objectStore.attributes ?? {}).map(([key, value]) => ({
    key,
    value: typeof value === 'number' ? formatNumber(value, { maxDigits: 3 }) : String(value)
  }))
);
</script>
