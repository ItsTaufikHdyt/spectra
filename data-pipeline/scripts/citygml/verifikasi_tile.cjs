// Periksa tile v2 satu kelurahan: tileset.json, ukuran/ekstensi .glb, tabel properti (noData dikenali), segitiga.
//   node data-pipeline/scripts/citygml/verifikasi_tile.cjs <folder tileset> <keluaran.json>
// Dekoder meshopt diambil dari frontend/node_modules (hanya dibaca; tidak mengubah frontend).
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '../../..');
const { MeshoptDecoder: D } = require(path.join(ROOT, 'frontend/node_modules/meshoptimizer'));
const dir = process.argv[2];
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(path.join(d, e.name)) : e.name.endsWith('.glb') ? [path.join(d, e.name)] : []));

(async () => {
  await D.ready;
  const ts = JSON.parse(fs.readFileSync(path.join(dir, 'tileset.json')));
  const root = ts.root;
  const tiles = (function* it(t) { yield t; for (const c of t.children || []) yield* it(c); })(root);
  const info = { versi: ts.asset.version, geometricErrorRoot: ts.geometricError, refine: root.refine, transform: !!root.transform, region: root.boundingVolume.region, rootBerkonten: !!root.content,
                 extensionsUsed: ts.extensionsUsed, jumlahTile: [...tiles].length, asetExtras: ts.asset.extras && ts.asset.extras.spectra };
  const PROPERTI = ['id', 'gml_id', 'nama', 'tinggi', 'jumlah_lantai', 'luas_tapak'];
  const glbs = [], ids = [], kolom = {}, tanpaProperti = {};
  let segitiga = 0;
  for (const p of walk(dir)) {
    const b = fs.readFileSync(p); const n = b.readUInt32LE(12); const j = JSON.parse(b.slice(20, 20 + n).toString());
    const bl = b.readUInt32LE(20 + n); const bin = b.slice(28 + n, 28 + n + bl);
    const view = (i) => { const v = j.bufferViews[i]; const m = v.extensions && v.extensions.EXT_meshopt_compression;
      if (m) { const s = bin.slice(m.byteOffset || 0, (m.byteOffset || 0) + m.byteLength); const o = new Uint8Array(m.count * m.byteStride); D.decodeGltfBuffer(o, m.count, m.byteStride, s, m.mode, m.filter || 'NONE'); return Buffer.from(o.buffer, 0, v.byteLength); }
      return bin.slice(v.byteOffset || 0, (v.byteOffset || 0) + v.byteLength); };
    const pr = j.meshes[0].primitives[0];
    const tri = j.accessors[pr.indices].count / 3; segitiga += tri;
    const sm = j.extensions && j.extensions.EXT_structural_metadata;
    const t = sm.propertyTables[0], N = t.count, cls = sm.schema.classes[t.class].properties;
    const kolomIni = {};
    for (const [k, pp] of Object.entries(t.properties)) {
      const raw = view(pp.values);
      if (cls[k].type === 'STRING') { const o = view(pp.stringOffsets); kolomIni[k] = [...Array(N)].map((_, i) => raw.slice(o.readUInt32LE(4 * i), o.readUInt32LE(4 * i + 4)).toString()); }
      else { const nd = cls[k].noData; kolomIni[k] = [...Array(N)].map((_, i) => { const v = cls[k].componentType === 'INT32' ? raw.readInt32LE(4 * i) : raw.readFloatLE(4 * i); return (nd !== undefined && v === nd) || Number.isNaN(v) ? null : v; }); }
    }
    for (const k of PROPERTI) if (!kolomIni[k]) tanpaProperti[k] = (tanpaProperti[k] || 0) + 1; // tyler menghilangkan kolom yang tidak punya nilai di tile
    for (let i = 0; i < N; i++) { ids.push(kolomIni.id[i]); for (const k of PROPERTI) (kolom[k] = kolom[k] || []).push(kolomIni[k] ? kolomIni[k][i] : null); }
    glbs.push({ berkas: path.relative(dir, p), byte: b.length, segitiga: tri, fitur: N, meshFeatures: !!(pr.extensions && pr.extensions.EXT_mesh_features), extensionsUsed: j.extensionsUsed,
                kelas: Object.fromEntries(Object.entries(cls).map(([k, v]) => [k, { type: v.type, componentType: v.componentType, noData: v.noData }])),
                material: j.materials[0].pbrMetallicRoughness.baseColorFactor });
  }
  const hitung = (k) => ({ null: kolom[k].filter((v) => v === null).length, nol: kolom[k].filter((v) => v === 0).length });
  const out = { ...info, glb: glbs, totalByte: glbs.reduce((s, g) => s + g.byte, 0), maksByte: Math.max(...glbs.map((g) => g.byte)), totalSegitiga: segitiga, totalFitur: ids.length,
                idUnik: new Set(ids).size, propertiDiKelas: [...new Set(glbs.flatMap((g) => Object.keys(g.kelas)))].sort(), tileTanpaProperti: tanpaProperti, jumlahLantai: hitung('jumlah_lantai'), luasTapak: hitung('luas_tapak'), tinggi: hitung('tinggi'), ids, kolom };
  fs.writeFileSync(process.argv[3], JSON.stringify(out));
  console.log(path.basename(dir), 'glb', glbs.length, 'fitur', ids.length, 'segitiga', segitiga, 'maks', out.maksByte, 'lantai', JSON.stringify(out.jumlahLantai), 'luas', JSON.stringify(out.luasTapak));
})();
