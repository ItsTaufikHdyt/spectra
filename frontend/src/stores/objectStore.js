import { defineStore } from 'pinia';
import { ref } from 'vue';
import { fetchBuildingAttributes, isAttributeServiceConfigured } from '@/services/buildingAttributes';

const hasEntries = (obj) => !!obj && Object.keys(obj).length > 0;

export const useObjectStore = defineStore('object', () => {
  /**
   * Objek terpilih (data biasa, tanpa objek Cesium):
   * { identity: { id, name, kelurahan, category }, attributes: {}, location: {...}|null,
   *   tile: { path, featureId } }
   */
  const selectedObject = ref(null);
  /** Atribut final yang ditampilkan: dari tile (property table) atau dari backend. */
  const attributes = ref(null);
  /** 'idle' | 'loading' | 'ready' | 'unavailable' | 'error' */
  const attributeStatus = ref('idle');
  const attributeError = ref('');

  let controller = null; // membatalkan lookup lama saat pilihan berganti

  const resetAttributes = () => {
    controller?.abort();
    controller = null;
    attributes.value = null;
    attributeError.value = '';
  };

  const loadAttributes = async () => {
    const obj = selectedObject.value;
    resetAttributes();
    if (!obj) {
      attributeStatus.value = 'idle';
      return;
    }
    // Jalur 1: tile sudah membawa atribut.
    if (hasEntries(obj.attributes)) {
      attributes.value = obj.attributes;
      attributeStatus.value = 'ready';
      return;
    }
    // Jalur 2: lookup backend (belum ada -> langsung "belum tersedia").
    if (!isAttributeServiceConfigured()) {
      attributeStatus.value = 'unavailable';
      return;
    }
    const c = (controller = new AbortController());
    attributeStatus.value = 'loading';
    try {
      const result = await fetchBuildingAttributes(obj.identity.id, { signal: c.signal });
      if (c !== controller) return; // pilihan sudah berganti
      attributes.value = hasEntries(result) ? result : null;
      attributeStatus.value = attributes.value ? 'ready' : 'unavailable';
    } catch (err) {
      if (c !== controller || err?.name === 'AbortError') return;
      attributeError.value = err?.message ?? String(err);
      attributeStatus.value = 'error';
    }
  };

  const selectObject = (data) => {
    selectedObject.value = data;
    loadAttributes();
  };

  const clearSelection = () => {
    resetAttributes();
    selectedObject.value = null;
    attributeStatus.value = 'idle';
  };

  return {
    selectedObject,
    attributes,
    attributeStatus,
    attributeError,
    selectObject,
    clearSelection,
    retryAttributes: loadAttributes
  };
});
