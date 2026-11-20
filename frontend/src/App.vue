<template>
  <div class="h-screen w-screen flex flex-col bg-bontang-ink text-bontang-text font-sans">
    <AppHeader :left-open="leftOpen" :right-open="rightOpen" @toggle-left="toggleLeft" @toggle-right="toggleRight" />

    <div class="relative flex-1 min-h-0 flex gap-3 px-3 pb-3">
      <!-- >= 1280 px: panel ikut alur layout (peta tidak tertutup). < 1280 px: laci overlay, satu per satu. -->
      <Transition name="panel-left">
        <aside
          v-show="leftOpen"
          id="panel-kiri"
          aria-label="Layer dan kontrol"
          class="absolute inset-y-0 left-3 z-30 w-[288px] max-w-[92vw] overflow-y-auto rounded-2xl border border-bontang-line bg-bontang-ink shadow-2xl xl:static xl:z-auto xl:shrink-0 xl:border-0 xl:bg-transparent xl:shadow-none"
        >
          <LayerControl />
        </aside>
      </Transition>

      <main class="relative flex-1 min-w-0 select-none overflow-hidden rounded-3xl border border-bontang-line" aria-label="Peta 3D Kota Bontang">
        <CesiumCanvas />
        <MapOverlay />
      </main>

      <Transition name="panel-right">
        <aside
          v-show="rightOpen"
          id="panel-kanan"
          aria-label="Informasi objek dan legenda"
          class="absolute inset-y-0 right-3 z-30 w-[320px] max-w-[92vw] overflow-y-auto rounded-2xl border border-bontang-line bg-bontang-ink p-2 shadow-2xl space-y-3 md:right-20 xl:static xl:z-auto xl:shrink-0 xl:border-0 xl:bg-transparent xl:p-0 xl:shadow-none"
        >
          <MapLegend />
          <div class="rounded-2xl border border-bontang-line bg-bontang-panel">
            <ObjectInfoPanel />
          </div>
        </aside>
      </Transition>

      <AppRail :open="rightOpen" :has-selection="!!objectStore.selectedObject" @toggle="toggleRight" />
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue';
import AppHeader from '@/components/layout/AppHeader.vue';
import AppRail from '@/components/layout/AppRail.vue';
import CesiumCanvas from '@/components/map/CesiumCanvas.vue';
import MapLegend from '@/components/map/MapLegend.vue';
import MapOverlay from '@/components/map/MapOverlay.vue';
import LayerControl from '@/components/panels/LayerControl.vue';
import ObjectInfoPanel from '@/components/panels/ObjectInfoPanel.vue';
import { useObjectStore } from '@/stores/objectStore';

// Breakpoint `xl` Tailwind (1280 px): di atasnya panel kiri ikut alur layout.
const wideQuery = window.matchMedia('(min-width: 1280px)');
const isWide = ref(wideQuery.matches);
const leftOpen = ref(isWide.value);
// Panel kanan tidak terbuka sendiri: hanya saat objek dipilih atau lewat rail.
const rightOpen = ref(false);
const objectStore = useObjectStore();

const onWideChange = (e) => {
  isWide.value = e.matches;
  leftOpen.value = e.matches;
  if (!e.matches) rightOpen.value = false;
};
wideQuery.addEventListener('change', onWideChange);

// Fokus kembali ke tombol pembuka saat laci ditutup lewat keyboard/tombol.
let opener = null;
const restoreFocus = () => nextTick(() => { opener?.focus?.(); opener = null; });

// Layar sempit: dua overlay sekaligus akan menutupi peta, jadi buka satu, tutup yang lain.
const toggleLeft = () => {
  leftOpen.value = !leftOpen.value;
  if (leftOpen.value) opener = document.activeElement;
  else restoreFocus();
  if (!isWide.value && leftOpen.value) rightOpen.value = false;
};
const toggleRight = () => {
  rightOpen.value = !rightOpen.value;
  if (rightOpen.value) opener = document.activeElement;
  else restoreFocus();
  if (!isWide.value && rightOpen.value) leftOpen.value = false;
};

// Esc menutup laci overlay (di layar lebar panel kanan juga bisa ditutup dengan Esc).
const onKey = (e) => {
  if (e.key !== 'Escape' || e.defaultPrevented) return;
  if (rightOpen.value) toggleRight();
  else if (leftOpen.value && !isWide.value) toggleLeft();
};
window.addEventListener('keydown', onKey);
onBeforeUnmount(() => {
  wideQuery.removeEventListener('change', onWideChange);
  window.removeEventListener('keydown', onKey);
});

// Objek baru dipilih -> pastikan panel informasi terlihat.
watch(
  () => objectStore.selectedObject,
  (obj) => {
    if (!obj || rightOpen.value) return;
    rightOpen.value = true;
    if (!isWide.value) leftOpen.value = false;
  }
);
</script>
