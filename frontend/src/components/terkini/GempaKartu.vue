<template>
  <KartuTerkini sumber="gempa" judul="Gempa" v-slot="{ data }">
    <div class="space-y-3 text-body">
      <div class="flex items-start gap-3">
        <p class="gempa-lencana relative shrink-0 w-14 h-14 rounded-xl border flex flex-col items-center justify-center leading-none" :class="data.terbaru.tsunami ? 'border-bontang-danger text-bontang-danger' : 'border-bontang-edge'">
          <span class="text-display font-bold tabular-nums">{{ fmt(data.terbaru.magnitudo) }}</span>
          <span class="text-caption text-bontang-muted">M</span>
        </p>
        <div class="min-w-0 space-y-0.5">
          <p class="font-medium break-words">{{ data.terbaru.wilayah }}</p>
          <p class="text-small text-bontang-muted tabular-nums">{{ tanggalJamWita(data.terbaru.waktu_utc) }}</p>
          <p class="text-small text-bontang-muted tabular-nums">
            Kedalaman {{ fmt(data.terbaru.kedalaman_km, 0) }} km · {{ formatNumber(data.terbaru.jarak_km) }} km dari pusat Bontang
          </p>
        </div>
      </div>
      <p v-if="data.terbaru.tsunami" role="alert" class="rounded-lg border-2 border-bontang-danger p-2 font-semibold text-bontang-danger">
        Berpotensi tsunami: {{ data.terbaru.potensi }}
      </p>
      <p v-else-if="data.terbaru.potensi" class="text-small text-bontang-muted">{{ data.terbaru.potensi }}</p>
      <p v-if="data.terbaru.dirasakan" class="text-small">Dirasakan: {{ data.terbaru.dirasakan }}</p>

      <section v-for="d in DAFTAR" :key="d.kunci" :aria-labelledby="`gempa-${d.kunci}`">
        <h3 :id="`gempa-${d.kunci}`" class="text-small font-semibold text-bontang-muted">{{ d.judul }}</h3>
        <ul class="mt-1 max-h-44 overflow-y-auto divide-y divide-bontang-line rounded-lg border border-bontang-line">
          <li v-for="g in data[d.kunci]" :key="g.waktu_utc + g.lat" class="flex gap-2 p-2 text-small" :class="g.tsunami ? 'border-l-4 border-bontang-danger' : ''">
            <span class="shrink-0 w-9 font-semibold tabular-nums">M{{ fmt(g.magnitudo) }}</span>
            <span class="min-w-0">
              <span class="block break-words">{{ g.wilayah }}</span>
              <span class="block text-caption text-bontang-muted tabular-nums">{{ tanggalJamWita(g.waktu_utc) }} · {{ formatNumber(g.jarak_km) }} km dari Bontang</span>
            </span>
          </li>
        </ul>
      </section>
    </div>
  </KartuTerkini>
</template>

<script setup>
import KartuTerkini from '@/components/terkini/KartuTerkini.vue';
import { formatNumber } from '@/utils/format';
import { tanggalJamWita } from '@/utils/terkini';

const DAFTAR = [
  { kunci: 'dirasakan', judul: 'Gempa dirasakan' },
  { kunci: 'terkini', judul: 'Gempa M5,0+' }
];
const fmt = (n, d = 1) => n.toLocaleString('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d });
</script>

<style scoped>
/* Riak seismik di belakang lencana magnitudo; singkat (±6 dtk) lalu diam agar tidak membebani GPU; dimatikan bila gerak dikurangi. */
.gempa-lencana::before, .gempa-lencana::after { content: ''; position: absolute; inset: 0; border-radius: inherit; border: 1.5px solid currentColor; opacity: 0; pointer-events: none; }
@media (prefers-reduced-motion: no-preference) {
  .gempa-lencana::before { animation: riak 2.4s ease-out 2; }
  .gempa-lencana::after { animation: riak 2.4s ease-out 1.2s 2; }
}
@keyframes riak { 0% { transform: scale(1); opacity: 0.45; } 100% { transform: scale(1.55); opacity: 0; } }
</style>
