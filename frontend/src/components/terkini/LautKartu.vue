<template>
  <KartuTerkini sumber="laut" judul="Laut" v-slot="{ data }">
    <div class="space-y-3 text-body">
      <div role="group" aria-label="Titik laut" class="grid grid-cols-3 gap-1 p-1 rounded-lg bg-bontang-ink border border-bontang-line">
        <button
          v-for="t in data.titik"
          :key="t.id"
          type="button"
          class="px-1 py-1.5 rounded-md text-small font-medium"
          :class="store.titikLaut === t.id ? 'bg-bontang-raised text-bontang-text ring-1 ring-inset ring-bontang-accent' : 'text-bontang-muted hover:text-bontang-text'"
          :aria-pressed="store.titikLaut === t.id"
          @click="store.titikLaut = t.id"
        >
          {{ t.id.charAt(0).toUpperCase() + t.id.slice(1) }}
        </button>
      </div>

      <template v-for="t in [dipilih(data)]" :key="t.id">
        <p class="text-small text-bontang-muted">{{ t.nama }}. Titik model ±13 km lepas pantai (sel ±9 km), bukan di tepi pantai.</p>
        <p v-if="!t.tersedia" class="text-small">Data gelombang tidak tersedia untuk titik ini.</p>
        <template v-else>
          <div class="rounded-xl border border-bontang-line p-3 space-y-1">
            <p class="text-small text-bontang-muted tabular-nums">Perkiraan {{ jamLokal(t.jam[0].waktu_lokal) }} WITA</p>
            <p class="flex items-baseline gap-2"><span class="text-display font-bold tabular-nums">{{ n(t.jam[0].tinggi_m) }} m</span> <span>tinggi gelombang</span></p>
            <p class="text-small text-bontang-muted tabular-nums">
              Arah dari {{ mataAngin(t.jam[0].arah_derajat) }} · Periode {{ n(t.jam[0].periode_s) }} dtk<template v-if="t.jam[0].suhu_laut_c != null"> · Suhu laut {{ n(t.jam[0].suhu_laut_c) }}°C</template>
            </p>
          </div>
          <table class="w-full text-small tabular-nums">
            <caption class="sr-only">Perkiraan gelombang beberapa jam ke depan</caption>
            <thead class="text-bontang-muted">
              <tr><th scope="col" class="text-left font-medium py-1">Jam (WITA)</th><th scope="col" class="text-right font-medium">Tinggi</th><th scope="col" class="text-right font-medium">Periode</th></tr>
            </thead>
            <tbody class="divide-y divide-bontang-line">
              <tr v-for="j in t.jam.filter((_, i) => i > 0 && i % 3 === 0).slice(0, 4)" :key="j.waktu_lokal">
                <td class="py-1">{{ jamLokal(j.waktu_lokal) }}</td><td class="text-right">{{ n(j.tinggi_m) }} m</td><td class="text-right">{{ n(j.periode_s) }} dtk</td>
              </tr>
            </tbody>
          </table>
        </template>
      </template>
    </div>
  </KartuTerkini>
</template>

<script setup>
import KartuTerkini from '@/components/terkini/KartuTerkini.vue';
import { useTerkiniStore } from '@/stores/terkiniStore';
import { jamLokal, mataAngin } from '@/utils/terkini';

const store = useTerkiniStore();
const dipilih = (data) => data.titik.find((t) => t.id === store.titikLaut) ?? data.titik[0];
const n = (v) => (v == null ? '–' : v.toLocaleString('id-ID', { maximumFractionDigits: 1 }));
</script>
