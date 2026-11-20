<template>
  <div class="space-y-3 text-body">
    <!-- Peta dasar -->
    <UiCard title="Peta dasar">
      <div role="group" aria-label="Peta dasar" class="grid grid-cols-2 gap-1 p-1 rounded-lg bg-bontang-ink border border-bontang-line">
        <button
          v-for="b in BASEMAP_CHOICES"
          :key="b.id"
          type="button"
          :aria-pressed="themeStore.basemapMode === b.id"
          class="px-2 py-1.5 rounded-md font-medium"
          :class="
            themeStore.basemapMode === b.id
              ? 'bg-bontang-raised text-bontang-text ring-1 ring-inset ring-bontang-accent'
              : 'text-bontang-muted hover:text-bontang-text'
          "
          @click="themeStore.setBasemapMode(b.id)"
        >
          {{ b.label }}
        </button>
      </div>
    </UiCard>

    <!-- Mode tampilan: Hemat / Seimbang / Kualitas -->
    <UiCard title="Mode tampilan" collapsible><DisplaySettings /></UiCard>

    <!-- Lapisan -->
    <UiCard title="Lapisan">
      <ul class="rounded-lg border border-bontang-line divide-y divide-bontang-line">
        <li v-for="row in LAYER_ROWS" :key="row.id" class="flex items-start justify-between gap-3 p-3">
          <div>
            <p :id="`label-${row.id}`" class="font-medium">{{ row.label }}</p>
            <p class="text-small text-bontang-muted">{{ row.note }}</p>
            <p v-if="rowError(row.id)" class="mt-1 text-small text-bontang-danger">Gagal dimuat: {{ rowError(row.id) }}</p>
          </div>
          <button
            type="button"
            role="switch"
            :aria-checked="mapStore[row.flag]"
            :aria-labelledby="`label-${row.id}`"
            class="relative mt-0.5 w-9 h-5 shrink-0 rounded-full border motion-safe:transition-colors"
            :class="mapStore[row.flag] ? 'bg-bontang-accent border-bontang-accent' : 'bg-bontang-ink border-bontang-edge'"
            @click="mapStore[row.flag] = !mapStore[row.flag]"
          >
            <span
              class="absolute top-0.5 left-0.5 w-3.5 h-3.5 rounded-full motion-safe:transition-transform"
              :class="mapStore[row.flag] ? 'translate-x-4 bg-bontang-accent-ink' : 'bg-bontang-muted'"
              aria-hidden="true"
            ></span>
          </button>
        </li>
        <!-- Data belum ada di proyek: tampilkan status, bukan toggle palsu. -->
        <li v-for="item in UPCOMING_LAYERS" :key="item.label" class="flex items-start justify-between gap-3 p-3">
          <div>
            <p class="font-medium text-bontang-muted">{{ item.label }}</p>
            <p class="text-small text-bontang-subtle">{{ item.note }}</p>
          </div>
          <span class="shrink-0 px-2 py-0.5 rounded-full border border-bontang-line text-caption text-bontang-muted">Segera hadir</span>
        </li>
      </ul>
    </UiCard>

    <!-- Layer dari geoportal (WFS/CSW lewat backend) -->
    <UiCard title="Data geoportal" collapsible><GeoportalPanel /></UiCard>

    <!-- Navigasi -->
    <UiCard :title="`Navigasi${kelurahanList.length ? ' · ' + formatNumber(kelurahanList.length) + ' kelurahan' : ''}`" collapsible :start-open="false">
      <button
        type="button"
        :disabled="!tilesetRef"
        class="w-full px-3 py-2 rounded-lg border border-bontang-edge font-medium hover:bg-bontang-raised disabled:opacity-50 disabled:cursor-not-allowed"
        @click="goToKota"
      >
        Tampilkan seluruh kota
      </button>
      <ul v-if="kelurahanList.length" class="max-h-56 overflow-y-auto rounded-lg border border-bontang-line py-1">
        <li v-for="k in kelurahanList" :key="k.slug">
          <button
            type="button"
            class="w-full text-left px-3 py-1.5 border-l-2 hover:bg-bontang-raised"
            :class="activeSlug === k.slug ? 'border-bontang-accent bg-bontang-raised' : 'border-transparent'"
            :aria-current="activeSlug === k.slug ? 'location' : undefined"
            @click="goToKelurahan(k.slug)"
          >
            {{ k.name }}
          </button>
        </li>
      </ul>
      <p v-else-if="!loadError" class="text-small text-bontang-muted">Daftar kelurahan muncul setelah model 3D dimuat.</p>
    </UiCard>

    <!-- Simulasi: daftar dari registry src/simulations/ -->
    <UiCard title="Simulasi" collapsible><SimulationPanel /></UiCard>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useMapStore } from '@/stores/mapStore';
import { useThemeStore } from '@/stores/themeStore';
import { BASEMAPS } from '@/config/basemaps';
import { BASEMAP_AUTO } from '@/utils/theme';
import { use3DTiles } from '@/composables/use3DTiles';
import { useVectorLayers } from '@/composables/useVectorLayers';
import { formatNumber } from '@/utils/format';
import SimulationPanel from '@/components/simulation/SimulationPanel.vue';
import GeoportalPanel from '@/components/panels/GeoportalPanel.vue';
import UiCard from '@/components/ui/UiCard.vue';
import DisplaySettings from '@/components/panels/DisplaySettings.vue';

// 'Otomatis' mengikuti tema; pilihan manual tersimpan dan tidak tertimpa saat tema berganti.
const BASEMAP_CHOICES = [{ id: BASEMAP_AUTO, label: 'Otomatis' }, ...BASEMAPS.map(({ id, label }) => ({ id, label }))];

// Toggle layer; `flag` = nama state di mapStore.
const LAYER_ROWS = [
  { id: 'bangunan', flag: 'is3DTilesActive', label: 'Bangunan 3D', note: 'LOD2, 15 kelurahan. Dari jauh tampil sebagai kotak kelurahan.' },
  { id: 'kelurahan', flag: 'isKelurahanActive', label: 'Batas kelurahan', note: 'Garis tebal.' },
  { id: 'rt', flag: 'isRtActive', label: 'Batas RT', note: 'Termasuk RT di pulau. Dimuat saat dinyalakan.' },
  { id: 'sungai', flag: 'isSungaiActive', label: 'Sungai dan drainase', note: 'Sungai biru; drainase hijau toska.' }
];

const UPCOMING_LAYERS = [
  { label: 'Terrain DTM', note: 'Model elevasi 1 m untuk medan 3D.' },
  { label: 'Orthophoto', note: 'Foto udara resolusi 5 cm.' }
];

const themeStore = useThemeStore();
const mapStore = useMapStore();
const { tilesetRef, kelurahanList, loadError, zoomToKota, flyToKelurahan } = use3DTiles();
const { layerErrors } = useVectorLayers();

const rowError = (id) => (id === 'bangunan' ? loadError.value : layerErrors.value[id]);

// Penanda tujuan navigasi terakhir (bukan lokasi kamera sebenarnya).
const activeSlug = ref('bontang_kuala');

const goToKota = () => {
  activeSlug.value = null;
  zoomToKota();
};
const goToKelurahan = (slug) => {
  activeSlug.value = slug;
  flyToKelurahan(slug);
};
</script>
