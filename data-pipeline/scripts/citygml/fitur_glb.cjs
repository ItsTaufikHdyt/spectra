// Per fitur: segitiga, tinggi, pusat ECEF (untuk membandingkan dua versi tile). Pakai: node fitur_glb.cjs <dir tileset> <keluaran.json>
// Dekoder meshopt dari frontend/node_modules (hanya dibaca).
const fs=require('fs'),path=require('path');
const {MeshoptDecoder:D}=require(path.join(__dirname, '../../../frontend/node_modules/meshoptimizer'));
const dir=process.argv[2];const ts=JSON.parse(fs.readFileSync(path.join(dir,'tileset.json')));const T=ts.root.transform||[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const mul=(m,p)=>[0,1,2].map(r=>m[r]*p[0]+m[4+r]*p[1]+m[8+r]*p[2]+m[12+r]);
const walk=d=>fs.readdirSync(d,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(d,e.name)):e.name.endsWith('.glb')?[path.join(d,e.name)]:[]);
(async()=>{await D.ready;const out=[];
for(const p of walk(dir)){const b=fs.readFileSync(p);const n=b.readUInt32LE(12);const j=JSON.parse(b.slice(20,20+n).toString());const bl=b.readUInt32LE(20+n);const bin=b.slice(28+n,28+n+bl);
 const view=i=>{const v=j.bufferViews[i],m=v.extensions&&v.extensions.EXT_meshopt_compression;
  if(m){const s=bin.slice(m.byteOffset||0,(m.byteOffset||0)+m.byteLength);const o=new Uint8Array(m.count*m.byteStride);D.decodeGltfBuffer(o,m.count,m.byteStride,s,m.mode,m.filter||'NONE');return {buf:Buffer.from(o.buffer),stride:m.byteStride};}
  return {buf:bin.slice(v.byteOffset||0,(v.byteOffset||0)+v.byteLength),stride:v.byteStride};};
 const pr=j.meshes[0].primitives[0],M=j.nodes[0].matrix;
 const A=pr.attributes,pa=j.accessors[A.POSITION],fa=j.accessors[A._FEATURE_ID_0],ia=j.accessors[pr.indices];
 const pv=view(pa.bufferView),fv=view(fa.bufferView),iv=view(ia.bufferView);
 const pos=i=>[0,1,2].map(k=>pv.buf.readInt16LE((pa.byteOffset||0)+i*(pv.stride||6)+2*k)/32767);
 const fid=i=>fv.buf.readUInt16LE((fa.byteOffset||0)+i*(fv.stride||2));
 const idx=i=>ia.componentType===5125?iv.buf.readUInt32LE(i*4):iv.buf.readUInt16LE(i*2);
 const f=new Map();
 const ensure=k=>{if(!f.has(k))f.set(k,{tri:0,min:[1e9,1e9,1e9],max:[-1e9,-1e9,-1e9]});return f.get(k)};
 for(let t=0;t<ia.count;t+=3){const a=idx(t);ensure(fid(a)).tri++;}
 for(let i=0;i<pa.count;i++){const e=ensure(fid(i)),q=pos(i);for(let k=0;k<3;k++){e.min[k]=Math.min(e.min[k],q[k]);e.max[k]=Math.max(e.max[k],q[k]);}}
 for(const[k,e]of f){const lo=mul(M,e.min),hi=mul(M,e.max);// matriks node (Y-atas): tinggi = selisih sumbu Y
  const c=[0,1,2].map(i=>(lo[i]+hi[i])/2);const h=Math.abs(hi[1]-lo[1]);
  // Y-atas -> Z-atas: (x,y,z)->(x,-z,y); lalu transform tileset ke ECEF
  const ecef=mul(T,[c[0],-c[2],c[1]]);out.push({tile:path.relative(dir,p),fid:k,tri:e.tri,h,ecef});}}
fs.writeFileSync(process.argv[3],JSON.stringify(out));
console.log(dir,'fitur',out.length,'segitiga',out.reduce((s,x)=>s+x.tri,0));})();
