<template>
  <header class="flex items-center gap-3 px-4 h-14 shrink-0">
    <button
      type="button"
      class="hdr-btn"
      :aria-expanded="leftOpen"
      aria-controls="panel-kiri"
      :aria-label="leftOpen ? 'Sembunyikan panel layer' : 'Tampilkan panel layer'"
      :title="leftOpen ? 'Sembunyikan panel layer' : 'Tampilkan panel layer'"
      @click="$emit('toggle-left')"
    >
      <UiIcon name="panel-left" />
    </button>

    <!-- Identitas spectra -->
    <div class="flex items-center gap-2 shrink-0" aria-hidden="true">
      <svg viewBox="0 0 24 24" class="w-6 h-6 text-bontang-accent" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linejoin="round">
        <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z" />
        <path d="M4 7.5l8 4.5 8-4.5M12 12v9" />
      </svg>
      <span class="text-title font-bold tracking-tight">spectra</span>
    </div>

    <!-- Judul aplikasi + status: di tengah, menggantikan pil navigasi pada referensi -->
    <div class="flex-1 min-w-0 flex flex-col items-center text-center leading-tight">
      <h1 class="sr-only sm:not-sr-only text-title md:text-display font-bold tracking-tight truncate max-w-full">Digital Twin Kota Bontang</h1>
      <p class="hidden sm:flex items-center gap-1.5 text-caption text-bontang-muted" role="status">
        <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass" aria-hidden="true"></span>
        <span class="truncate">{{ statusText }}</span>
      </p>
    </div>

    <div class="hidden md:block flex-1 max-w-[260px]"><KelurahanSearch /></div>
    <ThemeToggle />

    <!-- < 768 px rail disembunyikan: tombol panel kanan pindah ke header -->
    <button
      type="button"
      class="hdr-btn md:hidden"
      :aria-expanded="rightOpen"
      aria-controls="panel-kanan"
      :aria-label="rightOpen ? 'Sembunyikan panel informasi' : 'Tampilkan panel informasi'"
      @click="$emit('toggle-right')"
    >
      <UiIcon name="panel-right" />
    </button>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { use3DTiles } from '@/composables/use3DTiles';
import { formatNumber } from '@/utils/format';
import ThemeToggle from '@/components/layout/ThemeToggle.vue';
import KelurahanSearch from '@/components/layout/KelurahanSearch.vue';
import UiIcon from '@/components/ui/UiIcon.vue';

defineProps({
  leftOpen: { type: Boolean, required: true },
  rightOpen: { type: Boolean, required: true }
});
defineEmits(['toggle-left', 'toggle-right']);

const { kelurahanList, loadError } = use3DTiles();

const status = computed(() => {
  if (loadError.value) return 'error';
  return kelurahanList.value.length ? 'ready' : 'loading';
});
const statusText = computed(
  () =>
    ({
      error: 'Model 3D gagal dimuat',
      ready: `${formatNumber(kelurahanList.value.length)} kelurahan dimuat`,
      loading: 'Memuat model 3D…'
    })[status.value]
);
const statusDotClass = computed(
  () => ({ error: 'bg-bontang-danger', ready: 'bg-bontang-ok', loading: 'bg-bontang-muted motion-safe:animate-pulse' })[status.value]
);
</script>

<style scoped>
.hdr-btn {
  padding: 8px;
  border-radius: 12px;
  color: rgb(var(--bontang-muted));
}
.hdr-btn:hover {
  color: rgb(var(--bontang-text));
  background: rgb(var(--bontang-raised));
}
</style>
