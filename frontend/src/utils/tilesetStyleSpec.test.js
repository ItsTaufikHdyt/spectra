import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BUILDING_STYLE_COLOR, buildStyleSpec } from './tilesetStyleSpec.js';

test('tema gelap tanpa simulasi: tanpa gaya', () => {
  assert.equal(buildStyleSpec({ theme: 'gelap' }), null);
});

test('tema terang tanpa simulasi: satu kondisi warna tema', () => {
  assert.deepEqual(buildStyleSpec({ theme: 'terang' }), {
    color: { conditions: [['true', `color("${BUILDING_STYLE_COLOR.terang}")`]] }
  });
});

test('simulasi menang atas tema: kondisi simulasi lebih dulu, warna tema sebagai cadangan', () => {
  const sim = { conditions: [['${id} === "BTG-BLD-000001"', 'color("#08306B")']] };
  const terang = buildStyleSpec({ theme: 'terang', simulation: sim });
  assert.equal(terang.color.conditions[0][1], 'color("#08306B")');
  assert.equal(terang.color.conditions.at(-1)[0], 'true');
  assert.ok(terang.color.conditions.at(-1)[1].includes(BUILDING_STYLE_COLOR.terang));
  const gelap = buildStyleSpec({ theme: 'gelap', simulation: sim }); // tema gelap + simulasi tetap menghasilkan gaya
  assert.equal(gelap.color.conditions.length, 2);
  assert.equal(gelap.color.conditions.at(-1)[1], 'color("#FFFFFF")');
});

test('kondisi simulasi yang salah bentuk ditolak', () => {
  assert.throws(() => buildStyleSpec({ theme: 'gelap', simulation: { conditions: [['true']] } }));
  assert.throws(() => buildStyleSpec({ theme: 'gelap', simulation: { conditions: [[1, 2]] } }));
});
