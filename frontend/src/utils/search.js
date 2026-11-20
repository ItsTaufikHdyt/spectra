// Penyaringan daftar kelurahan untuk kotak pencarian di header.

const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

/** Kelurahan yang namanya memuat `query`; yang diawali query lebih dulu. Query kosong -> semua. */
export function filterKelurahan(list, query) {
  const q = norm(query ?? '');
  if (!q) return list;
  const cocok = list.filter((k) => norm(k.name).includes(q));
  return [...cocok.filter((k) => norm(k.name).startsWith(q)), ...cocok.filter((k) => !norm(k.name).startsWith(q))];
}
