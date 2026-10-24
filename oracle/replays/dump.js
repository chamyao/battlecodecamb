// Dump a .repl26a replay as per-champion-turn records for the differential replayer:
// one JSON line per champion turn: the engine state just before its first action (after
// start-of-turn processing) and the actions it took. First line: drafts.
// Usage: node dump.js REPLAY OUT.jsonl
'use strict';
const fs = require('fs');
const { Replay, STEPS } = require(process.env.CAMBC_ENGINE_JS || './engine.js');
const r = new Replay(fs.readFileSync(process.argv[2]));
const out = fs.openSync(process.argv[3], 'w');
const NONE = 4294967295;
const f32bits = x => { const b = Buffer.alloc(4); b.writeFloatLE(x); return b.readInt32LE(); };
const snap = s => ({
  ch: s.champions.map(c => [c.team, c.type, +c.alive, c.position ? c.position.x : -1, c.position ? c.position.y : -1,
    Math.round(c.health * 100) / 100, c.gold, c.gems, c.kills]),
  camps: s.camps.map(c => [c.position.x, c.position.y, Math.round(c.health * 100) / 100]),
  sub: s.submittedGems,
});
let prev = null, cur = null, last = null, lastLen = 0;
const flush = () => { if (cur) fs.writeSync(out, JSON.stringify(cur) + '\n'); cur = null; };
r.walk(s => {
  const st = s.step, k = STEPS[st.kind];
  // Only steps that consume an input are actions (automatic ones, e.g. a recall completing
  // as a Move, keep the input position); the snapshot is taken just before the first one.
  const input = prev && s.inputPosition > prev.inputPosition;
  if (input && st.actor.kind === 1 && s.currentChampion !== NONE && st.actor.index === s.currentChampion && k !== 'Tick') {
    const c = s.currentChampion;
    if (!cur || cur.c !== c || cur.r !== s.round || cur.ended) {
      flush();
      const ent = prev.champions.find(x => x.entity.index === c);
      cur = { r: s.round, c, team: ent.team, type: ent.type, before: snap(prev), acts: [] };
    }
    if (k === 'End turn') cur.ended = true;
    else {
      const a = { k };
      if (st.from.x || st.from.y) a.f = [st.from.x, st.from.y];
      if (st.to.x || st.to.y) a.t = [st.to.x, st.to.y];
      if (st.abilitySlot !== undefined) a.sl = st.abilitySlot;
      if (k === 'Set priority') a.p = f32bits(st.priority);
      if (k === 'Shop' || k === 'Sell item') {
        const pa = prev.champions.find(x => x.entity.index === c), sa = s.champions.find(x => x.entity.index === c);
        a.items = []; for (let j = 0; j < sa.items.length; j++) if (sa.items[j] !== pa.items[j]) a.items.push([j, sa.items[j] - pa.items[j]]);
        a.cons = []; for (let j = 0; j < 4; j++) if (sa.consumables[j] !== pa.consumables[j]) a.cons.push([j, sa.consumables[j] - pa.consumables[j]]);
      }
      cur.acts.push(a);
    }
  }
  prev = s; last = s;
});
flush();
fs.writeSync(out, JSON.stringify({ final: true, drafts: last.drafts, round: last.round, outcome: last.outcome, after: snap(last) }) + '\n');
fs.closeSync(out);
