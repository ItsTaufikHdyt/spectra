import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useMapStore = defineStore('map', () => {
  const isTerrainActive = ref(true);
  const activeBasemap = ref('arcgis'); // 'arcgis' | 'osm'
  const isOrthophotoActive = ref(true);
  const orthoOpacity = ref(1.0);
  const is3DTilesActive = ref(true);

  const toggleTerrain = () => {
    isTerrainActive.value = !isTerrainActive.value;
  };

  const setBasemap = (type) => {
    activeBasemap.value = type;
  };

  return {
    isTerrainActive,
    activeBasemap,
    isOrthophotoActive,
    orthoOpacity,
    is3DTilesActive,
    toggleTerrain,
    setBasemap
  };
});
