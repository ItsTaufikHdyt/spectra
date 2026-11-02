import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useMapStore = defineStore('map', () => {
  const activeBasemap = ref('arcgis'); // 'arcgis' | 'osm'
  const is3DTilesActive = ref(true);

  const setBasemap = (type) => {
    activeBasemap.value = type;
  };

  return {
    activeBasemap,
    is3DTilesActive,
    setBasemap
  };
});
