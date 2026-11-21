// Klien API "Kondisi Terkini" (/api/terkini/*, diteruskan proxy Vite ke backend). Browser tidak memanggil BMKG/FIRMS/Open-Meteo langsung.

const PESAN_MATI = 'Backend spectra tidak dapat dihubungi. Pastikan backend berjalan (lihat docs/remote-layers.md).';

/** GET JSON; kegagalan jaringan atau HTTP >= 500 (mis. proxy Vite tanpa backend) menjadi pesan ramah. */
export async function ambilTerkini(path, { signal } = {}) {
  let res;
  try {
    res = await fetch(`/api/terkini/${path}`, { signal, headers: { Accept: 'application/json' } });
  } catch (err) {
    if (err?.name === 'AbortError') throw err;
    throw new Error(PESAN_MATI);
  }
  const data = (res.headers.get('content-type') ?? '').includes('json') ? await res.json().catch(() => null) : null;
  if (!res.ok || !data) throw new Error(res.status >= 500 || !data ? PESAN_MATI : (data?.detail ?? `Permintaan gagal (HTTP ${res.status}).`));
  return data;
}
