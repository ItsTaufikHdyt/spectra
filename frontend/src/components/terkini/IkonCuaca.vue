<template>
  <svg v-if="ikon" viewBox="0 0 32 32" class="shrink-0" :class="ukuran" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" role="img" :aria-label="label">
    <g v-if="ikon === 'cerah'" class="text-bontang-warn"><circle cx="16" cy="16" r="5" /><g class="ik-putar"><path d="M16 4v3M16 25v3M4 16h3M25 16h3M7.5 7.5l2 2M22.5 22.5l2 2M24.5 7.5l-2 2M9.5 22.5l-2 2" /></g></g>
    <path v-else-if="ikon === 'cerah-malam'" d="M24 19A9 9 0 0113 8a9 9 0 1011 11z" class="text-bontang-accent ik-napas" />
    <template v-else-if="ikon === 'cerah-berawan'"><g class="text-bontang-warn"><circle cx="12" cy="12" r="4" /><g class="ik-putar"><path d="M12 3v2M3 12h2M5.6 5.6l1.4 1.4M18.4 5.6L17 7" /></g></g><path class="ik-melayang" d="M10 26h13a5 5 0 000-10 7 7 0 00-13.5 1.5A4.3 4.3 0 0010 26z" /></template>
    <template v-else-if="ikon === 'cerah-berawan-malam'"><path d="M16 11A6 6 0 019 4a6 6 0 108 7z" class="text-bontang-accent ik-napas" /><path class="ik-melayang" d="M10 26h13a5 5 0 000-10 7 7 0 00-13.5 1.5A4.3 4.3 0 0010 26z" /></template>
    <path v-else-if="ikon === 'berawan'" class="ik-melayang" d="M8 24h16a5 5 0 000-10 8 8 0 00-15.5 2A4 4 0 008 24z" />
    <template v-else-if="ikon === 'hujan'"><path d="M8 18h16a5 5 0 000-10 8 8 0 00-15.5 2A4 4 0 008 18z" /><g class="text-bontang-accent"><path class="ik-tetes" d="M11 21l-1.5 4" /><path class="ik-tetes t2" d="M16 21l-1.5 4" /><path class="ik-tetes t3" d="M21 21l-1.5 4" /></g></template>
    <template v-else-if="ikon === 'petir'"><path d="M8 17h16a5 5 0 000-10 8 8 0 00-15.5 2A4 4 0 008 17z" /><path class="ik-kilat text-bontang-warn" d="M17 18l-4 6h4l-2 5" /></template>
    <g v-else-if="ikon === 'kabut'"><path d="M6 11h20M4 17h20M8 23h20" class="ik-geser" /></g>
  </svg>
</template>

<script setup>
import { computed } from 'vue';
import { ikonCuaca } from '@/utils/terkini';

const props = defineProps({
  cuaca: { type: String, default: '' },
  waktuLokal: { type: String, default: '' },
  ukuran: { type: String, default: 'w-8 h-8' }
});
const ikon = computed(() => ikonCuaca(props.cuaca, props.waktuLokal));
const label = computed(() => props.cuaca);
</script>

<style scoped>
/* Animasi singkat (berhingga, ≤ 6 dtk) saat ikon muncul, lalu diam: animasi tanpa henti terukur menambah beban GPU (compositor)
   di atas kanvas. Hanya transform/opacity, dan hanya bila pengguna tidak meminta gerak berkurang. */
@media (prefers-reduced-motion: no-preference) {
  .ik-putar { transform-origin: 16px 16px; animation: ik-putar 6s ease-in-out 1; }
  .ik-napas { animation: ik-napas 2s ease-in-out 2; }
  .ik-melayang { animation: ik-melayang 3s ease-in-out 1; }
  .ik-tetes { animation: ik-tetes 1.2s linear 4; }
  .ik-tetes.t2 { animation-delay: 0.45s; }
  .ik-tetes.t3 { animation-delay: 0.9s; }
  .ik-kilat { animation: ik-kilat 2.5s ease-in-out 2; }
  .ik-geser { animation: ik-melayang 3s ease-in-out 1; }
}
@keyframes ik-putar { to { transform: rotate(360deg); } }
@keyframes ik-napas { 50% { opacity: 0.6; } }
@keyframes ik-melayang { 50% { transform: translateX(1.5px); } }
@keyframes ik-tetes { 0% { transform: translateY(-2px); opacity: 0; } 30% { opacity: 1; } 100% { transform: translateY(4px); opacity: 0; } }
@keyframes ik-kilat { 0%, 70%, 100% { opacity: 1; } 78% { opacity: 0.2; } 86% { opacity: 1; } }
</style>
