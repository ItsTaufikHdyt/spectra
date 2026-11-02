<template>
  <li class="p-3 space-y-2">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <p :id="`label-${layer.id}`" class="font-medium break-words">
          <span
            class="inline-block w-2.5 h-2.5 mr-1.5 rounded-sm align-middle"
            :style="layer.mode === 'wms' ? { border: '1.5px solid #9DB2BE' } : { backgroundColor: layer.warna }"
            aria-hidden="true"
          ></span>{{ layer.judul }}
        </p>
        <p class="text-small text-bontang-muted">
          {{ formatNumber(layer.jumlah_fitur) ?? '–' }} fitur, {{ layer.mode === 'wms' ? 'gambar WMS' : 'GeoJSON' }}
        </p>
      </div>
      <button
        type="button"
        role="switch"
        :aria-checked="layer.aktif"
        :aria-labelledby="`label-${layer.id}`"
        :disabled="!!busy"
        class="relative mt-0.5 w-9 h-5 shrink-0 rounded-full border motion-safe:transition-colors disabled:opacity-50"
        :class="layer.aktif ? 'bg-bontang-accent border-bontang-accent' : 'bg-bontang-ink border-bontang-edge'"
        @click="store.update(layer.id, { aktif: !layer.aktif })"
      >
        <span
          class="absolute top-0.5 left-0.5 w-3.5 h-3.5 rounded-full motion-safe:transition-transform"
          :class="layer.aktif ? 'translate-x-4 bg-bontang-accent-ink' : 'bg-bontang-muted'"
          aria-hidden="true"
        ></span>
      </button>
    </div>

    <!-- Aksi -->
    <div class="flex flex-wrap gap-1.5">
      <button type="button" :class="BTN" :disabled="!layer.bbox" @click="zoomToLayer(layer)">Zoom</button>
      <button type="button" :class="BTN" :disabled="!!busy" @click="store.refresh(layer.id)">Refresh</button>
      <button type="button" :class="BTN" :aria-expanded="open" :aria-controls="`atur-${layer.id}`" @click="open = !open">Atur</button>
      <button type="button" :class="[BTN, 'text-bontang-danger']" :disabled="!!busy" @click="dialog?.showModal()">Hapus</button>
    </div>

    <p v-if="busy" role="status" class="text-small text-bontang-muted">{{ BUSY_TEXT[busy] }}</p>
    <p v-if="store.errors[layer.id]" role="alert" class="text-small text-bontang-danger break-words">{{ store.errors[layer.id] }}</p>
    <p v-else-if="layer.status === 'error'" role="alert" class="text-small text-bontang-danger break-words">
      Refresh terakhir gagal: {{ layer.pesan_error }} Data sebelumnya tetap dipakai.
    </p>

    <!-- Pengaturan -->
    <div v-show="open" :id="`atur-${layer.id}`" class="grid grid-cols-[auto_1fr] items-center gap-x-3 gap-y-2 pt-1 text-small">
      <template v-if="layer.mode === 'geojson'">
        <label :for="`warna-${layer.id}`" class="text-bontang-muted">Warna</label>
        <input
          :id="`warna-${layer.id}`"
          type="color"
          :value="layer.warna"
          class="h-7 w-12 rounded border border-bontang-edge bg-bontang-ink"
          @input="store.setLocal(layer.id, { warna: $event.target.value })"
          @change="store.update(layer.id, { warna: $event.target.value })"
        />
      </template>
      <label :for="`opasitas-${layer.id}`" class="text-bontang-muted">Opasitas</label>
      <div class="flex items-center gap-2">
        <input
          :id="`opasitas-${layer.id}`"
          type="range"
          min="0"
          max="1"
          step="0.05"
          :value="layer.opasitas"
          class="flex-1 accent-bontang-accent"
          @input="store.setLocal(layer.id, { opasitas: Number($event.target.value) })"
          @change="store.update(layer.id, { opasitas: Number($event.target.value) })"
        />
        <span class="w-9 text-right tabular-nums">{{ formatNumber(layer.opasitas * 100, { maxDigits: 0 }) }}%</span>
      </div>
      <template v-if="layer.mode === 'geojson' && layer.atribut_tersedia?.length">
        <label :for="`nama-${layer.id}`" class="text-bontang-muted">Kolom nama</label>
        <select
          :id="`nama-${layer.id}`"
          :value="layer.field_nama ?? ''"
          class="min-w-0 px-1.5 py-1 rounded-md bg-bontang-ink border border-bontang-edge"
          @change="store.update(layer.id, { field_nama: $event.target.value || null })"
        >
          <option value="">Tanpa nama</option>
          <option v-for="a in layer.atribut_tersedia" :key="a" :value="a">{{ a }}</option>
        </select>
      </template>
      <p class="col-span-2 text-caption text-bontang-subtle break-all">
        {{ layer.typename }}, diambil {{ formatTime(layer.diambil) }}
      </p>
    </div>

    <!-- Konfirmasi hapus -->
    <dialog
      ref="dialog"
      :aria-labelledby="`hapus-judul-${layer.id}`"
      class="fixed inset-0 m-auto h-fit w-[min(92vw,360px)] rounded-lg border border-bontang-line bg-bontang-panel p-4 text-body text-bontang-text backdrop:bg-black/60"
    >
      <h3 :id="`hapus-judul-${layer.id}`" class="text-title font-semibold">Hapus {{ layer.judul }}?</h3>
      <p class="mt-2 text-bontang-muted">Layer ini akan dihapus dari spectra. Data di geoportal tidak berubah.</p>
      <form method="dialog" class="mt-4 flex justify-end gap-2">
        <button value="batal" class="px-3 py-1.5 rounded-md border border-bontang-edge font-medium hover:bg-bontang-raised" autofocus>Batal</button>
        <button
          value="hapus"
          class="px-3 py-1.5 rounded-md bg-bontang-danger text-bontang-ink font-semibold hover:brightness-110"
          @click="store.remove(layer.id)"
        >
          Hapus layer
        </button>
      </form>
    </dialog>
  </li>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRemoteLayerStore } from '@/stores/remoteLayerStore';
import { useRemoteLayers } from '@/composables/useRemoteLayers';
import { formatNumber } from '@/utils/format';

const props = defineProps({ layer: { type: Object, required: true } });

const BTN =
  'px-2 py-1 rounded-md border border-bontang-edge text-caption font-medium hover:bg-bontang-raised disabled:opacity-50 disabled:cursor-not-allowed';
const BUSY_TEXT = { refresh: 'Menarik ulang data dari geoportal…', menghapus: 'Menghapus…' };

const store = useRemoteLayerStore();
const { zoomToLayer } = useRemoteLayers();
const open = ref(false);
const dialog = ref(null);
const busy = computed(() => store.busy[props.layer.id]);

const timeFmt = new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' });
const formatTime = (iso) => (iso ? timeFmt.format(new Date(iso)) : '–');
</script>
