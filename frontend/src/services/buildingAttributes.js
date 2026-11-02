// Lookup atribut bangunan (nama, tinggi, fungsi, dst.) dari backend.
//
// Kondisi saat ini: tile .glb tidak membawa EXT_structural_metadata dan backend belum ada,
// jadi tanpa VITE_API_BASE_URL fungsi ini selalu mengembalikan null ("belum tersedia").
// Kontrak endpoint yang diharapkan (usulan, belum diimplementasikan di backend):
//   GET {VITE_API_BASE_URL}/buildings/{buildingId}/attributes
//   200 -> { "name": "...", "height": 12.5, "function": "...", ... }   404 -> belum ada data
// Catatan: buildingId saat ini berasal dari path tile + featureId (tidak stabil antar ETL);
// lookup yang andal butuh ID bangunan permanen (mis. gml_id CityJSON) di dalam tile.

const API_BASE = (import.meta.env?.VITE_API_BASE_URL ?? '').replace(/\/+$/, '');

/** Kandidat nama kolom atribut (tidak peka huruf besar/kecil), dipakai bersama pickFirst(). */
export const ATTRIBUTE_KEYS = Object.freeze({
  name: ['name', 'nama'],
  height: ['measuredHeight', 'height', 'tinggi'],
  function: ['function', 'fungsi', 'usage', 'penggunaan']
});

export const isAttributeServiceConfigured = () => API_BASE !== '';

/**
 * @param {string} buildingId
 * @param {{ signal?: AbortSignal }} [options]
 * @returns {Promise<Record<string, unknown>|null>} null bila layanan belum ada / data tidak ditemukan
 */
export async function fetchBuildingAttributes(buildingId, { signal } = {}) {
  if (!isAttributeServiceConfigured()) return null;
  const res = await fetch(`${API_BASE}/buildings/${encodeURIComponent(buildingId)}/attributes`, {
    signal,
    headers: { Accept: 'application/json' }
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Layanan atribut merespons HTTP ${res.status}`);
  const data = await res.json();
  return data && typeof data === 'object' && !Array.isArray(data) ? data : null;
}
