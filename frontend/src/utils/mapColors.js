// Warna yang dipakai di peta DAN legenda — satu sumber agar keduanya tidak menyimpang.
export const MAP_COLORS = Object.freeze({
  building: '#D9DEE2', // perkiraan warna material glb (belum diverifikasi visual)
  overview: '#CFE0E8', // kotak ikhtisar kelurahan saat kamera jauh
  selection: '#F0B43C', // = bontang.accent
  kelurahan: '#FFFFFF', // batas kelurahan (garis tebal, kontras di citra satelit)
  rt: '#C3D3DC', // batas RT (garis tipis)
  sungai: '#38BDF8',
  drainase: '#5EEAD4' // fitur "Drainase …" dibedakan dari sungai (kategori belum diputuskan)
});
