<template>
  <div v-if="sections.length" class="w-60 rounded-lg border border-bontang-line bg-bontang-panel/95 text-small shadow-lg">
    <button
      type="button"
      class="w-full flex items-center justify-between px-3 py-2 font-semibold"
      :aria-expanded="open"
      aria-controls="isi-legenda"
      @click="open = !open"
    >
      Legenda
      <svg viewBox="0 0 20 20" class="w-4 h-4 text-bontang-muted motion-safe:transition-transform" :class="open ? '' : 'rotate-180'" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <path d="M5 12.5l5-5 5 5" />
      </svg>
    </button>

    <div v-show="open" id="isi-legenda" class="px-3 pb-3 space-y-3 max-h-[40vh] overflow-y-auto">
      <section v-for="s in sections" :key="s.id" class="space-y-1.5">
        <h3 class="text-caption font-semibold text-bontang-muted">{{ s.title }}</h3>

        <ul v-if="s.type === 'categorical'" class="space-y-1">
          <li v-for="item in s.items" :key="item.label" class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 shrink-0" :class="swatchClass(item.shape)" :style="swatchStyle(item)" aria-hidden="true"></span>
            <span>{{ item.label }}</span>
          </li>
        </ul>

        <div v-else-if="s.type === 'gradient'" class="space-y-1">
          <div class="h-2.5 rounded-sm" :style="{ background: gradientCss(s.stops) }" aria-hidden="true"></div>
          <div class="flex justify-between text-caption text-bontang-muted tabular-nums">
            <span>{{ formatNumber(s.stops[0].value) }} {{ s.unit }}</span>
            <span>{{ formatNumber(s.stops[s.stops.length - 1].value) }} {{ s.unit }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useLegend } from '@/composables/useLegend';
import { formatNumber } from '@/utils/format';

const open = ref(true);
const { sections } = useLegend();

const swatchClass = (shape) =>
  ({ dot: 'rounded-full scale-75', outline: 'rounded-sm border-2', fill: 'rounded-sm' })[shape] ?? 'rounded-sm';

const swatchStyle = (item) =>
  item.shape === 'outline' ? { borderColor: item.color } : { backgroundColor: item.color };

/** Stop -> linear-gradient CSS dengan posisi proporsional terhadap nilai. */
const gradientCss = (stops) => {
  const min = stops[0].value;
  const span = stops[stops.length - 1].value - min || 1;
  const parts = stops.map((s) => `${s.color} ${(((s.value - min) / span) * 100).toFixed(1)}%`);
  return `linear-gradient(to right, ${parts.join(', ')})`;
};
</script>
