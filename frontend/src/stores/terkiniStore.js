import { defineStore } from 'pinia';
import { ref } from 'vue';
import { ambilTerkini } from '@/services/terkini';

// Sumber -> path API. Cuaca membawa kelurahan terpilih.
export const SUMBER_TERKINI = ['gempa', 'cuaca', 'hotspot', 'laut'];
export const TTL_DETIK = { gempa: 120, cuaca: 3600, hotspot: 1800, laut: 3600 }; // sama dengan backend/app/terkini.py

const awal = () => ({ status: 'idle', data: null, galat: null }); // status: idle | memuat | siap | galat

export const useTerkiniStore = defineStore('terkini', () => {
  const sumber = ref({ gempa: awal(), cuaca: awal(), hotspot: awal(), laut: awal() });
  const kelurahanCuaca = ref('bontang_kuala');
  const titikLaut = ref('tengah');
  const sedangMuat = new Set();

  const pathDari = (s) => (s === 'cuaca' ? `cuaca?kelurahan=${encodeURIComponent(kelurahanCuaca.value)}` : s);

  /** Muat satu sumber. Gagal + ada data lama -> data lama ditandai stale (tidak ada angka baru yang dikarang). */
  async function muat(s) {
    const kunci = pathDari(s);
    if (sedangMuat.has(kunci)) return;
    sedangMuat.add(kunci);
    const st = sumber.value[s];
    if (!st.data) st.status = 'memuat';
    try {
      const data = await ambilTerkini(kunci);
      if (s === 'cuaca' && data.kelurahan && data.kelurahan.slug !== kelurahanCuaca.value) return; // pilihan sudah berganti
      st.data = data;
      st.galat = data.tersedia ? null : data.galat ?? 'Data tidak tersedia.';
      st.status = 'siap';
    } catch (err) {
      st.galat = err.message;
      if (st.data) { st.data = { ...st.data, stale: true }; st.status = 'siap'; } // data terakhir tetap tampil, berlabel "data lama"
      else st.status = 'galat';
    } finally {
      sedangMuat.delete(kunci);
    }
  }

  function pilihKelurahan(slug) {
    if (slug === kelurahanCuaca.value) return;
    kelurahanCuaca.value = slug;
    sumber.value.cuaca = awal(); // data kelurahan lain tidak boleh tampil sebagai kelurahan ini
    muat('cuaca');
  }

  return { sumber, kelurahanCuaca, titikLaut, muat, pilihKelurahan };
});
