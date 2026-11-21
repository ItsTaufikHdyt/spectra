<template>
  <KartuTerkini sumber="cuaca" judul="Cuaca" v-slot="{ data }">
    <div class="space-y-3 text-body">
      <div>
        <label for="cuaca-kelurahan" class="block text-small text-bontang-muted">Kelurahan</label>
        <select
          id="cuaca-kelurahan"
          class="w-full mt-1 px-2 py-1.5 rounded-md bg-bontang-ink border border-bontang-edge text-body"
          :value="store.kelurahanCuaca"
          @change="store.pilihKelurahan($event.target.value)"
        >
          <option v-for="k in daftar" :key="k.slug" :value="k.slug">{{ k.name }}</option>
        </select>
      </div>

      <template v-for="s in [slotCuaca(data.jam)]" :key="s.sekarang?.waktu_utc">
        <div v-if="s.sekarang" class="rounded-xl border border-bontang-line p-3 space-y-1">
          <p class="text-small text-bontang-muted tabular-nums">Perkiraan {{ jamLokal(s.sekarang.waktu_lokal) }} WITA</p>
          <div class="flex items-center gap-3">
            <IkonCuaca :cuaca="s.sekarang.cuaca" :waktu-lokal="s.sekarang.waktu_lokal" ukuran="w-12 h-12" />
            <p class="flex flex-col"><span class="text-display font-bold tabular-nums leading-tight">{{ s.sekarang.suhu_c }}°C</span> <span>{{ s.sekarang.cuaca }}</span></p>
          </div>
          <p class="text-small text-bontang-muted tabular-nums">
            Lembap {{ s.sekarang.kelembapan }}% · Angin {{ s.sekarang.angin_kmj }} km/jam dari {{ mataAngin(s.sekarang.angin_derajat) }} · Hujan {{ s.sekarang.hujan_mm }} mm
          </p>
        </div>
        <table v-if="s.berikut.length" class="w-full text-small tabular-nums">
          <caption class="sr-only">Perkiraan beberapa jam ke depan</caption>
          <thead class="text-bontang-muted">
            <tr>
              <th scope="col" class="text-left font-medium py-1 whitespace-nowrap">Jam WITA</th>
              <th scope="col" class="text-left font-medium">Cuaca</th>
              <th scope="col" class="text-right font-medium">Suhu</th>
              <th scope="col" class="text-right font-medium whitespace-nowrap">Angin km/j</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-bontang-line">
            <tr v-for="j in s.berikut" :key="j.waktu_utc">
              <td class="py-1 whitespace-nowrap">{{ jamLokal(j.waktu_lokal) }}</td>
              <td><span class="flex items-center gap-1.5"><IkonCuaca :cuaca="j.cuaca" :waktu-lokal="j.waktu_lokal" ukuran="w-5 h-5" />{{ j.cuaca }}</span></td>
              <td class="text-right">{{ j.suhu_c }}°C</td>
              <td class="text-right whitespace-nowrap">{{ j.angin_kmj }} {{ mataAngin(j.angin_derajat) }}</td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>
  </KartuTerkini>
</template>

<script setup>
import { computed } from 'vue';
import IkonCuaca from '@/components/terkini/IkonCuaca.vue';
import KartuTerkini from '@/components/terkini/KartuTerkini.vue';
import { use3DTiles } from '@/composables/use3DTiles';
import { useTerkiniStore } from '@/stores/terkiniStore';
import { jamLokal, mataAngin, slotCuaca } from '@/utils/terkini';

const store = useTerkiniStore();
const { kelurahanList } = use3DTiles();
// Daftar dari model 3D (nama sama dengan di panel lain); sebelum termuat, pilihan bawaan tetap ada.
const daftar = computed(() => (kelurahanList.value.length ? kelurahanList.value : [{ slug: store.kelurahanCuaca, name: 'Bontang Kuala' }]));
</script>
