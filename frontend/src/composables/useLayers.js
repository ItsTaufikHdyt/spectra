import * as Cesium from 'cesium';
import { viewer } from './useCesium';
import { useMapStore } from '@/stores/mapStore';
import { watch } from 'vue';

export function useLayers() {
  const mapStore = useMapStore();
  let arcgisLayer = null;
  let osmLayer = null;

  const initBasemaps = async () => {
    if (!viewer.value) return;

    // ArcGIS Imagery
    const arcgisProvider = await Cesium.ArcGisMapServerImageryProvider.fromUrl(
      'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
    );
    arcgisLayer = viewer.value.imageryLayers.addImageryProvider(arcgisProvider);

    // OpenStreetMap
    const osmProvider = new Cesium.OpenStreetMapImageryProvider({
      url: 'https://tile.openstreetmap.org/'
    });
    osmLayer = viewer.value.imageryLayers.addImageryProvider(osmProvider);
    osmLayer.show = false; // Default off
  };

  // Watcher ganti basemap
  watch(() => mapStore.activeBasemap, (newVal) => {
    if (arcgisLayer && osmLayer) {
      arcgisLayer.show = newVal === 'arcgis';
      osmLayer.show = newVal === 'osm';
    }
  });

  // Watcher Terrain ON / OFF
  watch(() => mapStore.isTerrainActive, (isActive) => {
    if (!viewer.value) return;
    if (isActive) {
      viewer.value.scene.globe.depthTestAgainstTerrain = true;
      // Gunakan World Terrain bawaan Cesium Ion atau Terrain 1m lokal
      viewer.value.scene.terrainProvider = new Cesium.EllipsoidTerrainProvider();
    } else {
      viewer.value.scene.terrainProvider = new Cesium.EllipsoidTerrainProvider();
      viewer.value.scene.globe.depthTestAgainstTerrain = false;
    }
  });

  return {
    initBasemaps
  };
}
