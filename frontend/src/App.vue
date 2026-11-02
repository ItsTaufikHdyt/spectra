<template>
  <div class="h-screen w-screen grid grid-rows-[auto_1fr] bg-bontang-ink text-bontang-text font-sans">
    <AppHeader
      :left-open="leftOpen"
      :right-open="rightOpen"
      @toggle-left="toggleLeft"
      @toggle-right="toggleRight"
    />

    <div class="relative flex min-h-0">
      <!-- >= 1280 px: panel ikut alur layout (peta tidak tertutup). < 1280 px: overlay, satu per satu. -->
      <Transition name="panel-left">
        <aside
          v-show="leftOpen"
          id="panel-kiri"
          aria-label="Layer dan kontrol"
          class="absolute inset-y-0 left-0 z-30 w-[296px] max-w-[85vw] shrink-0 overflow-y-auto border-r border-bontang-line bg-bontang-panel shadow-2xl xl:static xl:z-auto xl:shadow-none"
        >
          <LayerControl />
        </aside>
      </Transition>

      <main class="relative flex-1 min-w-0 select-none" aria-label="Peta 3D Kota Bontang">
        <CesiumCanvas />
        <MapLegend class="absolute left-3 bottom-3 z-20" />
      </main>

      <Transition name="panel-right">
        <aside
          v-show="rightOpen"
          id="panel-kanan"
          aria-label="Informasi objek terpilih"
          class="absolute inset-y-0 right-0 z-30 w-[320px] max-w-[85vw] shrink-0 overflow-y-auto border-l border-bontang-line bg-bontang-panel shadow-2xl xl:static xl:z-auto xl:shadow-none"
        >
          <ObjectInfoPanel />
        </aside>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue';
import AppHeader from '@/components/layout/AppHeader.vue';
import CesiumCanvas from '@/components/map/CesiumCanvas.vue';
import MapLegend from '@/components/map/MapLegend.vue';
import LayerControl from '@/components/panels/LayerControl.vue';
import ObjectInfoPanel from '@/components/panels/ObjectInfoPanel.vue';
import { useObjectStore } from '@/stores/objectStore';

// Breakpoint `xl` Tailwind (1280 px): di atasnya kedua panel boleh terbuka bersamaan.
const wideQuery = window.matchMedia('(min-width: 1280px)');
const isWide = ref(wideQuery.matches);
const leftOpen = ref(isWide.value);
const rightOpen = ref(isWide.value);

const onWideChange = (e) => {
  isWide.value = e.matches;
  leftOpen.value = e.matches;
  rightOpen.value = e.matches;
};
wideQuery.addEventListener('change', onWideChange);
onBeforeUnmount(() => wideQuery.removeEventListener('change', onWideChange));

// Layar sempit: dua overlay sekaligus akan menutupi peta, jadi buka satu, tutup yang lain.
const toggleLeft = () => {
  leftOpen.value = !leftOpen.value;
  if (!isWide.value && leftOpen.value) rightOpen.value = false;
};
const toggleRight = () => {
  rightOpen.value = !rightOpen.value;
  if (!isWide.value && rightOpen.value) leftOpen.value = false;
};

// Objek baru dipilih -> pastikan panel informasi terlihat.
const objectStore = useObjectStore();
watch(
  () => objectStore.selectedObject,
  (obj) => {
    if (obj && !rightOpen.value) toggleRight();
  }
);
</script>
