<template>
  <svg viewBox="0 0 24 24" class="w-5 h-5 shrink-0 text-bontang-accent" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path v-if="nama === 'gempa'" class="ik-denyut" d="M2 12h4l2-6 4 12 3-9 2 3h5" />
    <path v-else-if="nama === 'cuaca'" d="M7 18h10a4 4 0 000-8 6 6 0 00-11.6 1.6A3.3 3.3 0 007 18z" />
    <path v-else-if="nama === 'hotspot'" class="ik-api" d="M12 3c1 3 4 4.5 4 8.5a4 4 0 01-8 0c0-1.5.6-2.6 1.5-3.5.2 1.2.8 1.8 1.5 2C11 8.5 11 5.5 12 3zM12 21a3 3 0 003-3c0-1.4-1.5-2-3-3.5C10.5 16 9 16.6 9 18a3 3 0 003 3z" />
    <path v-else-if="nama === 'laut'" class="ik-ombak" d="M2 9c2-2 4-2 6 0s4 2 6 0 4-2 6 0M2 15c2-2 4-2 6 0s4 2 6 0 4-2 6 0" />
  </svg>
</template>

<script setup>
defineProps({ nama: { type: String, required: true } }); // gempa | cuaca | hotspot | laut
</script>

<style scoped>
@media (prefers-reduced-motion: no-preference) {
  .ik-denyut { stroke-dasharray: 40; animation: ik-denyut 2.5s ease-in-out 1; }
  .ik-api { transform-origin: 12px 20px; animation: ik-api 1.5s ease-in-out 3; }
  .ik-ombak { animation: ik-ombak 2s ease-in-out 2; }
}
@keyframes ik-denyut { 0% { stroke-dashoffset: 40; } 45%, 100% { stroke-dashoffset: 0; } }
@keyframes ik-api { 50% { transform: scale(1.06, 0.94); } }
@keyframes ik-ombak { 50% { transform: translateX(2px); } }
</style>
