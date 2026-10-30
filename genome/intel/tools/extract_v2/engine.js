// Load the official engine (WASM, extracted from the cambc visualiser) and walk a
// .repl26a replay step by step. Snapshot layouts copied from the visualiser bundle
// (PanelChrome-*.js: functions Tr/yr). Engine versions v1_0_3 (cambc 3.0.5) and v2_0_0 (cambc 4.0.0; layout from visualiser index/PanelChrome mr()).
'use strict';
const fs = require('fs');
const path = require('path');

const WASM = process.env.CAMBC_WASM || path.join(__dirname, 'engine', 'v1_0_3.wasm');

const ITEMS = ('Monster Shard of Strength.Monster Emblem of Strength.Monster Shard of Focus.Monster Emblem of Focus.Monster Shard of Health.Monster Emblem of Health.Power Shard of Strength.Power Emblem of Strength.Power Shard of Focus.Power Emblem of Focus.Power Shard of Health.Power Emblem of Health.Durability Shard of Strength.Durability Emblem of Strength.Durability Shard of Focus.Durability Emblem of Focus.Durability Shard of Health.Durability Emblem of Health.Treasure Shard of Strength.Treasure Emblem of Strength.Treasure Shard of Focus.Treasure Emblem of Focus.Treasure Shard of Health.Treasure Emblem of Health.Jungle Shard of Strength.Jungle Emblem of Strength.Jungle Shard of Focus.Jungle Emblem of Focus.Jungle Shard of Health.Jungle Emblem of Health.Home Shard of Strength.Home Emblem of Strength.Home Shard of Focus.Home Emblem of Focus.Home Shard of Health.Home Emblem of Health.Bruiser Shard of Strength.Bruiser Emblem of Strength.Bruiser Shard of Focus.Bruiser Emblem of Focus.Bruiser Shard of Health.Bruiser Emblem of Health' + ['Tribute', 'Capture', 'Prospector', 'Hunter', 'Skirmish', 'Greed', 'Collectors'].map(f => ['Strength', 'Focus', 'Health'].map(s => `.${f} Shard of ${s}.${f} Emblem of ${s}`).join('')).join('')).split('.');
const CHAMPS = ['Ryth', 'Vesper Vale', 'Vendetta', 'Cassi', 'Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart of Ruin'];
const DRAFT = ['Ryth', 'Vesper Vale', 'Vendetta', 'Cassi & Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart of Ruin'];
const CAMPS = ['wolf', 'elk', 'gem_cluster', 'gold_cluster', 'monolith', 'golem'];
const STEPS = 'Phase.Respawn.Capture.Tick.Move.Attack.Cast ability.Input.End turn.Set priority..Recall.Submit gems.Shop.Place ward.Consumable.Cancel channel.Sandbox.Gems submitted.Draft champion.Place altar lock.Teleport channel.Teleport complete.Movement blocked.Resign.Sell item.Turn rollover.Bot error'.split('.');
const CONSUMABLES = ['altar_lock', 'teleport_crystal', 'c2', 'c3'];

let wasmModule;
function instantiate() {
  wasmModule = wasmModule || new WebAssembly.Module(fs.readFileSync(WASM));
  let mem;
  let out = '';
  const wasi = {
    random_get: () => 0, clock_time_get: () => 0,
    environ_sizes_get(a, b) { const d = new DataView(mem.buffer); d.setUint32(a, 0, true); d.setUint32(b, 0, true); return 0; },
    environ_get: () => 0, args_sizes_get: () => 0, args_get: () => 0, fd_close: () => 0,
    fd_fdstat_get: () => 0, fd_prestat_get: () => 8, fd_prestat_dir_name: () => 8, fd_read: () => 8, fd_seek: () => 70,
    fd_write(fd, iov, n, nw) {
      const d = new DataView(mem.buffer); let c = 0;
      for (let i = 0; i < n; i++) { const p = d.getUint32(iov + i * 8, true), l = d.getUint32(iov + i * 8 + 4, true); out += Buffer.from(mem.buffer, p, l).toString(); c += l; }
      d.setUint32(nw, c, true); return 0;
    },
    proc_exit(c) { throw new Error('exit ' + c); },
  };
  const inst = new WebAssembly.Instance(wasmModule, { wasi_snapshot_preview1: wasi });
  mem = inst.exports.memory;
  inst.exports._initialize();
  return inst.exports;
}

