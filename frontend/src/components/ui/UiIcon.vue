<template>
  <svg viewBox="0 0 20 20" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path v-for="(d, i) in PATHS[name]" :key="i" :d="d" />
  </svg>
</template>

<script setup>
// Ikon garis inline. Selalu dekoratif: tombol pemakainya wajib punya aria-label.
defineProps({ name: { type: String, required: true } });

const PATHS = {
  'panel-left': ['M3.5 4.5h13a1 1 0 011 1v9a1 1 0 01-1 1h-13a1 1 0 01-1-1v-9a1 1 0 011-1z', 'M7.5 4.5v11'],
  'panel-right': ['M3.5 4.5h13a1 1 0 011 1v9a1 1 0 01-1 1h-13a1 1 0 01-1-1v-9a1 1 0 011-1z', 'M12.5 4.5v11'],
  info: ['M10 17.5a7.5 7.5 0 100-15 7.5 7.5 0 000 15z', 'M10 9v4.5', 'M10 6.5v.01'],
  plus: ['M10 4.5v11', 'M4.5 10h11'],
  minus: ['M4.5 10h11'],
  city: ['M3 17V8l5-2v11', 'M8 17V4l6 2.5V17', 'M14 17V9l3 1v7', 'M2 17h16'],
  search: ['M9 15a6 6 0 100-12 6 6 0 000 12z', 'M13.5 13.5L17 17'],
  close: ['M5 5l10 10', 'M15 5L5 15'],
  chevron: ['M5 12.5l5-5 5 5']
};
</script>
