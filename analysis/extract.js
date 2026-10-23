// Extract one replay into a compact JSON record for analysis.
// Usage: node extract.js <replay.repl26a> <out.json>
'use strict';
const fs = require('fs');
const { Replay, STEPS } = require('./engine.js');

const KEEP = new Set(['Attack', 'Cast ability', 'Recall', 'Submit gems', 'Shop', 'Place ward', 'Consumable', 'Cancel channel',
  'Gems submitted', 'Draft champion', 'Place altar lock', 'Teleport channel', 'Teleport complete', 'Capture', 'Respawn', 'Resign', 'Sell item', 'Bot error']);

function main(inp, outp) {
  const bytes = fs.readFileSync(inp);
  const r = new Replay(bytes);
  const ev = [];
  const rounds = [];   // per round end: [round, subA, subB, per champion [gold, gems, alive, kills, x, y, hp]]
  let prev, first, last, lastRound = -1;
  const pos = c => (c.position ? [c.position.x, c.position.y] : [-1, -1]);
  const at = (s, p) => {
    for (const c of s.champions) if (c.alive && c.position && c.position.x === p.x && c.position.y === p.y) return ['C', c.entity.index];
    for (const c of s.camps) if (c.position.x === p.x && c.position.y === p.y && c.health > 0) return ['M', c.entity.index];
    return null;
  };
  r.walk(s => {
    if (!first && s.champions.length) first = s;
    const k = STEPS[s.step.kind];
    if (prev && s.round !== prev.round && prev.champions.length) {
      rounds.push([prev.round, prev.submittedGems[0], prev.submittedGems[1],
        prev.champions.map(c => [c.gold, c.gems, +c.alive, c.kills, ...pos(c), Math.round(c.health)])]);
    }
    if (prev && prev.champions.length === s.champions.length) {
      const diffs = [];
      for (let i = 0; i < s.champions.length; i++) {
        const a = prev.champions[i], b = s.champions[i], d = { i };
        let any = false;
        if (a.gold !== b.gold) { d.gold = b.gold - a.gold; any = true; }
        if (a.gems !== b.gems) { d.gems = b.gems - a.gems; any = true; }
        if (a.kills !== b.kills) { d.kills = b.kills - a.kills; any = true; }
        if (a.alive !== b.alive) { d.alive = +b.alive; any = true; }
        const it = []; for (let j = 0; j < b.items.length; j++) if (a.items[j] !== b.items[j]) it.push([j, b.items[j] - a.items[j]]);
        if (it.length) { d.items = it; any = true; }
        const co = []; for (let j = 0; j < 4; j++) if (a.consumables[j] !== b.consumables[j]) co.push([j, b.consumables[j] - a.consumables[j]]);
        if (co.length) { d.cons = co; any = true; }
        if ((k === 'Attack' || k === 'Cast ability') && a.health !== b.health) { d.hp = Math.round(b.health - a.health); any = true; }
        if (any) { if (k === 'Capture' || k === 'Gems submitted' || d.alive !== undefined) d.p = pos(a); diffs.push(d); }
      }
      const campd = [];
      if (k === 'Attack' || k === 'Cast ability') {
        const m = new Map(prev.camps.map(c => [c.entity.index, c.health]));
        for (const c of s.camps) { const h = m.get(c.entity.index); if (h !== undefined && h !== c.health) campd.push([c.entity.index, Math.round(c.health - h)]); }
      }
      const subd = [s.submittedGems[0] - prev.submittedGems[0], s.submittedGems[1] - prev.submittedGems[1]];
      if (KEEP.has(k) || diffs.length || subd[0] || subd[1]) {
        const e = { r: s.round, k, a: [s.step.actor.kind, s.step.actor.index] };
        if (s.step.from.x || s.step.from.y) e.f = [s.step.from.x, s.step.from.y];
        if (s.step.to.x || s.step.to.y) e.t = [s.step.to.x, s.step.to.y];
        if (s.step.abilitySlot !== undefined) { e.sl = s.step.abilitySlot; e.ty = s.step.abilityType; }
        if ((k === 'Attack' || k === 'Cast ability') && e.t) { const tg = at(prev, s.step.to); if (tg) e.tg = tg; }
        if (diffs.length) e.d = diffs;
        if (campd.length) e.cd = campd;
        if (subd[0] || subd[1]) e.sub = subd;
        ev.push(e);
      }
    }
    prev = s; last = s;
  });
  rounds.push([last.round, last.submittedGems[0], last.submittedGems[1],
    last.champions.map(c => [c.gold, c.gems, +c.alive, c.kills, ...pos(c), Math.round(c.health)])]);
  const out = {
    file: inp, rounds_played: last.round, outcome: last.outcome, submitted: last.submittedGems,
    drafts: last.drafts, draftCounts: last.draftCounts,
    champions: first.champions.map(c => ({ i: c.entity.index, team: c.team, type: c.type, maxHealth: c.maxHealth })),
    final: last.champions.map(c => ({ i: c.entity.index, gold: c.gold, gems: c.gems, kills: c.kills, alive: c.alive, items: c.items, cons: c.consumables })),
    camps: first.camps.map(c => ({ i: c.entity.index, type: c.type, x: c.position.x, y: c.position.y, hp: c.health })),
    events: ev, rounds,
  };
  fs.writeFileSync(outp, JSON.stringify(out));
}
main(process.argv[2], process.argv[3]);
