<template>
  <header class="h-[52px] flex items-center gap-3 px-3 border-b border-bontang-line bg-bontang-panel">
    <button
      type="button"
      class="p-2 rounded-md text-bontang-muted hover:text-bontang-text hover:bg-bontang-raised"
      :aria-expanded="leftOpen"
      aria-controls="panel-kiri"
      :aria-label="leftOpen ? 'Sembunyikan panel layer' : 'Tampilkan panel layer'"
      @click="$emit('toggle-left')"
    >
      <svg viewBox="0 0 20 20" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <rect x="2.5" y="3.5" width="15" height="13" rx="2" />
        <path d="M7.5 3.5v13" />
      </svg>
    </button>

    <div class="min-w-0 flex items-baseline gap-3">
      <h1 class="text-display font-bold tracking-tight whitespace-nowrap">Digital Twin Bontang</h1>
      <p class="hidden md:block text-small text-bontang-muted truncate">Kota Bontang, Kalimantan Timur</p>
    </div>

    <div class="ml-auto flex items-center gap-2">
      <p class="flex items-center gap-2 px-2.5 py-1 rounded-full bg-bontang-ink border border-bontang-line text-small" role="status">
        <span class="w-2 h-2 rounded-full" :class="statusDotClass" aria-hidden="true"></span>
        <span>{{ statusText }}</span>
      </p>
      <p class="hidden lg:block text-caption text-bontang-subtle">Terrain dan atribut bangunan belum tersedia</p>
      <ThemeToggle />
      <button
        type="button"
        class="p-2 rounded-md text-bontang-muted hover:text-bontang-text hover:bg-bontang-raised"
        :aria-expanded="rightOpen"
        aria-controls="panel-kanan"
        :aria-label="rightOpen ? 'Sembunyikan panel informasi' : 'Tampilkan panel informasi'"
        @click="$emit('toggle-right')"
      >
        <svg viewBox="0 0 20 20" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
          <rect x="2.5" y="3.5" width="15" height="13" rx="2" />
          <path d="M12.5 3.5v13" />
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { use3DTiles } from '@/composables/use3DTiles';
import { formatNumber } from '@/utils/format';
import ThemeToggle from '@/components/layout/ThemeToggle.vue';

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
  () =>
    ({
      error: 'bg-bontang-danger',
      ready: 'bg-bontang-ok',
      loading: 'bg-bontang-muted motion-safe:animate-pulse'
    })[status.value]
);
</script>
