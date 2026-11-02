import { defineStore } from 'pinia';
import { ref } from 'vue';

/**
 * State simulasi (terpisah dari mapStore/layer). HANYA data biasa:
 * objek Cesium hasil simulasi dipegang useSimulation.js di variabel modul.
 */
export const useSimulationStore = defineStore('simulation', () => {
  const activeId = ref(null);
  const params = ref({});
  /** 'idle' | 'loading' | 'active' | 'error' */
  const status = ref('idle');
  const error = ref('');
  const visible = ref(true);

  const reset = () => {
    activeId.value = null;
    params.value = {};
    status.value = 'idle';
    error.value = '';
    visible.value = true;
  };

  return { activeId, params, status, error, visible, reset };
});
