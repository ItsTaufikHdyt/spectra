<template>
  <UiCard :title="judul" collapsible>
    <template #ikon><IkonKartu :nama="sumber" /></template>
    <p v-if="st.status === 'idle' || st.status === 'memuat'" role="status" class="flex items-center gap-2 text-small text-bontang-muted">
      <span class="w-3.5 h-3.5 rounded-full border-2 border-bontang-line border-t-bontang-accent motion-safe:animate-spin" aria-hidden="true"></span>
      Memuat {{ judul.toLowerCase() }}…
    </p>

    <p v-else-if="st.data?.dikonfigurasi === false" class="text-small text-bontang-muted">{{ pesanBelumDikonfigurasi }}</p>

    <div v-else-if="!st.data || st.data.tersedia === false" role="alert" class="rounded-lg border border-bontang-edge p-3 space-y-2">
      <p class="font-medium">Data tidak tersedia</p>
      <p class="text-small text-bontang-muted break-words">{{ st.galat ?? st.data?.galat ?? 'Sumber belum dapat dijangkau.' }}</p>
      <button type="button" class="px-3 py-1.5 rounded-md border border-bontang-edge text-small font-medium hover:bg-bontang-raised" @click="store.muat(sumber)">
        Coba lagi
      </button>
    </div>

    <slot v-else :data="st.data" />

    <p v-if="st.data?.dikonfigurasi !== false" class="mt-3 pt-2 border-t border-bontang-line text-caption text-bontang-muted flex flex-wrap items-center gap-x-2 gap-y-1">
      <span>
        Sumber:
        <a :href="st.data?.url_sumber ?? STATIS[sumber].url" target="_blank" rel="noopener noreferrer" class="underline text-bontang-accent">{{ st.data?.sumber ?? STATIS[sumber].nama }}</a>
      </span>
      <span v-if="st.data?.diambil_pada" class="tabular-nums">· diperbarui {{ jamWita(st.data.diambil_pada) }}</span>
      <span v-if="st.data?.stale" class="px-1.5 rounded border border-bontang-warn text-bontang-warn font-medium">data lama</span>
    </p>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue';
import UiCard from '@/components/ui/UiCard.vue';
import IkonKartu from '@/components/terkini/IkonKartu.vue';
import { useTerkiniStore } from '@/stores/terkiniStore';
import { jamWita } from '@/utils/terkini';

const props = defineProps({
  sumber: { type: String, required: true }, // gempa | cuaca | hotspot | laut
  judul: { type: String, required: true },
  pesanBelumDikonfigurasi: { type: String, default: 'Sumber ini belum dikonfigurasi.' }
});

const STATIS = {
  gempa: { nama: 'BMKG', url: 'https://data.bmkg.go.id/gempabumi/' },
  cuaca: { nama: 'BMKG', url: 'https://data.bmkg.go.id/prakiraan-cuaca/' },
  hotspot: { nama: 'NASA FIRMS', url: 'https://firms.modaps.eosdis.nasa.gov/' },
  laut: { nama: 'Open-Meteo (CC BY 4.0)', url: 'https://open-meteo.com/en/docs/marine-weather-api' }
};
const store = useTerkiniStore();
const st = computed(() => store.sumber[props.sumber]);
</script>
