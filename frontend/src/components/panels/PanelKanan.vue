<template>
  <div class="space-y-3">
    <!-- Dua tab: info peta/objek (seperti sebelumnya) dan Kondisi Terkini. Memilih bangunan selalu membuka tab info. -->
    <div role="tablist" aria-label="Isi panel kanan" class="grid grid-cols-2 gap-1 p-1 rounded-xl border border-bontang-line bg-bontang-panel" @keydown="geser">
      <button
        v-for="t in TAB"
        :id="`tab-${t.id}`"
        :key="t.id"
        ref="tabEls"
        type="button"
        role="tab"
        :aria-selected="tab === t.id"
        :aria-controls="`isi-${t.id}`"
        :tabindex="tab === t.id ? 0 : -1"
        class="px-2 py-1.5 rounded-lg text-small font-semibold"
        :class="tab === t.id ? 'bg-bontang-accent text-bontang-accent-ink' : 'text-bontang-muted hover:text-bontang-text'"
        @click="tab = t.id"
      >
        {{ t.label }}
      </button>
    </div>

    <div v-show="tab === 'info'" id="isi-info" role="tabpanel" aria-labelledby="tab-info" class="space-y-3">
      <MapLegend />
      <div class="rounded-2xl border border-bontang-line bg-bontang-panel">
        <ObjectInfoPanel />
      </div>
    </div>
    <div v-if="tab === 'kondisi'" id="isi-kondisi" role="tabpanel" aria-labelledby="tab-kondisi">
      <KondisiTerkini v-if="open" />
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue';
import MapLegend from '@/components/map/MapLegend.vue';
import ObjectInfoPanel from '@/components/panels/ObjectInfoPanel.vue';
import KondisiTerkini from '@/components/terkini/KondisiTerkini.vue';
import { useObjectStore } from '@/stores/objectStore';

defineProps({ open: { type: Boolean, required: true } });
const TAB = [
  { id: 'info', label: 'Peta dan objek' },
  { id: 'kondisi', label: 'Kondisi terkini' }
];
const tab = ref('info');
const tabEls = ref([]);

const objectStore = useObjectStore();
watch(() => objectStore.selectedObject, (obj) => { if (obj) tab.value = 'info'; });

// Panah kiri/kanan, Home, End memindahkan tab (pola WAI-ARIA tabs).
const geser = (e) => {
  const i = TAB.findIndex((t) => t.id === tab.value);
  const k = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: TAB.length - 1 }[e.key];
  if (k === undefined) return;
  e.preventDefault();
  tab.value = TAB[(k + TAB.length) % TAB.length].id;
  nextTick(() => tabEls.value.find((el) => el.id === `tab-${tab.value}`)?.focus());
};
</script>
