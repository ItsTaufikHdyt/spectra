import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useMapStore = defineStore('map', () => {
  const activeBasemap = ref('arcgis'); // 'arcgis' | 'osm'
  const isOrthophotoActive = ref(true);
  const orthoOpacity = ref(1.0);
  const is3DTilesActive = ref(true);

  const setBasemap = (type) => {
    activeBasemap.value = type;
  };

  return {
    activeBasemap,
    isOrthophotoActive,
    orthoOpacity,
    is3DTilesActive,
    setBasemap
  };
});
