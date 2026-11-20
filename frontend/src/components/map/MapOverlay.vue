<template>
  <!-- Overlay di atas kanvas: solid/semitransparan, tanpa backdrop-filter (murah untuk WebGL). -->
  <div class="pointer-events-none absolute inset-0 z-20">
    <!-- Mode kamera -->
    <div role="group" aria-label="Mode tampilan kamera" class="pointer-events-auto absolute left-3 top-3 flex p-1 rounded-xl border border-bontang-line bg-bontang-panel shadow-md">
      <button
        v-for="m in VIEW_MODES"
        :key="m.id"
        type="button"
        class="px-3 py-1 rounded-lg text-small font-semibold"
        :class="mode === m.id ? 'bg-bontang-accent text-bontang-accent-ink' : 'text-bontang-muted hover:text-bontang-text'"
        :aria-pressed="mode === m.id"
        :title="m.title"
        @click="setViewMode(m.id)"
      >
        {{ m.label }}
      </button>
    </div>

    <!-- Kontrol peta -->
    <div role="group" aria-label="Kontrol peta" class="pointer-events-auto absolute right-3 top-3 flex flex-col gap-1.5">
      <div class="flex flex-col rounded-xl border border-bontang-line bg-bontang-panel shadow-md overflow-hidden divide-y divide-bontang-line">
        <button type="button" class="map-btn" aria-label="Perbesar" title="Perbesar" @click="zoomIn"><UiIcon name="plus" /></button>
        <button type="button" class="map-btn" aria-label="Perkecil" title="Perkecil" @click="zoomOut"><UiIcon name="minus" /></button>
      </div>
      <button
        type="button"
        class="map-btn rounded-xl border border-bontang-line bg-bontang-panel shadow-md"
        :aria-label="`Kompas, arah ${Math.round(headingDeg)}°. Klik untuk menghadap utara`"
        title="Menghadap utara"
        @click="resetNorth"
      >
        <svg viewBox="0 0 20 20" class="w-5 h-5" :style="{ transform: `rotate(${-headingDeg}deg)` }" aria-hidden="true">
          <path d="M10 2.5l3 7.5H7z" fill="rgb(var(--bontang-danger))" />
          <path d="M10 17.5L7 10h6z" fill="currentColor" opacity="0.55" />
        </svg>
      </button>
      <button type="button" class="map-btn rounded-xl border border-bontang-line bg-bontang-panel shadow-md" aria-label="Tampilkan seluruh kota" title="Tampilkan seluruh kota" :disabled="!tilesetRef" @click="zoomToKota">
        <UiIcon name="city" />
      </button>
    </div>

    <!-- Skala dan koordinat -->
    <div class="absolute left-3 bottom-10 flex flex-col items-start gap-1.5">
      <div v-if="scaleBar" class="px-2 py-1 rounded-lg bg-bontang-panel/90 text-caption text-bontang-text tabular-nums" role="img" :aria-label="`Skala ${scaleBar.label}`">
        <div class="h-1.5 border-x-2 border-b-2 border-bontang-text" :style="{ width: `${scaleBar.widthPx}px` }"></div>
        {{ scaleBar.label }}
      </div>
      <p
        v-if="cursorText"
        class="hidden sm:block px-2 py-1 rounded-lg bg-bontang-panel/90 text-caption text-bontang-text tabular-nums"
        title="Posisi pada permukaan bumi (elipsoid), bukan di atas bangunan"
      >
        {{ cursorText }}
        <span class="text-bontang-muted">· permukaan bumi</span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import UiIcon from '@/components/ui/UiIcon.vue';
import { use3DTiles } from '@/composables/use3DTiles';
import { cursorText, headingDeg, pitchDeg, scaleBar, useMapControls } from '@/composables/useMapControls';

const VIEW_MODES = [
  { id: '3d', label: '3D', title: 'Tampilan miring 3D' },
  { id: 'atas', label: 'Atas', title: 'Menghadap lurus ke bawah (bukan peta 2D)' }
];
const { zoomIn, zoomOut, resetNorth, setViewMode } = useMapControls();
const { tilesetRef, zoomToKota } = use3DTiles();
const mode = computed(() => (pitchDeg.value < -80 ? 'atas' : '3d'));
</script>

<style scoped>
.map-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: rgb(var(--bontang-text));
}
.map-btn:hover:not(:disabled) {
  background: rgb(var(--bontang-raised));
}
.map-btn:disabled {
  opacity: 0.5;
}
</style>
