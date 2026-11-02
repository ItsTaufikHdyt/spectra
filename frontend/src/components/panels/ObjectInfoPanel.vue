<template>
  <!-- Belum ada pilihan: arahkan pengguna, bukan sekadar kosong. -->
  <div v-if="!selected" class="h-full flex flex-col items-center justify-center gap-3 p-8 text-center">
    <svg viewBox="0 0 48 48" class="w-12 h-12 text-bontang-edge" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <path d="M10 38V18l14-8 14 8v20" />
      <path d="M18 38V26h12v12" />
      <circle cx="24" cy="19" r="2.5" />
    </svg>
    <h2 class="text-title font-semibold">Belum ada objek dipilih</h2>
    <p class="text-body text-bontang-muted max-w-[32ch]">
      Klik bangunan di peta untuk melihat lokasi dan atributnya. Dari kejauhan, klik kotak
      kelurahan untuk mendekat.
    </p>
  </div>

  <article v-else aria-labelledby="judul-objek" class="p-4 space-y-5 text-body">
    <header class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="text-small text-bontang-muted">{{ selected.identity.category }}</p>
        <h2 id="judul-objek" class="text-display font-semibold leading-tight break-words">{{ displayName }}</h2>
        <p v-if="selected.identity.kelurahan" class="text-body text-bontang-muted">Kelurahan {{ selected.identity.kelurahan }}</p>
      </div>
      <button
        type="button"
        class="shrink-0 p-1.5 rounded-md text-bontang-muted hover:text-bontang-text hover:bg-bontang-raised"
        aria-label="Hapus pilihan objek"
        @click="objectStore.clearSelection()"
      >
        <svg viewBox="0 0 20 20" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true">
          <path d="M5 5l10 10M15 5L5 15" />
        </svg>
      </button>
    </header>

    <!-- Atribut bangunan -->
    <section aria-labelledby="judul-atribut" class="space-y-2">
      <h3 id="judul-atribut" class="text-small font-semibold text-bontang-muted">{{ selected.source ? 'Atribut fitur' : 'Atribut bangunan' }}</h3>

      <dl v-if="objectStore.attributeStatus === 'ready'" class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5">
        <template v-for="row in attributeRows" :key="row.key">
          <dt class="text-bontang-muted">{{ row.key }}</dt>
          <dd class="text-right tabular-nums break-words">{{ row.value }}</dd>
        </template>
      </dl>

      <div v-else-if="objectStore.attributeStatus === 'loading'" class="space-y-2" aria-busy="true">
        <p class="sr-only">Memuat atribut bangunan</p>
        <div class="h-3 w-3/4 rounded bg-bontang-raised motion-safe:animate-pulse"></div>
        <div class="h-3 w-1/2 rounded bg-bontang-raised motion-safe:animate-pulse"></div>
      </div>

      <div v-else-if="objectStore.attributeStatus === 'error'" role="alert" class="rounded-lg border border-bontang-danger/50 p-3 space-y-2">
        <p class="font-medium text-bontang-danger">Atribut gagal dimuat</p>
        <p class="text-small text-bontang-muted break-words">{{ objectStore.attributeError }}</p>
        <button type="button" class="px-3 py-1.5 rounded-md border border-bontang-edge text-small font-medium hover:bg-bontang-raised" @click="objectStore.retryAttributes()">
          Coba lagi
        </button>
      </div>

      <div v-else class="rounded-lg border border-dashed border-bontang-edge p-3 space-y-1">
        <p class="font-medium">Data atribut belum tersedia</p>
        <p class="text-small text-bontang-muted">
          Model 3D belum membawa nama, tinggi, dan fungsi bangunan. Informasi ini tampil di sini
          setelah data atribut tersambung.
        </p>
      </div>
    </section>

    <!-- Lokasi titik klik -->
    <section v-if="selected.location" aria-labelledby="judul-lokasi" class="space-y-2">
      <h3 id="judul-lokasi" class="text-small font-semibold text-bontang-muted">Lokasi titik klik</h3>
      <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5">
        <dt class="text-bontang-muted">Bujur</dt>
        <dd class="text-right tabular-nums">{{ formatDegrees(selected.location.longitude) }}</dd>
        <dt class="text-bontang-muted">Lintang</dt>
        <dd class="text-right tabular-nums">{{ formatDegrees(selected.location.latitude) }}</dd>
        <dt class="text-bontang-muted">Elevasi</dt>
        <dd class="text-right tabular-nums">{{ formatWithUnit(selected.location.elevation, 'm') }}</dd>
      </dl>
    </section>

    <!-- Sumber data: layer geoportal -->
    <section v-if="selected.source" aria-labelledby="judul-sumber" class="space-y-2">
      <h3 id="judul-sumber" class="text-small font-semibold text-bontang-muted">Sumber data</h3>
      <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5">
        <dt class="text-bontang-muted">Layer</dt>
        <dd class="text-right break-words">{{ selected.source.judul }}</dd>
        <dt class="text-bontang-muted">FeatureType</dt>
        <dd class="text-right break-all">{{ selected.source.typename }}</dd>
        <dt class="text-bontang-muted">ID fitur</dt>
        <dd class="text-right tabular-nums">{{ selected.source.fid }}</dd>
      </dl>
    </section>

    <!-- Sumber data: bangunan 3D -->
    <section v-else-if="selected.tile" aria-labelledby="judul-sumber" class="space-y-2">
      <h3 id="judul-sumber" class="text-small font-semibold text-bontang-muted">Sumber data</h3>
      <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5">
        <dt class="text-bontang-muted">Tingkat detail</dt>
        <dd class="text-right">LOD 2</dd>
        <dt class="text-bontang-muted">Tile</dt>
        <dd class="text-right break-all">{{ selected.tile.path || '–' }}</dd>
        <template v-if="selected.tile.featureId !== undefined">
          <dt class="text-bontang-muted">ID fitur</dt>
          <dd class="text-right tabular-nums">{{ formatNumber(selected.tile.featureId) }}</dd>
        </template>
      </dl>
    </section>

    <p v-if="selected.location" class="text-small text-bontang-muted border-t border-bontang-line pt-3">
      Elevasi adalah tinggi titik yang diklik, bukan elevasi lantai dasar (FFL) hasil survei.
    </p>
  </article>
</template>

<script setup>
import { computed } from 'vue';
import { useObjectStore } from '@/stores/objectStore';
import { ATTRIBUTE_KEYS } from '@/services/buildingAttributes';
import { pickFirst } from '@/utils/tileMeta';
import { formatDegrees, formatNumber, formatWithUnit } from '@/utils/format';

const objectStore = useObjectStore();
const selected = computed(() => objectStore.selectedObject);

const displayName = computed(() => {
  const name = objectStore.attributes ? pickFirst(objectStore.attributes, ATTRIBUTE_KEYS.name) : undefined;
  return name ?? selected.value?.identity.name;
});

const attributeRows = computed(() =>
  Object.entries(objectStore.attributes ?? {}).map(([key, value]) => ({
    key,
    value: typeof value === 'number' ? formatNumber(value, { maxDigits: 3 }) : String(value)
  }))
);
</script>
