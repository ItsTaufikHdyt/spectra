<template>
  <div class="space-y-3">
    <!-- 1. Periksa link WFS / CSW -->
    <form class="space-y-1.5" @submit.prevent="periksa">
      <label for="url-geoportal" class="block text-small text-bontang-muted">Link WFS atau CSW</label>
      <div class="flex gap-1.5">
        <input
          id="url-geoportal"
          v-model.trim="url"
          type="url"
          inputmode="url"
          required
          placeholder="https://geoportal.bontangkota.go.id/geoserver/ows"
          class="min-w-0 flex-1 px-2 py-1.5 rounded-md bg-bontang-ink border border-bontang-edge text-small placeholder:text-bontang-subtle focus:outline-none focus:ring-2 focus:ring-bontang-accent"
        />
        <button
          type="submit"
          :disabled="store.inspectStatus === 'loading' || !url"
          class="shrink-0 px-3 py-1.5 rounded-md bg-bontang-accent text-bontang-accent-ink text-small font-semibold hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Periksa
        </button>
      </div>
    </form>

    <p v-if="store.inspectStatus === 'loading'" role="status" class="flex items-center gap-2 text-small text-bontang-muted">
      <span class="w-3.5 h-3.5 rounded-full border-2 border-bontang-line border-t-bontang-accent motion-safe:animate-spin" aria-hidden="true"></span>
      Memeriksa layanan dan menghitung fitur…
    </p>
    <p v-else-if="store.inspectStatus === 'error'" role="alert" class="rounded-md border border-bontang-danger/50 p-2 text-small text-bontang-danger break-words">
      {{ store.inspectError }}
    </p>

    <!-- 2. Hasil inspect -->
    <div v-if="result" class="space-y-1.5">
      <div class="flex items-baseline justify-between gap-2">
        <p class="text-small text-bontang-muted">
          {{ result.tipe === 'csw' ? 'Katalog CSW' : 'Layanan WFS' }}: {{ formatNumber(result.layers.length) }}
          {{ result.tipe === 'csw' ? 'dataset' : 'layer' }}
        </p>
        <button type="button" class="text-caption text-bontang-muted underline hover:text-bontang-text" @click="tutupHasil">Tutup</button>
      </div>
      <label for="cari-layer" class="sr-only">Cari layer</label>
      <input
        id="cari-layer"
        v-model="query"
        type="search"
        placeholder="Cari judul atau nama layer"
        class="w-full px-2 py-1.5 rounded-md bg-bontang-ink border border-bontang-edge text-small placeholder:text-bontang-subtle focus:outline-none focus:ring-2 focus:ring-bontang-accent"
      />
      <div class="max-h-72 overflow-y-auto rounded-lg border border-bontang-line">
        <table class="w-full text-small">
          <caption class="sr-only">Layer yang tersedia di layanan</caption>
          <thead class="sticky top-0 bg-bontang-raised text-bontang-muted">
            <tr>
              <th scope="col" class="text-left font-medium px-2 py-1.5">Layer</th>
              <th scope="col" class="text-right font-medium px-2 py-1.5">Fitur</th>
              <th scope="col" class="px-2 py-1.5"><span class="sr-only">Aksi</span></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-bontang-line">
            <tr v-for="row in filtered" :key="row.id_record ?? row.typename" class="align-top">
              <td class="px-2 py-1.5">
                <p class="font-medium break-words">{{ row.judul }}</p>
                <p v-if="row.typename" class="text-caption text-bontang-subtle break-all">{{ row.typename }}</p>
                <span v-if="row.besar" class="inline-block mt-1 px-1.5 rounded border border-bontang-accent text-caption text-bontang-accent">Besar — WMS</span>
                <p v-if="row.catatan" class="text-caption text-bontang-muted">{{ row.catatan }}</p>
                <p v-if="store.errors[row.typename]" role="alert" class="mt-1 text-caption text-bontang-danger break-words">{{ store.errors[row.typename] }}</p>
              </td>
              <td class="px-2 py-1.5 text-right tabular-nums whitespace-nowrap">{{ row.hits == null ? '–' : formatNumber(row.hits) }}</td>
              <td class="px-2 py-1.5 text-right">
                <span v-if="isAdded(row)" class="text-caption text-bontang-ok whitespace-nowrap">Ditambahkan</span>
                <span v-else-if="!row.typename" class="text-caption text-bontang-muted whitespace-nowrap">Tanpa WFS</span>
                <span v-else-if="store.busy[row.typename]" role="status" class="text-caption text-bontang-muted whitespace-nowrap">Mengambil…</span>
                <button
                  v-else-if="!row.besar || row.wms"
                  type="button"
                  class="px-2 py-1 rounded-md border border-bontang-edge text-caption font-medium hover:bg-bontang-raised whitespace-nowrap"
                  :aria-label="`Tambahkan ${row.judul}${row.besar ? ' sebagai WMS' : ''}`"
                  @click="store.add(row, row.besar ? 'wms' : 'geojson')"
                >
                  {{ row.besar ? 'Tambahkan WMS' : 'Tambahkan' }}
                </button>
                <span v-else class="text-caption text-bontang-muted">Terlalu besar</span>
              </td>
            </tr>
            <tr v-if="!filtered.length">
              <td colspan="3" class="px-2 py-3 text-center text-bontang-muted">Tidak ada layer yang cocok.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-caption text-bontang-subtle">
        Layer di atas {{ formatNumber(store.batasFitur) }} fitur tidak diunduh; tampil sebagai gambar WMS dari geoportal.
      </p>
    </div>

    <!-- 3. Layer yang sudah ditambahkan -->
    <div class="space-y-1.5">
      <p v-if="store.listStatus === 'error'" role="alert" class="rounded-md border border-bontang-danger/50 p-2 text-small text-bontang-danger break-words">
        Daftar layer tidak dapat dimuat: {{ store.listError }}
      </p>
      <ul v-if="store.layers.length" class="rounded-lg border border-bontang-line divide-y divide-bontang-line" aria-label="Layer geoportal yang ditambahkan">
        <RemoteLayerItem v-for="layer in store.layers" :key="layer.id" :layer="layer" />
      </ul>
      <p v-else-if="store.listStatus === 'ready'" class="text-small text-bontang-muted">
        Belum ada layer geoportal. Tempel link WFS atau CSW di atas, lalu pilih layer yang ingin ditampilkan.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRemoteLayerStore } from '@/stores/remoteLayerStore';
import { formatNumber } from '@/utils/format';
import RemoteLayerItem from '@/components/panels/RemoteLayerItem.vue';

const store = useRemoteLayerStore();
const url = ref('');
const query = ref('');

const result = computed(() => (store.inspectStatus === 'ready' ? store.inspectResult : null));
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase();
  const rows = result.value?.layers ?? [];
  return q ? rows.filter((r) => `${r.judul} ${r.typename ?? ''}`.toLowerCase().includes(q)) : rows;
});

const isAdded = (row) => store.layers.some((l) => l.typename === row.typename && l.wfs_url === row.wfs_url);

const periksa = () => {
  query.value = '';
  store.inspect(url.value);
};
const tutupHasil = () => {
  store.inspectStatus = 'idle';
  store.inspectResult = null;
};
</script>
