<template>
  <div class="space-y-3">
    <CuacaKartu />
    <GempaKartu />
    <HotspotKartu />
    <LautKartu />
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, watch } from 'vue';
import GempaKartu from '@/components/terkini/GempaKartu.vue';
import CuacaKartu from '@/components/terkini/CuacaKartu.vue';
import HotspotKartu from '@/components/terkini/HotspotKartu.vue';
import LautKartu from '@/components/terkini/LautKartu.vue';
import { startTerkini, stopTerkini } from '@/composables/useTerkini';
import { useObjectStore } from '@/stores/objectStore';
import { useTerkiniStore } from '@/stores/terkiniStore';
import { use3DTiles } from '@/composables/use3DTiles';

// Polling hanya berjalan selama komponen ini terpasang (tab Kondisi terlihat); tidak menyentuh Cesium.
onMounted(startTerkini);
onBeforeUnmount(stopTerkini);

// Bangunan terpilih -> cuaca mengikuti kelurahannya (nama kelurahan dari panel -> slug dari daftar model 3D).
const objectStore = useObjectStore();
const store = useTerkiniStore();
const { kelurahanList } = use3DTiles();
watch(
  () => objectStore.selectedObject?.identity?.kelurahan,
  (nama) => {
    const k = kelurahanList.value.find((x) => x.name === nama);
    if (k) store.pilihKelurahan(k.slug);
  }
);
</script>
