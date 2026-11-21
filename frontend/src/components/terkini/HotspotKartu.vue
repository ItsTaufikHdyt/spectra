<template>
  <KartuTerkini sumber="hotspot" judul="Hotspot" pesan-belum-dikonfigurasi="Hotspot belum dikonfigurasi (FIRMS_MAP_KEY)." v-slot="{ data }">
    <div class="space-y-3 text-body">
      <p class="flex items-baseline gap-2">
        <span class="text-display font-bold tabular-nums">{{ formatNumber(data.jumlah_24jam) }}</span>
        <span>titik dalam 24 jam terakhir</span>
      </p>
      <p class="text-small text-bontang-muted">
        {{ formatNumber(data.jumlah_total) }} titik dalam {{ data.hari }} hari terakhir, area Bontang + 20 km.
      </p>
      <ul v-if="data.per_hari.length" class="text-small tabular-nums" aria-label="Jumlah titik per hari (WITA)">
        <li v-for="h in data.per_hari" :key="h.tanggal_wita" class="flex justify-between py-0.5">
          <span>{{ tanggal(h.tanggal_wita) }}</span><span>{{ h.jumlah }}</span>
        </li>
      </ul>
      <section v-if="terdekat.length" aria-labelledby="hotspot-terdekat">
        <h3 id="hotspot-terdekat" class="text-small font-semibold text-bontang-muted">Terdekat dari pusat Bontang</h3>
        <ul class="mt-1 divide-y divide-bontang-line rounded-lg border border-bontang-line">
          <li v-for="t in terdekat" :key="t.waktu_utc + t.lat + t.lon" class="p-2 text-small">
            <span class="font-medium tabular-nums">{{ formatNumber(t.jarak_km) }} km</span> · {{ t.sensor }}
            <span class="block text-caption text-bontang-muted tabular-nums">
              {{ tanggalJamWita(t.waktu_utc) }} · keyakinan {{ t.confidence }}<template v-if="t.frp_mw != null"> · FRP {{ t.frp_mw }} MW</template>
            </span>
          </li>
        </ul>
      </section>
      <p v-else class="text-small text-bontang-muted">Tidak ada titik panas terdeteksi pada periode ini.</p>
      <p class="text-caption text-bontang-muted">{{ data.catatan }}</p>
    </div>
  </KartuTerkini>
</template>

<script setup>
import { computed } from 'vue';
import KartuTerkini from '@/components/terkini/KartuTerkini.vue';
import { useTerkiniStore } from '@/stores/terkiniStore';
import { formatNumber } from '@/utils/format';
import { tanggalJamWita } from '@/utils/terkini';

const store = useTerkiniStore();
const terdekat = computed(() => [...(store.sumber.hotspot.data?.titik ?? [])].sort((a, b) => a.jarak_km - b.jarak_km).slice(0, 5));
const tanggal = (iso) => new Date(`${iso}T00:00:00Z`).toLocaleDateString('id-ID', { timeZone: 'UTC', day: 'numeric', month: 'short' });
</script>
