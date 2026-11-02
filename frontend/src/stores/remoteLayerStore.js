import { defineStore } from 'pinia';
import { ref } from 'vue';
import * as api from '@/services/geoportalApi';

/**
 * Layer geoportal yang ditambahkan pengguna (data biasa; objek Cesium ada di useRemoteLayers.js).
 * Sumber kebenaran status (aktif, warna, opasitas, urutan) = registry backend, jadi tetap ada
 * setelah halaman dimuat ulang.
 */
export const useRemoteLayerStore = defineStore('remoteLayers', () => {
  const layers = ref([]);
  const batasFitur = ref(20000);
  const listStatus = ref('idle'); // 'idle' | 'loading' | 'ready' | 'error'
  const listError = ref('');

  const inspectStatus = ref('idle'); // 'idle' | 'loading' | 'ready' | 'error'
  const inspectError = ref('');
  const inspectResult = ref(null); // { tipe, url, batas_fitur, layers: [...] }

  /** { [kunci]: 'menambahkan' | 'refresh' | 'menghapus' } — kunci = id layer atau typename. */
  const busy = ref({});
  /** { [kunci]: pesan } — kegagalan aksi atau tampilan (mis. WMS gagal dimuat). */
  const errors = ref({});

  const setBusy = (key, action) => {
    const next = { ...busy.value };
    if (action) next[key] = action;
    else delete next[key];
    busy.value = next;
  };
  const setError = (key, message) => {
    const next = { ...errors.value };
    if (message) next[key] = message;
    else delete next[key];
    errors.value = next;
  };
  const replace = (entry) => {
    layers.value = layers.value.map((l) => (l.id === entry.id ? entry : l));
  };

  const load = async () => {
    listStatus.value = 'loading';
    try {
      const data = await api.listLayers();
      layers.value = data.layers;
      batasFitur.value = data.batas_fitur;
      listStatus.value = 'ready';
      listError.value = '';
    } catch (err) {
      listError.value = err.message;
      listStatus.value = 'error';
    }
  };

  const inspect = async (url) => {
    inspectStatus.value = 'loading';
    inspectError.value = '';
    inspectResult.value = null;
    try {
      inspectResult.value = await api.inspectSource(url);
      inspectStatus.value = 'ready';
    } catch (err) {
      inspectError.value = err.message;
      inspectStatus.value = 'error';
    }
  };

  /** row = baris hasil inspect; mode 'geojson' | 'wms'. */
  const add = async (row, mode) => {
    const key = row.typename;
    setBusy(key, 'menambahkan');
    setError(key, null);
    try {
      const entry = await api.addLayer({ wfs_url: row.wfs_url, typename: row.typename, judul: row.judul, mode });
      layers.value = [...layers.value, entry];
      return entry;
    } catch (err) {
      setError(key, err.message);
      return null;
    } finally {
      setBusy(key, null);
    }
  };

  /** Ubah lokal saja (pratinjau langsung di peta, mis. saat slider digeser). */
  const setLocal = (id, patch) => {
    const cur = layers.value.find((l) => l.id === id);
    if (cur) replace({ ...cur, ...patch });
  };

  /** Ubah lokal lalu simpan ke backend; kembalikan ke nilai lama bila gagal. */
  const update = async (id, patch) => {
    const before = layers.value.find((l) => l.id === id);
    if (!before) return;
    setLocal(id, patch);
    setError(id, null);
    try {
      replace(await api.patchLayer(id, patch));
    } catch (err) {
      replace(before);
      setError(id, `Perubahan tidak tersimpan: ${err.message}`);
    }
  };

  const refresh = async (id) => {
    setBusy(id, 'refresh');
    setError(id, null);
    try {
      replace(await api.refreshLayer(id));
    } catch (err) {
      setError(id, err.message);
      await load(); // backend mencatat status error di registry
    } finally {
      setBusy(id, null);
    }
  };

  const remove = async (id) => {
    setBusy(id, 'menghapus');
    setError(id, null);
    try {
      await api.deleteLayer(id);
      layers.value = layers.value.filter((l) => l.id !== id);
    } catch (err) {
      setError(id, err.message);
    } finally {
      setBusy(id, null);
    }
  };

  return {
    layers, batasFitur, listStatus, listError,
    inspectStatus, inspectError, inspectResult,
    busy, errors, setError,
    load, inspect, add, setLocal, update, refresh, remove
  };
});
