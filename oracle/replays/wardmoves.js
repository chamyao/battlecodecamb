// Every 1-tile Move / Movement blocked input onto a tile holding a ward that is not the mover's
// own, with candidate features. One JSON line per case.
// Usage: node wardmoves.js REPLAY
'use strict';
const fs = require('fs');
const { Replay, STEPS } = require(process.env.CAMBC_ENGINE_JS || './engine.js');
const r = new Replay(fs.readFileSync(process.argv[2]));
const X = r.X; const buf = X.Engine_Malloc(X.Game_Visualiser_SnapshotSize()); const persp = X.Engine_Malloc(8);
const wards = () => {
  const dv = r.dv; dv.setUint32(persp, 2, true); dv.setUint32(persp + 4, 4294967295, true);
  r.check(X.Game_Visualiser_ReadState(r.h, persp, buf));
  const n = dv.getUint32(buf + 132, true), out = [];
  for (let i = 0; i < n; i++) { const o = buf + 133436 + i * 40; out.push({ owner: dv.getInt32(o + 12, true), team: dv.getInt32(o + 16, true), x: dv.getInt32(o + 20, true), y: dv.getInt32(o + 24, true), dis: dv.getUint8(o + 36) }); }
  return out;
};
let prev = null, turnKey = null, movedThisTurn = false, acts = [], W = null;
const placed = {};  // owner -> round of last Place ward
r.walk(s => {
  const st = s.step, k = STEPS[st.kind];
  const input = prev && s.inputPosition > prev.inputPosition && st.actor.kind === 1;
  if (input) {
    const key = s.round + ':' + st.actor.index;
    if (key !== turnKey) { turnKey = key; movedThisTurn = false; acts = []; }
    if (k === 'Place ward') { placed[st.actor.index] = s.round; W = null; }
    if ((k === 'Move' || k === 'Movement blocked') && !movedThisTurn &&
        Math.max(Math.abs(st.from.x - st.to.x), Math.abs(st.from.y - st.to.y)) === 1) {
      const me = prev.champions.find(c => c.entity.index === st.actor.index);
      const occ = prev.champions.some(c => c.alive && c.position && c.position.x === st.to.x && c.position.y === st.to.y) ||
        prev.camps.some(c => c.health > 0 && c.position.x === st.to.x && c.position.y === st.to.y);
      if (!W) W = wards();
      const here = W.filter(w => w.x === st.to.x && w.y === st.to.y && w.owner !== st.actor.index);
      if (here.length && !occ) {
        const own = W.find(w => w.owner === st.actor.index);
        const ow = prev.champions.find(c => c.entity.index === here[0].owner);
        console.log(JSON.stringify({ r: s.round, actor: st.actor.index, team: me.team, type: me.type, from: [st.from.x, st.from.y], to: [st.to.x, st.to.y],
          ok: k === 'Move', wards: here, ownerAlive: ow ? ow.alive : null, ownerPos: ow && ow.position ? [ow.position.x, ow.position.y] : null,
          placedRound: placed[here[0].owner], ownWard: own ? [own.x, own.y] : null, prior: acts.slice(), stunned: !!me.stunSource }));
      }
    }
    if (k === 'Move') movedThisTurn = true;
    acts.push(k);
  }
  prev = s;
});
