// Daftar basemap — SATU tempat konfigurasi. Komponen dan composable hanya membaca daftar ini,
// jadi mengganti penyedia berarti mengubah entri di sini (tanpa menyentuh komponen).
//
// kind:
//   'arcgis' : ArcGisMapServerImageryProvider (server bertile; atribusi bawaan dari layanan DAN `credit` di bawah
//              ditambahkan sebagai kredit statis karena opsi credit Cesium diabaikan untuk server bertile)
//   'osm'    : OpenStreetMapImageryProvider (`credit` dipasang langsung pada penyedia)
//   'xyz'    : UrlTemplateImageryProvider (mis. CARTO bila nanti disetujui; belum ada entri)
// reference : lapisan label yang digambar di atas basemap (hanya untuk basemap abu Esri).
// fallback  : id basemap yang dipakai bila layanan ini gagal dimuat (pilihan pengguna tidak diubah).
//
// HUTANG (STATUS #37): ketentuan pemakaian layanan Esri (termasuk citra satelit) belum diverifikasi;
// periksa sebelum dipakai publik. Metadata Light Gray menyebut "mature support, no longer updated".

const ESRI = 'https://services.arcgisonline.com/ArcGIS/rest/services';
const ESRI_CREDIT = 'Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community';
const OSM_CREDIT = '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors</a>';

export const BASEMAPS = Object.freeze([
  {
    id: 'terang',
    label: 'Terang',
    kind: 'arcgis',
    url: `${ESRI}/Canvas/World_Light_Gray_Base/MapServer`,
    reference: { url: `${ESRI}/Canvas/World_Light_Gray_Reference/MapServer` },
    credit: ESRI_CREDIT,
    fallback: 'osm'
  },
  {
    id: 'gelap',
    label: 'Gelap',
    kind: 'arcgis',
    url: `${ESRI}/Canvas/World_Dark_Gray_Base/MapServer`,
    reference: { url: `${ESRI}/Canvas/World_Dark_Gray_Reference/MapServer` },
    credit: ESRI_CREDIT,
    fallback: 'satelit'
  },
  {
    id: 'satelit',
    label: 'Citra satelit',
    kind: 'arcgis',
    url: `${ESRI}/World_Imagery/MapServer`,
    credit: 'Esri, Maxar, Earthstar Geographics, and the GIS User Community',
    fallback: 'osm'
  },
  {
    id: 'osm',
    label: 'OpenStreetMap',
    kind: 'osm',
    url: 'https://tile.openstreetmap.org/',
    credit: OSM_CREDIT,
    fallback: null
  }
]);

export const BASEMAP_IDS = Object.freeze(BASEMAPS.map((b) => b.id));
export const basemapById = (id) => BASEMAPS.find((b) => b.id === id) ?? null;
