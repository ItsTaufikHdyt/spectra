<template>
  <UiCard v-if="sections.length" title="Legenda" collapsible>
    <div class="space-y-3 max-h-[40vh] overflow-y-auto text-small">
      <section v-for="s in sections" :key="s.id" class="space-y-1.5">
        <h3 class="text-caption font-semibold text-bontang-muted">{{ s.title }}</h3>

        <ul v-if="s.type === 'categorical'" class="space-y-1">
          <li v-for="item in s.items" :key="item.label" class="flex items-center gap-2">
            <span class="w-3.5 shrink-0" :class="swatchClass(item.shape)" :style="swatchStyle(item)" aria-hidden="true"></span>
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
  </UiCard>
</template>

<script setup>
import UiCard from '@/components/ui/UiCard.vue';
import { useLegend } from '@/composables/useLegend';
import { formatNumber } from '@/utils/format';

const { sections } = useLegend();

const swatchClass = (shape) =>
  ({
    dot: 'h-3.5 rounded-full scale-75',
    outline: 'h-3.5 rounded-sm border-2',
    fill: 'h-3.5 rounded-sm',
    line: 'h-[3px] rounded-full',
    'line-thin': 'h-px'
  })[shape] ?? 'h-3.5 rounded-sm';

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
