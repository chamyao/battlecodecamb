// Dump game settings and champion/camp/item designs from an engine build, to compare
// the Sprint 1 ruleset (v0_0_3) with the current one (v1_0_3).
// Layouts: oracle/tools/parse_dump.py on branch sim/engine.
'use strict';
const fs = require('fs');
process.env.CAMBC_WASM = process.argv[2];
const { Replay, CHAMPS, CAMPS, ITEMS } = require('./engine.js');
const r = new Replay(fs.readFileSync(process.argv[3]));
const X = r.X, out = X.Engine_Malloc(4096);
const dv = () => new DataView(X.memory.buffer);
const SET = [['capture_time', 'i'], ['camp_sleep_time', 'i'], ['respawn_time', 'i'], ['recall_time', 'i'], ['submit_gem_duration_multiplier', 'd'], ['submit_gem_base_duration', 'i'], ['submit_gem_minimum_duration', 'i'], ['submit_gems_range', 'i'], ['max_rounds', 'I'], ['winning_gems', 'I'], ['kill_gold', 'I'], ['assist_gold', 'I'], ['passive_gold', 'I'], ['spawn_healing', 'f'], ['active_wards', 'I'], ['ward_charges', 'I'], ['shared_memory_bytes', 'I'], ['draft_memory_bytes', 'I'], ['tile_reveal_rounds', 'I'], ['ward_cooldown', 'i'], ['ward_lifetime', 'i'], ['ward_vision_radius', 'f'], ['ward_placement_radius', 'f'], ['control_ward_vision_radius', 'f'], ['control_ward_placement_radius', 'f'], ['altar_lock_hits', 'I'], ['tp_scroll_time', 'i'], ['tp_crystal_time', 'i']];
function rd(off, t) { const d = dv(); return t === 'd' ? d.getFloat64(off, true) : t === 'f' ? d.getFloat32(off, true) : t === 'I' ? d.getUint32(off, true) : d.getInt32(off, true); }
function call(f, ...a) { const rc = f(...a); if (rc) throw new Error('rc ' + rc); }
const res = { settings: {}, champions: {}, camps: {}, items: {} };
call(X.Game_API_GetSettings, out);
let o = 0;
for (const [n, t] of SET) { if (t === 'd' && o % 8) o += 4; res.settings[n] = rd(out + o, t); o += t === 'd' ? 8 : 4; }
function ability(off) {
  const d = dv(); const kind = d.getUint32(off, true);
  const a = { kind: ['none', 'attack_reset', 'damage', 'aoe_damage', 'cc', 'heal', 'dash', 'shield'][kind], cooldown: d.getInt32(off + 4, true) };
  const f = k => +d.getFloat32(off + 20 + k * 4, true).toFixed(3);
  if (a.kind === 'damage' || a.kind === 'heal') Object.assign(a, { range: f(0), modifier: f(1) });
  if (a.kind === 'aoe_damage' || a.kind === 'dash') Object.assign(a, { range: f(0), radius: f(1), modifier: f(2), dur: d.getInt32(off + 32, true) });
  if (a.kind === 'cc' || a.kind === 'shield') Object.assign(a, { range: f(0), modifier: f(1), dur: d.getInt32(off + 28, true) });
  return a;
}
const statN = ['vision', 'move', 'range', 'health', 'health_g', 'str', 'str_g', 'focus', 'focus_g', 'camp_mult'];
for (let t = 0; t < 13; t++) {
  if (X.Game_API_Champion_Design(r.h, t, out)) continue;
  const d = dv(), st = {};
  statN.forEach((n, k) => { st[n] = k < 3 ? d.getInt32(out + 88 + k * 4, true) : +d.getFloat32(out + 88 + k * 4, true).toFixed(3); });
  res.champions[CHAMPS[t]] = { stats: st, abilities: [ability(out + 12), ability(out + 48)] };
}
for (let t = 0; t < 6; t++) {
  if (X.Game_API_Camp_Design(r.h, t, out)) continue;
  const d = dv();
  res.camps[CAMPS[t]] = { health: d.getFloat32(out + 88 + 12, true), str: d.getFloat32(out + 88 + 20, true), range: d.getInt32(out + 88 + 8, true), abilities: [ability(out + 12), ability(out + 48)] };
}
for (let t = 0; t < ITEMS.length; t += 2) {
  if (X.Game_API_GetItemInfo(t, out)) continue;
  const d = dv(); res.items[ITEMS[t]] = { cost: d.getUint32(out, true), hp: d.getInt32(out + 8, true), str: d.getInt32(out + 12, true), focus: d.getInt32(out + 16, true), passive: d.getUint32(out + 20, true), mag: +d.getFloat32(out + 24, true).toFixed(3) };
}
console.log(JSON.stringify(res, null, 0));
