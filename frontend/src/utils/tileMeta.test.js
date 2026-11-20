import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseContentUrl, pickFirst, readFeatureProperties, slugToName } from './tileMeta.js';

test('slugToName', () => {
  assert.equal(slugToName('tanjung_laut_indah'), 'Tanjung Laut Indah');
  assert.equal(slugToName(''), '');
});

test('parseContentUrl', () => {
  assert.deepEqual(parseContentUrl('http://x/tiles/api_api/t/3/2/2.glb?v=1'), {
    slug: 'api_api',
    tile: 't/3/2/2'
  });
  assert.deepEqual(parseContentUrl('http://x/lain/a.glb'), { slug: null, tile: 'http://x/lain/a.glb' });
});

test('pickFirst tidak peka huruf besar/kecil dan menganggap 0 valid', () => {
  assert.equal(pickFirst({ Height: 0 }, ['height']), 0);
  assert.equal(pickFirst({ name: '' , nama: 'Masjid' }, ['name', 'nama']), 'Masjid');
  assert.equal(pickFirst({}, ['name']), undefined);
});

test('readFeatureProperties melewati undefined/null (noData) tetapi menyimpan 0 dan string kosong', () => {
  const data = { id: 'BTG-BLD-000001', jumlah_lantai: undefined, luas_tapak: null, tinggi: 0, nama: '' };
  const feature = { getPropertyIds: () => Object.keys(data), getProperty: (k) => data[k] };
  assert.deepEqual(readFeatureProperties(feature), { id: 'BTG-BLD-000001', tinggi: 0, nama: '' });
});

test('readFeatureProperties aman bila konten tanpa property table', () => {
  const feature = { getPropertyIds: () => { throw new Error('tanpa property table'); }, getProperty: () => 1 };
  assert.deepEqual(readFeatureProperties(feature), {});
});
