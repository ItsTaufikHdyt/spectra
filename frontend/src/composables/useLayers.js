import * as Cesium from 'cesium';
import { requestRender, viewer } from './useCesium';
import { useMapStore } from '@/stores/mapStore';
import { watch } from 'vue';

// Terrain DTM belum tersambung: data quantized-mesh 1m belum ada di proyek.
// Globe memakai EllipsoidTerrainProvider bawaan Viewer; UI menampilkan "Segera hadir".

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
    requestRender();
  };

  // Watcher ganti basemap
  watch(() => mapStore.activeBasemap, (newVal) => {
    if (arcgisLayer && osmLayer) {
      arcgisLayer.show = newVal === 'arcgis';
      osmLayer.show = newVal === 'osm';
      requestRender();
    }
  });

  return {
    initBasemaps
  };
}
