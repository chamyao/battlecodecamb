// Camp-group rewards (gems, gold, respawn) per group composition, from an engine build and a map.
// Usage: node rewards.js ENGINE.wasm MAP.map26a
'use strict';
process.env.CAMBC_WASM = process.argv[2];
const { Replay, CAMPS } = require('./engine.js');
const r = new Replay(require('fs').readFileSync(process.argv[3]));
const X = r.X, out = X.Engine_Malloc(64), dv = () => new DataView(X.memory.buffer);
const ck = rc => { if (rc) throw new Error('rc ' + rc); };
ck(X.Game_GetNumCampGroups(r.h, out));
const n = dv().getUint32(out, true), res = {};
for (let g = 0; g < n; g++) {
  ck(X.Game_GetCampGroupHandle(r.h, g, out)); const gh = dv().getBigUint64(out, true);
  ck(X.Game_GetCampGroup(r.h, gh, out));
  const [gems, gold, cd, nc] = [0, 4, 8, 12].map(o => dv().getUint32(out + o, true));
  const types = [];
  for (let t = 0; t < nc; t++) {
    ck(X.Game_GetCampGroupCamp(r.h, gh, t, out)); const ch = dv().getBigUint64(out, true);
    ck(X.Game_GetCamp(r.h, ch, out)); types.push(CAMPS[dv().getInt32(out, true)]);
  }
  const c = {}; types.forEach(t => { c[t] = (c[t] || 0) + 1; });
  const key = Object.keys(c).sort().map(k => c[k] > 1 ? `${k}x${c[k]}` : k).join('+');
  res[key] = { gems, gold, respawn: cd };
}
console.log(JSON.stringify(res));
