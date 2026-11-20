import test from 'node:test';
import assert from 'node:assert/strict';
import { formatCoord, niceScale } from './coords.js';
import { filterKelurahan } from './search.js';

test('formatCoord memakai koma desimal dan arah mata angin', () => {
  assert.equal(formatCoord(0.12345, 117.5), '0,12345° LU, 117,50000° BT');
  assert.equal(formatCoord(-1.5, -70), '1,50000° LS, 70,00000° BB');
});

test('niceScale membulatkan ke 1/2/5 x 10^n tanpa melebihi jarak', () => {
  assert.deepEqual([niceScale(130).meters, niceScale(130).label], [100, '100 m']);
  assert.equal(niceScale(260).meters, 200);
  assert.equal(niceScale(740).meters, 500);
  assert.equal(niceScale(2500).label, '2 km');
  assert.equal(niceScale(1000).label, '1 km');
  assert.ok(niceScale(740).fraction <= 1);
  assert.equal(niceScale(0), null);
  assert.equal(niceScale(NaN), null);
});

test('filterKelurahan: kosong -> semua; awalan lebih dulu; abaikan huruf besar', () => {
  const l = [{ name: 'Bontang Kuala' }, { name: 'Api Api' }, { name: 'Gunung Elai' }, { name: 'Kanaan' }];
  assert.equal(filterKelurahan(l, '').length, 4);
  assert.deepEqual(filterKelurahan(l, 'ELAI').map((k) => k.name), ['Gunung Elai']);
  assert.deepEqual(filterKelurahan(l, 'a').map((k) => k.name), ['Api Api', 'Bontang Kuala', 'Gunung Elai', 'Kanaan']);
  assert.deepEqual(filterKelurahan(l, 'zzz'), []);
});
