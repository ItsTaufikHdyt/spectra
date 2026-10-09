import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useObjectStore = defineStore('object', () => {
  const selectedObject = ref(null);

  const selectObject = (data) => {
    selectedObject.value = data;
  };

  const clearSelection = () => {
    selectedObject.value = null;
  };

  return {
    selectedObject,
    selectObject,
    clearSelection
  };
});
