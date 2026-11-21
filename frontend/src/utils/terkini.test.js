import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ikonCuaca, jamLokal, jamWita, mataAngin, slotCuaca, tanggalJamWita, umurDetik } from './terkini.js';

test('jamWita mengubah UTC ke WITA (UTC+8), bukan WIB', () => {
  assert.equal(jamWita('2026-11-21T19:52:18+00:00'), '03:52 WITA'); // BMKG menulis 02:52 WIB
  assert.equal(tanggalJamWita('2026-11-21T19:52:18+00:00'), '22 Nov 03:52 WITA');
  assert.equal(jamWita('2026-11-22T00:00:00Z'), '08:00 WITA');
  assert.equal(jamWita(null), '–');
  assert.equal(jamWita('bukan waktu'), '–');
});

test('jamLokal memotong waktu lokal sumber', () => {
  assert.equal(jamLokal('2026-11-22 07:00:00'), '07:00');
  assert.equal(jamLokal('2026-11-22T13:00'), '13:00');
  assert.equal(jamLokal(undefined), '–');
});

test('mataAngin: delapan arah, melingkar, nilai tak valid -> –', () => {
  assert.deepEqual([0, 45, 90, 135, 180, 225, 270, 315, 360].map(mataAngin), ['U', 'TL', 'T', 'TG', 'S', 'BD', 'B', 'BL', 'U']);
  assert.equal(mataAngin(280), 'B');
  assert.equal(mataAngin(293), 'BL'); // 293° lebih dekat ke 315° (barat laut) daripada 270°
  assert.equal(mataAngin(-10), 'U');
  assert.equal(mataAngin(null), '–');
});

test('slotCuaca memilih slot terakhir yang sudah lewat dan slot berikutnya', () => {
  const jam = ['2026-11-21 23:00:00', '2026-11-22 02:00:00', '2026-11-22 05:00:00', '2026-11-22 08:00:00'].map((u) => ({ waktu_utc: u }));
  const now = Date.parse('2026-11-22T03:00:00Z');
  const r = slotCuaca(jam, now, 2);
  assert.equal(r.sekarang.waktu_utc, '2026-11-22 02:00:00');
  assert.deepEqual(r.berikut.map((s) => s.waktu_utc), ['2026-11-22 05:00:00', '2026-11-22 08:00:00']);
  assert.equal(slotCuaca(jam, Date.parse('2026-11-20T00:00:00Z')).sekarang.waktu_utc, '2026-11-21 23:00:00'); // belum ada yang lewat
  assert.deepEqual(slotCuaca([], now), { sekarang: null, berikut: [] });
});

test('umurDetik', () => {
  assert.equal(umurDetik('2026-11-22T00:00:00+00:00', Date.parse('2026-11-22T00:01:30Z')), 90);
  assert.equal(umurDetik(null), null);
});

test('ikonCuaca: kata kunci BMKG, malam memakai bulan, tidak dikenal -> null', () => {
  assert.equal(ikonCuaca('Cerah', '2026-11-22 13:00:00'), 'cerah');
  assert.equal(ikonCuaca('Cerah', '2026-11-22 19:00:00'), 'cerah-malam');
  assert.equal(ikonCuaca('Cerah Berawan', '2026-11-22 07:00:00'), 'cerah-berawan');
  assert.equal(ikonCuaca('Berawan Tebal'), 'berawan');
  assert.equal(ikonCuaca('Hujan Lebat', '2026-11-22 02:00:00'), 'hujan');
  assert.equal(ikonCuaca('Hujan Petir'), 'petir');
  assert.equal(ikonCuaca('Udara Kabur'), 'kabut');
  assert.equal(ikonCuaca('Entah'), null);
  assert.equal(ikonCuaca(undefined), null);
});
