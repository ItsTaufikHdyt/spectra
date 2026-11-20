<template>
  <div class="relative w-full max-w-[260px]">
    <label for="cari-kelurahan" class="sr-only">Cari kelurahan</label>
    <UiIcon name="search" class="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-bontang-muted" />
    <input
      id="cari-kelurahan"
      v-model="query"
      type="text"
      role="combobox"
      autocomplete="off"
      placeholder="Cari kelurahan"
      class="w-full pl-8 pr-2 py-1.5 rounded-full bg-bontang-ink border border-bontang-edge text-small placeholder:text-bontang-subtle disabled:opacity-60"
      :disabled="!kelurahanList.length"
      aria-autocomplete="list"
      aria-controls="daftar-kelurahan"
      :aria-expanded="open"
      :aria-activedescendant="open && hasil.length ? `kel-${hasil[aktif]?.slug}` : undefined"
      @focus="open = true"
      @input="(open = true), (aktif = 0)"
      @keydown.down.prevent="geser(1)"
      @keydown.up.prevent="geser(-1)"
      @keydown.enter.prevent="pilih(hasil[aktif])"
      @keydown.esc="tutup"
      @blur="tundaTutup"
    />
    <ul
      v-show="open && query"
      id="daftar-kelurahan"
      role="listbox"
      aria-label="Kelurahan"
      class="absolute z-50 mt-1 w-full max-h-64 overflow-y-auto rounded-xl border border-bontang-line bg-bontang-panel py-1 shadow-lg"
    >
      <li
        v-for="(k, i) in hasil"
        :id="`kel-${k.slug}`"
        :key="k.slug"
        role="option"
        :aria-selected="i === aktif"
        class="px-3 py-1.5 text-body cursor-pointer"
        :class="i === aktif ? 'bg-bontang-raised' : ''"
        @mousedown.prevent="pilih(k)"
      >
        {{ k.name }}
      </li>
      <li v-if="!hasil.length" class="px-3 py-1.5 text-small text-bontang-muted">Tidak ada kelurahan yang cocok.</li>
    </ul>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import UiIcon from '@/components/ui/UiIcon.vue';
import { use3DTiles } from '@/composables/use3DTiles';
import { filterKelurahan } from '@/utils/search';

const { kelurahanList, flyToKelurahan } = use3DTiles();
const query = ref('');
const open = ref(false);
const aktif = ref(0);
const hasil = computed(() => filterKelurahan(kelurahanList.value, query.value));

const geser = (d) => {
  open.value = true;
  if (hasil.value.length) aktif.value = (aktif.value + d + hasil.value.length) % hasil.value.length;
};
const tutup = () => { open.value = false; };
const tundaTutup = () => setTimeout(tutup, 100);
const pilih = (k) => {
  if (!k) return;
  flyToKelurahan(k.slug);
  query.value = '';
  tutup();
};
</script>