class Replay {
  constructor(bytes) {
    const X = this.X = instantiate();
    this.out = X.Engine_Malloc(32);
    this.args = X.Engine_Malloc(128);
    const p = X.Engine_Malloc(bytes.length);
    new Uint8Array(X.memory.buffer, p, bytes.length).set(bytes);
    const isMap = bytes.readUInt32LE(0) === 0x70323677; // 'w62p': a .map26a, not a replay
    this.check(isMap ? X.Game_FromMapFileBytes(p, bytes.length, this.out, 0) : X.Game_FromReplayFileBytes(p, bytes.length, this.out));
    this.h = this.dv.getBigUint64(this.out, true);
    X.Engine_Free(p);
    if (isMap) return;
    this.snapSize = X.Game_Visualiser_TimelineSnapshotSize();
    if (this.snapSize !== 40152 && this.snapSize !== 42840) throw new Error('snapshot layout ' + this.snapSize);
    this.snap = X.Engine_Malloc(this.snapSize);
    this.check(X.Game_Visualiser_Timeline_GetMain(this.h, this.out));
    this.timeline = this.dv.getBigUint64(this.out, true);
    this.check(X.Game_Visualiser_Timeline_Info(this.h, this.timeline, this.args, this.args + 8, this.args + 16));
    this.size = this.dv.getUint32(this.args, true);
  }
  get dv() { return new DataView(this.X.memory.buffer); }
  check(rc) {
    if (rc === 0) return;
    const X = this.X, p = X.GetLastErrorMsg(); const m = new Uint8Array(X.memory.buffer); let e = p; while (m[e]) e++;
    throw new Error('engine error ' + rc + ': ' + Buffer.from(m.subarray(p, e)).toString());
  }
  seek(pos) { this.check(this.X.Game_Visualiser_Timeline_Seek(this.h, this.timeline, pos, 0)); }
  next() { this.check(this.X.Game_Visualiser_Timeline_ReplayNext(this.h, 1)); }
  state() {
    this.check(this.X.Game_Visualiser_ReadTimelineState(this.h, this.snap));
    return decodeTimeline(this.dv, this.snap, this.snapSize);
  }
  // Walk the whole main timeline, calling fn(state) at every step.
  walk(fn) {
    this.seek(0);
    let s = this.state();
    for (;;) {
      fn(s);
      if (s.outcome || (s.awaitingInput && s.inputPosition >= this.size)) break;
      this.next();
      const t = this.state();
      if (t.inputPosition === s.inputPosition && t.step.substep === s.step.substep) throw new Error('no progress');
      s = t;
    }
  }
}

function gr(e, t, n) { const r = new Array(n); for (let i = 0; i < n; i++) r[i] = e.getUint32(t + i * 4, true); return r; }

// Tr(): header shared by game and timeline snapshots.
function header(e, t, n, r) {
  const i = o => e.getUint32(t + o, true), a = o => e.getInt32(t + o, true);
  if (i(0) !== 1 || i(4) !== n) throw new Error('Unsupported snapshot ABI');
  const o = i(108), c = i(68), s = o !== 4294967295 && c !== 19;
  const drafts = [[], []];
  for (let k = 0; k < 2; k++) for (let j = 0; j < 5; j++) drafts[k].push(a(r + 12 + k * 20 + j * 4));
  return {
    draftNumRounds: i(r), draftCounts: [i(r + 4), i(r + 8)], drafts,
    round: i(8), turn: i(12), team: i(16), awaitingInput: !!i(20), phase: i(24), outcome: i(28),
    submittedGems: [Number(e.getBigUint64(t + 32, true)), Number(e.getBigUint64(t + 40, true))],
    inputPosition: i(56), currentChampion: i(60),
    step: {
      phase: i(64), kind: c, actor: { kind: i(72), index: i(76) },
      from: { x: a(80), y: a(84) }, to: { x: a(88), y: a(92) }, round: i(96), inputPosition: i(100), substep: i(104),
      abilitySlot: s ? o : undefined, abilityType: s ? i(112) : undefined, priority: e.getFloat32(t + 116, true),
      raw108: o,
    },
  };
}

// yr(): timeline snapshot.
// v2 (42840): 84 items per champion (+168 bytes), so later champion fields and every list after champions shift.
function decodeTimeline(e, t, size = 40152) {
  const v2 = size === 42840, ci = v2 ? 168 : 0, ca = v2 ? 2688 : 0, ni = v2 ? 84 : 42;
  const n = header(e, t, size, 120);
  const r = o => e.getUint32(t + o, true), i = o => e.getInt32(t + o, true), a = o => e.getFloat32(t + o, true);
  const ent = o => ({ kind: r(o), index: r(o + 4) });
  function list(countOff, dataOff, stride, cap, f) {
    const c = r(countOff); if (c > cap) throw new Error('bad count');
    const out = new Array(c); for (let k = 0; k < c; k++) out[k] = f(dataOff + k * stride); return out;
  }
  n.champions = list(172, 196, 252 + ci, 16, o => ({
    entity: ent(o), team: r(o + 8), type: r(o + 12),
    position: i(o + 16) >= 0 && i(o + 20) >= 0 ? { x: i(o + 16), y: i(o + 20) } : undefined,
    health: a(o + 24), maxHealth: a(o + 28), alive: !!r(o + 32), gold: r(o + 36), gems: r(o + 40), kills: r(o + 44),
    items: gr(e, t + o + 48, ni), consumables: gr(e, t + o + ci + 216, 4), abilityTargets: [r(o + ci + 232), r(o + ci + 236)],
    stunSource: r(o + ci + 248) ? ent(o + ci + 240) : undefined,
  }));
  n.camps = list(176, 4228 + ca, 28, 500, o => ({ entity: ent(o), team: r(o + 8), type: r(o + 12), position: { x: i(o + 16), y: i(o + 20) }, health: a(o + 24) }));
  n.groups = list(180, 18228 + ca, 8, 500, o => ({ rewardAvailable: !!r(o), captureTeam: r(o + 4) }));
  n.wards = list(184, 22228 + ca, 8, 128, o => ({ team: r(o), disabled: !!r(o + 4) }));
  n.spells = list(192, 23764 + ca, 16, 1024, o => ({ entity: ent(o), owner: ent(o + 8) }));
  return n;
}

module.exports = { Replay, ITEMS, CHAMPS, DRAFT, CAMPS, STEPS, CONSUMABLES };
