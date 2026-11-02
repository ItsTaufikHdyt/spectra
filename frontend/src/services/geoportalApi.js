// Klien API backend spectra untuk layer geoportal (/api, diteruskan proxy Vite ke backend/).
// Browser tidak pernah memanggil WFS/CSW geoportal secara langsung.

const BASE = '/api';

/** fetch JSON + pesan error berbahasa Indonesia dari field `detail` backend. */
async function request(path, { method = 'GET', body } = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined
    });
  } catch {
    throw new Error('Backend spectra tidak dapat dihubungi. Pastikan backend berjalan (lihat docs/remote-layers.md).');
  }
  if (res.status === 204) return null;
  const type = res.headers.get('content-type') ?? '';
  const data = type.includes('json') ? await res.json().catch(() => null) : null;
  if (!res.ok) {
    const detail = data?.detail;
    // Error validasi FastAPI berupa array; ambil pesan pertama.
    const message = Array.isArray(detail) ? detail[0]?.msg : detail;
    // Tanpa `detail` + 5xx = proxy Vite gagal menjangkau backend (backend mati).
    const err = new Error(message || (res.status >= 500
      ? 'Backend spectra tidak dapat dihubungi. Pastikan backend berjalan (lihat docs/remote-layers.md).'
      : `Permintaan gagal (HTTP ${res.status}).`));
    err.status = res.status;
    err.saran = data?.saran;
    throw err;
  }
  if (data === null) throw new Error('Respons backend bukan JSON. Pastikan backend berjalan di balik proxy /api.');
  return data;
}

export const inspectSource = (url) => request('/sources/inspect', { method: 'POST', body: { url } });
export const listLayers = () => request('/layers');
export const addLayer = (payload) => request('/layers', { method: 'POST', body: payload });
export const patchLayer = (id, patch) => request(`/layers/${encodeURIComponent(id)}`, { method: 'PATCH', body: patch });
export const refreshLayer = (id) => request(`/layers/${encodeURIComponent(id)}/refresh`, { method: 'POST' });
export const deleteLayer = (id) => request(`/layers/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const layerDataUrl = (id) => `${BASE}/layers/${encodeURIComponent(id)}/data`;
