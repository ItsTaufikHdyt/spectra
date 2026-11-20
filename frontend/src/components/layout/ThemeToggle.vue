<template>
  <div role="group" aria-label="Tema tampilan" class="flex p-0.5 rounded-full bg-bontang-ink border border-bontang-line">
    <button
      v-for="o in OPTIONS"
      :key="o.id"
      type="button"
      :aria-pressed="themeStore.preference === o.id"
      :aria-label="o.label"
      :title="o.label"
      class="p-1.5 rounded-full"
      :class="
        themeStore.preference === o.id
          ? 'bg-bontang-accent text-bontang-accent-ink'
          : 'text-bontang-muted hover:text-bontang-text'
      "
      @click="themeStore.setPreference(o.id)"
    >
      <svg viewBox="0 0 20 20" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <path v-if="o.id === 'terang'" d="M10 3v1.5M10 15.5V17M3 10h1.5M15.5 10H17M5 5l1 1M14 14l1 1M15 5l-1 1M6 14l-1 1M10 6.5a3.5 3.5 0 100 7 3.5 3.5 0 000-7z" />
        <path v-else-if="o.id === 'gelap'" d="M16 11.5A6.5 6.5 0 018.5 4a6.5 6.5 0 107.5 7.5z" />
        <g v-else><rect x="3" y="4" width="14" height="9.5" rx="1.5" /><path d="M7 16.5h6" /></g>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { useThemeStore } from '@/stores/themeStore';

// Urutan: Terang, Gelap, Sistem (mengikuti pengaturan perangkat).
const OPTIONS = [
  { id: 'terang', label: 'Tema terang' },
  { id: 'gelap', label: 'Tema gelap' },
  { id: 'sistem', label: 'Tema mengikuti perangkat' }
];
const themeStore = useThemeStore();
</script>
