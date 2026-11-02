import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseContentUrl, pickFirst, slugToName } from './tileMeta.js';

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
