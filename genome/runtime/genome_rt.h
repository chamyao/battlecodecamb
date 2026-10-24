// Genome runtime (docs/GENOME.md): the primitives genes call, the legal options of a turn and the fixed
// loop (list legal options, score each, do the best if its score > 0, look again).
//
// Written against cbs::Api, so the same code runs in the simulator (every engine call priced by the
// Api; genes' own operations charged through F(n)) and, later, in the bot over the real imports.
// Generated genes (genome/lang.py) include this header and derive from GenesBase.
#pragma once
#include <algorithm>
#include <array>
#include <cstring>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cstdint>
#include <memory>
#include <optional>
#include <vector>
#include "cbs/api.h"
#include "cbs/runner.h"

#ifndef GENOME_OP_FUEL
#define GENOME_OP_FUEL 1 // fuel per own operation: compiled arithmetic is nearly free in the bot (constants fold away); the cost is in the primitives' extra()
#endif
#ifndef GENOME_LOOP_FUEL
#define GENOME_LOOP_FUEL 8 // fuel per loop iteration beyond its operations (a 100-step range sum: ~9.5 per step in the bot)
#endif
// F(n): n own operations; FL(n) / FLU(n): one loop iteration (over a range or tiles / over units) with n
// operations; FX(n): n fuel of generated code the bot runs beyond its operations (a memo hit's copy)
#ifdef GENOME_BOT
#ifdef GENOME_PROF
#define F(n) (X.ops += (n))
#else
#define F(n) ((void)0)
#endif
#define FL(n) F(n)
#define FLU(n) F(n)
#define FX(n) ((void)0)
#else
#define F(n) X.charge_ops(n)
#define FL(n) X.charge_loop(n)
#define FLU(n) (X.charge_loop(n), X.extra(11))
#define FX(n) X.extra(n)
#endif

namespace genome
{
#ifdef GENOME_BOT
#define GENOME_TRACE_FILE stdout
#else
#define GENOME_TRACE_FILE stderr
#endif
#ifdef GENOME_PROF
// Inclusive fuel and calls per gene (real fuel in the bot), printed every GENOME_PROF_GENES rounds.
struct GeneStat
{
	const char* name = nullptr;
	long long calls = 0, fuel = 0, self = 0, kids = 0; // self: excluding the genes it calls (kids: how many calls)
};
inline GeneStat gene_stats[256];
struct GeneScope
{
	GeneStat& s;
	cbs::Api& api;
	std::int64_t t0, child = 0;
	void*& top; // the innermost open scope of this bot instance (simulator bots interleave on one thread)
	GeneScope* parent;
	GeneScope(GeneStat& s, cbs::Api& api, void*& top) : s(s), api(api), t0(api.fuel_remaining()), top(top), parent(static_cast<GeneScope*>(top))
	{
		++s.calls, top = this;
		if (turn_calls) ++turn_calls[&s - gene_stats];
	}
	static inline int* turn_calls = nullptr; // GENOME_TURN_CALLS (simulator): this bot instance's calls per gene this turn
	~GeneScope()
	{
		const std::int64_t f = t0 - api.fuel_remaining();
		s.fuel += f, s.self += f - child;
		if (parent) parent->child += f, ++parent->s.kids;
		top = parent;
	}
};
// (simulator: only team 0's champion 0 is profiled, as the bot's printed stats are champion 0's own)
#ifdef GENOME_BOT
#define GENE_PROF(i, nm) genome::gene_stats[i].name = nm; genome::GeneScope gene_scope_(genome::gene_stats[i], X.api, X.prof_top)
#else
#define GENE_PROF(i, nm) \
	genome::gene_stats[i].name = nm; \
	std::optional<genome::GeneScope> gene_scope_; \
	if (X.api.team() == 0 && X.api.champ() == 0) gene_scope_.emplace(genome::gene_stats[i], X.api, X.prof_top)
#endif
// The first distance-field searches: expansions and the fuel of the search call alone (printed with @@GENE).
struct FieldRec
{
	int expansions, stopped;
	long long fuel;
};
inline FieldRec field_recs[400];
// Guest primitives (wfield, path_*): fuel of each call with its own work counters (printed as @@PRIM).
struct PrimRec
{
	int prim;
	long long fuel, n[4];
};
inline PrimRec prim_recs[600];
inline int n_prim_recs = 0;
// First-turn checkpoints (fuel remaining): main start, map built, Api ready, genes made, then per phase
// of the first play_turn; printed on the second turn with the per-gene totals of turn 1 (@@T1).
inline std::int64_t t1_marks[16];
inline int n_t1_marks = 0;
inline void t1_mark(std::int64_t f) { if (n_t1_marks < 16) t1_marks[n_t1_marks++] = f; }
inline int n_field_recs = 0;
#define FIELD_PROF_BEGIN const std::int64_t fp0_ = api.fuel_remaining()
#define PRIM_PROF_BEGIN const std::int64_t pp0_ = api.fuel_remaining()
#define PRIM_PROF_END(id) \
	if (genome::n_prim_recs < 600 && api.team() == 0 && api.champ() == 0) \
	genome::prim_recs[genome::n_prim_recs++] = { id, pp0_ - api.fuel_remaining(), { last_work.tiles, last_work.pops, last_work.relax, last_work.scans } }
#define FIELD_PROF_END(n, st) \
	if (genome::n_field_recs < 400) genome::field_recs[genome::n_field_recs++] = { static_cast<int>(n), (st) ? 1 : 0, fp0_ - api.fuel_remaining() }
#else
#define FIELD_PROF_BEGIN ((void)0)
#define FIELD_PROF_END(n, st) ((void)0)
#define PRIM_PROF_BEGIN ((void)0)
#define PRIM_PROF_END(id) ((void)0)
#define GENE_PROF(i, nm) ((void)0)
#endif
using cbs::Api;
using cbs::Bitboard;
using cbs::Err;
using cbs::Vec2;

struct Tile
{
	int x = -1, y = -1;
	bool valid() const { return x >= 0; }
	bool operator==(const Tile&) const = default;
	Vec2 v() const { return { x, y }; }
};
struct Unit
{
	int kind = 0; // 0 none, 1 champion, 2 camp
	std::uint32_t h = 0;
	bool enemy = false;
	int type = -1; // ChampionType or CampType
	Tile pos;
	float health = 0, max_health = 0, strength = 0, focus = 0;
	int attack_range = 0, move_speed = 0;
	std::uint32_t state = 0;
	bool valid() const { return kind != 0; }
	bool operator==(const Unit& o) const { return kind == o.kind && h == o.h; }
};
using Units = std::vector<Unit>;
// Tile sets share an immutable board (1.6 KB) instead of copying it.
struct Tiles
{
	std::shared_ptr<const Bitboard> b;
};
// A distance field: row-major W x H in the simulator, the host's chunked layout in the bot.
struct Field
{
	std::shared_ptr<std::uint16_t[]> d;
	// box_field: only the 3 x 3 box around (bx, by) is stored (d[(dy + 1) * 3 + dx + 1]); reads elsewhere,
	// or above the centre's own distance, are unreachable
	int bx = -1, by = -1, br = 1; // dash_field: the 5 x 5 box (br = 2), d[(dy + br) * (2 br + 1) + dx + br]
	bool rm = false; // computed in guest code (wfield): padded row-major (W + 2) x (H + 2), bot and simulator
};
#ifdef GENOME_BOT
constexpr int kBotFieldWords = 13 * 13 * 64; // the engine's largest chunked map (100 x 100)
#endif
enum OptionKind
{
	PICK = 1, MOVE, ATTACK, CAST, WARD, BUY, RECALL, TRIBUTE, CANCEL, LOCK, BUY_LOCK
};
// Small on purpose: copying costs ~1 fuel per byte in the bot. The target unit is an entry of the
// pass's cached unit lists (Ctx::unit_of: usrc + ui); ukind/uh identify it across passes.
struct Option
{
	std::int8_t kind = 0;
	std::int8_t slot = -1, item = -1, champ = -1;
	std::int8_t ukind = 0;
	std::int8_t usrc = 0; // unit_of: 0 none, 1 enemies(), 2 camps(), 3 allies(), 4 me()
	std::int16_t ui = -1;
	std::int32_t count = 1; // BUY: units bought at once (the SDK's buy_item count)
	std::uint32_t uh = 0;
	Tile tile;
};
// The options of a pass, written in place (no per-option construction or copy).
struct OptionList
{
	static constexpr int kMax = 1024; // more than any turn can list (buys, 8 moves, units, 2 x 81 ground tiles, 25 wards, altars)
	// uninitialised storage (Option is an implicit-lifetime type; add() writes every field): constructing
	// 1,024 options up front costs ~35k fuel in the bot
	Option* v = static_cast<Option*>(std::malloc(sizeof(Option) * kMax));
	int n = 0;
	OptionList() = default;
	OptionList(const OptionList&) = delete;
	OptionList& operator=(const OptionList&) = delete;
	~OptionList() { std::free(v); }
	int size() const { return n; }
	const Option* begin() const { return v; }
	const Option* end() const { return v + n; }
	// a fresh option of `kind` (the other fields at their defaults)
	Option& add(int kind)
	{
		Option& o = v[n < kMax - 1 ? n++ : n];
		o.kind = static_cast<std::int8_t>(kind), o.slot = -1, o.item = -1, o.champ = -1, o.ukind = 0, o.usrc = 0, o.ui = -1, o.count = 1, o.uh = 0, o.tile = {};
		return o;
	}
};

inline double div(double a, double b) { return b == 0 ? 0.0 : a / b; }
inline double fmod_pos(double a, double b)
{
	if (b == 0) return 0.0;
	const double r = std::fmod(a, b);
	return r < 0 ? r + std::fabs(b) : r;
}

// The genome's optional consider(kind) entry gene, seen from the runtime (GenesBase implements it).
struct KindFilter
{
	virtual ~KindFilter() = default;
	virtual bool consider_kind(int kind) = 0;
	virtual bool has_consider() const = 0;
};

inline std::atomic<std::uint64_t>& pass_counter()
{
	static std::atomic<std::uint64_t> c{ 1 };
	return c;
}

// Per bot instance: the Api, plus observations cached within one pass of the loop.
class Ctx
{
public:
	explicit Ctx(Api& api) : api(api), m(api.map())
	{
		rng_ = 0x9E3779B97F4A7C15ull ^ (static_cast<std::uint64_t>(api.team()) << 32) ^ static_cast<std::uint64_t>(api.champ() + 7) * 0xBF58476D1CE4E5B9ull;
		rng_ |= 1;
	}
	Api& api;
	const cbs::Map& m;
	std::uint64_t pass_id = 0;

	long long ops = 0; // own operations counted by F(n) (profiling and calibration)
	void* prof_top = nullptr; // GENOME_PROF: the innermost open gene scope
#ifdef GENOME_PROF
	int turn_calls_buf[256] = {};
	long long turn_opts = 0;
#endif
	// Simulator only: the runtime's own work in the bot beyond what the Api already prices (fitted
	// from genome/examples/calib.genome profiled in cambc; docs in genome/FUEL.md). Compiled away in the bot.
	void extra(double fuel) const
	{
#ifndef GENOME_BOT
		if (fuel > 0) api.compute(static_cast<std::int64_t>(fuel));
#endif
	}
	double chunks() const { return ((m.W + 7) / 8) * ((m.H + 7) / 8); }
	[[gnu::always_inline]] void charge_ops(long n)
	{
		ops += n;
		api.compute(n * GENOME_OP_FUEL);
	}
	void charge_loop(long n)
	{
		ops += n;
		api.compute(n * GENOME_OP_FUEL + GENOME_LOOP_FUEL);
	}

	void new_pass()
	{
		pass_id = pass_counter()++;
		have_me_ = have_enemies_ = have_allies_ = have_camps_ = have_gems_ = have_gold_ = have_occ_ = have_items_ = have_cons_ = false;
	}

	// ---- self
	// me() as genes call it: the cached unit costs ~22 in the bot (measured per scored option)
	const Unit& me() { return extra(8), me_u(); }
	const Unit& me_u()
	{
		if (!have_me_)
		{
			self_ = static_cast<std::uint32_t>(api.my_champion());
			cbs::ChampionInfo ci{};
			api.champion(self_, &ci);
			me_ = from_champ(self_, ci);
			have_me_ = true;
			extra(50);
		}
		return me_;
	}
	std::uint32_t self() { return me_u(), self_; }
	bool alive() { return extra(10), me_u().state & cbs::state_bit::alive; }
	bool my_state(std::uint32_t bits) { return extra(21), api.champ() >= 0 && (me_u().state & bits); }
	bool channeling() { return my_state(cbs::state_bit::recalling | cbs::state_bit::submitting | cbs::state_bit::teleporting); }
	// uniform integer in [0, n) from this instance's generator (generic operation, no engine call)
	double rand(double n)
	{
		extra(18);
		rng_ ^= rng_ << 13, rng_ ^= rng_ >> 7, rng_ ^= rng_ << 17;
		const double k = std::floor(n);
		return k >= 1 ? static_cast<double>((rng_ >> 11) % static_cast<std::uint64_t>(std::min(k, 1e9))) : 0.0;
	}
	void set_priority(double p) { api.set_priority(static_cast<std::int32_t>(std::clamp(p, -1e6, 1e6))); }
	double gems()
	{
		if (!have_gems_) gems_ = unit_gems(me_u()), have_gems_ = true;
		return gems_;
	}
	double gold()
	{
		if (!have_gold_)
		{
			std::uint32_t g = 0;
			api.champion_gold(self(), &g);
			gold_ = g, have_gold_ = true;
			extra(32);
		}
		return gold_;
	}
	double round()
	{
		std::uint32_t r = 0;
		api.round_number(&r);
		extra(6);
		return r;
	}
	double fuel() { return static_cast<double>(api.fuel_remaining()); }
	bool can_shop()
	{
		std::int32_t v = 0;
		api.champion_can_shop(self(), false, &v);
		extra(16);
		return v;
	}
	double submitted(bool enemy)
	{
		std::uint32_t g = 0;
		api.submitted_gems(static_cast<std::uint32_t>(enemy ? 1 - api.team() : api.team()), &g);
		return g;
	}

	// ---- units
	const Units& enemies()
	{
		if (!have_enemies_) champs(true, enemies_), have_enemies_ = true;
		else extra(27); // a cached list still costs ~27 in the bot
		return enemies_;
	}
	const Units& allies()
	{
		if (!have_allies_) champs(false, allies_), have_allies_ = true;
		else extra(27);
		return allies_;
	}
	const Units& camps()
	{
		if (!have_camps_)
		{
			camps_.clear();
			std::vector<std::uint32_t> hs;
			api.visible_camps(hs);
			for (std::uint32_t h : hs)
			{
				cbs::CampRecord cr{};
				if (api.camp(h, &cr) != Err::success || cr.health <= 0) continue;
				Unit u;
				u.kind = 2, u.h = h, u.enemy = true, u.type = static_cast<int>(m.camps[h].type), u.pos = { cr.x, cr.y };
				u.health = cr.health, u.max_health = cr.max_health, u.strength = cr.strength, u.focus = cr.focus;
				u.attack_range = cbs::camp_design(m.camps[h].type).attack_range;
				camps_.push_back(u);
			}
			have_camps_ = true;
			extra(174 + 3.0 * chunks() + 253.0 * camps_.size());
		}
		else extra(27);
		return camps_;
	}
	double unit_gems(const Unit& u)
	{
		if (u.kind != 1) return 0;
		std::uint32_t g = 0;
		api.champion_gems(u.h, &g);
		extra(40);
		return g;
	}
	bool unit_state(const Unit& u, std::uint32_t bit) { return u.kind == 1 && (u.state & bit); }
	bool camp_awake(const Unit& u)
	{
		if (u.kind != 2) return false;
		std::uint32_t life = 0;
		extra(22);
		return api.camp_state(u.h, &life) == Err::success && life == static_cast<std::uint32_t>(cbs::CampLife::awake);
	}
	Tile camp_spawn(const Unit& u) const
	{
		extra(26);
		if (u.kind != 2 || u.h >= m.camps.size()) return {};
		return { m.camps[u.h].pos.x, m.camps[u.h].pos.y };
	}
	// static map: the camp spawning on a tile (its type / group), -1 if none
	int camp_index(Tile t)
	{
		extra(135);
		if (!in_bounds(t)) return -1;
		// the camp spawn tiles in a small open-addressing table keyed by tile index (a W x H table cost
		// ~30k+ to fill on a 100 x 100 map)
		if (camp_at_.empty())
		{
			std::size_t cap = 64;
			while (cap < 4 * m.camps.size()) cap *= 2;
			camp_at_.assign(cap, CampAt{ -1, -1 });
			for (std::size_t c = 0; c < m.camps.size(); ++c)
			{
				const int key = m.idx(m.camps[c].pos);
				std::size_t h = camp_hash(key, cap);
				while (camp_at_[h].tile >= 0) h = (h + 1) & (cap - 1);
				camp_at_[h] = { key, static_cast<int>(c) };
			}
			extra(500 + 85.0 * m.camps.size());
		}
		const int key = m.idx(t.v());
		const std::size_t cap = camp_at_.size();
		for (std::size_t h = camp_hash(key, cap);; h = (h + 1) & (cap - 1))
			if (camp_at_[h].tile == key || camp_at_[h].tile < 0) return camp_at_[h].tile == key ? camp_at_[h].camp : -1;
	}
	double spawn_type(Tile t)
	{
		const int c = camp_index(t);
		return c < 0 ? -1 : static_cast<int>(m.camps[c].type);
	}
	double spawn_group(Tile t)
	{
		const int c = camp_index(t);
		return c < 0 ? -1 : m.camps[c].group;
	}
	static bool camp_type_ok(double k) { return k >= 0 && k <= static_cast<double>(cbs::CampType::golem); }
	double camp_base(double k, int which)
	{
		if (!camp_type_ok(k)) return 0;
		const auto& d = cbs::camp_design(static_cast<cbs::CampType>(static_cast<int>(k)));
		extra(12);
		return which == 0 ? d.base_health : which == 1 ? d.base_strength : d.base_focus;
	}
	double camp_group(const Unit& u) { return u.kind == 2 ? m.camps[u.h].group : -1; }
	bool group_ok(double g) const { return g >= 0 && g < static_cast<double>(m.groups.size()); }
	double group_gems(double g) { return group_ok(g) ? m.groups[static_cast<int>(g)].gems : 0; }
	double group_gold(double g) { return group_ok(g) ? m.groups[static_cast<int>(g)].gold : 0; }
	bool group_in_state(double g, cbs::GroupState want)
	{
		if (!group_ok(g)) return false;
		std::uint32_t s = 0;
		api.camp_group_state(static_cast<std::uint32_t>(g), &s);
		extra(32);
		return s == static_cast<std::uint32_t>(want);
	}
	bool group_respawning(double g) { return group_in_state(g, cbs::GroupState::respawning); }
	bool group_reward(double g) { return group_in_state(g, cbs::GroupState::reward); }
	Tiles group_tiles(double g)
	{
		if (!group_ok(g)) return { std::make_shared<Bitboard>() };
		// static: built once per group (each host bit set costs ~170 fuel in the bot)
		if (group_tiles_.empty()) group_tiles_.resize(m.groups.size());
		extra(104); // as a static set read (~74) and the group lookup
		auto& slot = group_tiles_[static_cast<int>(g)];
		if (!slot)
		{
			auto b = std::make_shared<Bitboard>();
			for (int c : m.groups[static_cast<int>(g)].camps) b->set(m.camps[c].pos);
			slot = b;
		}
		return { slot };
	}
	double num_groups() const { return static_cast<double>(m.groups.size()); }
	bool visible(Tile t)
	{
		if (!in_bounds(t)) return false;
		std::int32_t v = 0;
		api.is_visible(t.v(), &v);
		extra(100);
		return v;
	}

	// ---- static map (built once per instance)
	// a static set costs ~74 per read in the bot (the shared board's handle copied out; score variants)
	Tiles altars() { return extra(74), stat(altars_, [&](Bitboard& b) { b = m.altars; }); }
	Tiles walls() { return extra(74), stat(walls_, [&](Bitboard& b) { b = m.walls; }); }
	Tiles bushes() { return extra(74), stat(bushes_, [&](Bitboard& b) { b = m.bushes; }); }
	Tiles holes() { return extra(74), stat(holes_, [&](Bitboard& b) { b = m.holes; }); }
	Tiles spawn(bool enemy)
	{
		extra(74);
		return stat(enemy ? espawn_ : myspawn_, [&](Bitboard& b) { b = m.spawn_mask[enemy ? 1 - api.team() : api.team()]; });
	}
	Tiles camp_spawns()
	{
		extra(74);
		return stat(campsp_, [&](Bitboard& b) {
			for (const auto& c : m.camps) b.set(c.pos);
		});
	}
	// spawn tiles of the camps of one type (static map)
	Tiles type_spawns(double k)
	{
		extra(117);
		if (!camp_type_ok(k)) return { std::make_shared<Bitboard>() };
		const int i = static_cast<int>(k);
		return stat(type_sp_[i], [&](Bitboard& b) {
			for (const auto& c : m.camps)
				if (static_cast<int>(c.type) == i) b.set(c.pos);
		});
	}
	Tiles locked_altars()
	{
		auto b = std::make_shared<Bitboard>();
		cbs::AltarLockRecord rec[16];
		std::uint32_t n = 0;
		api.altar_locks(rec, 16, &n);
		for (std::uint32_t i = 0; i < n && i < 16; ++i)
			if (static_cast<int>(rec[i].team) != api.team()) b->set(rec[i].x, rec[i].y);
		extra(275);
		return { b };
	}
	// ---- live occupancy and vision as the SDK reports them (one engine call each)
	// (each ~160 + 2.1 x chunks in the bot, beyond the Api's price of the call: 62 vision, 14 + chunks occupancy)
	Tiles vision() { return extra(100 + 2.1 * chunks()), sdk_mask([&](Bitboard& b) { api.vision(b); }); }
	Tiles ally_tiles() { return extra(148 + 1.1 * chunks()), sdk_mask([&](Bitboard& b) { api.ally_occupancy(b); }); }
	Tiles enemy_tiles() { return extra(148 + 1.1 * chunks()), sdk_mask([&](Bitboard& b) { api.enemy_occupancy(b); }); }
	Tiles camp_tiles() { return extra(148 + 1.1 * chunks()), sdk_mask([&](Bitboard& b) { api.camp_occupancy(b, 0); }); }
	double width() const { return m.W; }
	double height() const { return m.H; }

	// ---- geometry
	bool in_bounds(Tile t) const { return t.valid() && m.in_bounds(t.v()); }
	double dist(Tile a, Tile b) const { return extra(30), dist_raw(a, b); } // ~30 in the bot (measured per scored option)
	double dist_raw(Tile a, Tile b) const { return a.valid() && b.valid() ? cbs::chebyshev(a.v(), b.v()) : 1e9; }
	Tiles near(Tile t, double r)
	{
		auto b = std::make_shared<Bitboard>();
		if (in_bounds(t)) cbs::draw_chebyshev(*b, m.W, m.H, t.v(), static_cast<float>(std::max(0.0, r)));
		extra(122 + 1.03 * chunks());
		return { b };
	}
	Tile nearest(const Tiles& s, Tile t)
	{
		Tile best;
		int bd = 1 << 30;
		if (!s.b || !t.valid()) return best;
		// ties broken by (y, x), so the iteration order does not matter (the bot's cheap order is not row-major)
		s.b->for_each_unordered(m.H, [&](int x, int y) {
			const int d = cbs::chebyshev({ x, y }, t.v());
			if (d < bd || (d == bd && (y < best.y || (y == best.y && x < best.x)))) bd = d, best = { x, y };
		});
		extra(46 + 52.0 * s.b->count(m.H));
		return best;
	}
	double size(const Tiles& s)
	{
		extra(6 + 1.0 * chunks());
		return s.b ? s.b->count(m.H) : 0;
	}
	bool contains(const Tiles& s, Tile t) { return extra(66), s.b && in_bounds(t) && s.b->test(t.v()); }
	Tiles tiles_or(const Tiles& a, const Tiles& b) { return extra(76 + 3.1 * chunks()), combine(a, b, 0); }
	Tiles tiles_and(const Tiles& a, const Tiles& b) { return extra(76 + 3.1 * chunks()), combine(a, b, 1); }
	Tiles tiles_minus(const Tiles& a, const Tiles& b) { return extra(77 + 4.0 * chunks()), combine(a, b, 2); }
	// Row-major, as the simulator iterates. In the bot the host lists tiles chunk row by chunk row
	// ((chunk row, chunk col, y, x)); a stable counting sort on y alone restores row-major order in
	// linear time (the host bitboard's own for_each uses an insertion sort, quadratic per chunk row).
	std::vector<Tile> tiles_of(const Tiles& s) const
	{
		std::vector<Tile> out;
		if (!s.b) return out;
#ifdef GENOME_BOT
		// one host call lists the tiles; then a stable counting sort on y (no intermediate vector)
		static cbs::hostbb::Pos buf[cbs::kMaxDim * cbs::kMaxDim];
		std::uint32_t n = 0;
		cambc::detail::sdk_Bitboard_GetSetBits(s.b->w, buf, cbs::kMaxDim * cbs::kMaxDim, &n);
		out.resize(n);
		if (n <= 32)
		{
			// a small set: insertion sort by (y, x) (the counting sort's pass over the rows costs ~2k)
			for (std::uint32_t i = 0; i < n; ++i)
			{
				const Tile t{ buf[i].x, buf[i].y };
				std::uint32_t j = i;
				for (; j > 0 && (out[j - 1].y > t.y || (out[j - 1].y == t.y && out[j - 1].x > t.x)); --j) out[j] = out[j - 1];
				out[j] = t;
			}
			return out;
		}
		int count[cbs::kMaxDim + 1] = {};
		for (std::uint32_t i = 0; i < n; ++i) ++count[buf[i].y + 1];
		for (int y = 0; y < m.H; ++y) count[y + 1] += count[y];
		for (std::uint32_t i = 0; i < n; ++i) out[count[buf[i].y]++] = Tile{ buf[i].x, buf[i].y };
#else
		s.b->for_each(m.H, [&](int x, int y) { out.push_back({ x, y }); });
		// bot: up to 32 tiles an insertion sort, else a counting sort over the rows
		extra(out.size() <= 32 ? 80 + 1.0 * chunks() + 90.0 * out.size() : 2026 + 1.0 * chunks() + 81.0 * out.size());
#endif
		return out;
	}
	// Walking distance field to `goals` (walls, holes, altars and the enemy spawn block; goal tiles
	// themselves are allowed). One engine distance-field call, priced by the Api.
	Field field(const Tiles& goals)
	{
		if (!goals.b || !goals.b->any(m.H)) return empty_field();
		Bitboard blocked = m.walls;
		blocked |= m.holes;
		blocked |= m.altars;
		blocked |= m.spawn_mask[1 - api.team()];
		blocked.andnot(*goals.b);
		extra(527 + 8.1 * chunks()); // the wrapper in the bot: blocked set (5 board ops), buffers
		return run_field(blocked, *goals.b, nullptr);
	}
	// Walking distance field to `goals` over every tile not in `walls` (goal tiles always allowed). The
	// search stops after the distance layer by which every reachable tile of `stop` has been reached
	// (the host's ComputeTo; empty `stop`: the whole map); tiles beyond it read as unreachable.
	Field field_avoid(const Tiles& goals, const Tiles& walls, const Tiles& stop)
	{
		if (!goals.b || !goals.b->any(m.H)) return empty_field();
		Bitboard blocked;
		if (walls.b) blocked = *walls.b;
		blocked.andnot(*goals.b);
		const bool stops = stop.b && stop.b->any(m.H);
		extra(528 + 7.1 * chunks()); // the wrapper in the bot
		return run_field(blocked, *goals.b, stops ? stop.b.get() : nullptr);
	}
	// A full-map field the genome can read anywhere. Simulator: the Api's search, row-major. Bot: the
	// host search straight into a buffer we own, read in the host's chunked layout. (The bot's
	// Api::distance_field fills only the champion's box and the dests, for the interpreter's needs, and
	// filling a 20 KB array costs ~1 fuel per byte; the host initialises every entry itself.)
	Field run_field(const Bitboard& blocked, const Bitboard& roots, const Bitboard* dests)
	{
#ifdef GENOME_BOT
		std::shared_ptr<std::uint16_t[]> d(new std::uint16_t[kBotFieldWords]); // uninitialised: the host writes all of it
		Bitboard visited;
		std::uint16_t c = 0;
		FIELD_PROF_BEGIN;
		if (dests) cambc::detail::sdk_DistanceField_ComputeToWithExpansionCount(blocked.w, roots.w, dests->w, visited.w, d.get(), cbs::kUnreachable, &c);
		else cambc::detail::sdk_DistanceField_ComputeWithExpansionCount(blocked.w, roots.w, visited.w, d.get(), cbs::kUnreachable, &c);
		FIELD_PROF_END(c, dests != nullptr);
		return { d };
#else
		std::shared_ptr<std::uint16_t[]> d(new std::uint16_t[static_cast<std::size_t>(m.W) * m.H]); // cbs::distance_field writes every entry
		Bitboard visited;
		FIELD_PROF_BEGIN;
		// the bot runs the host search directly (no memo), so it is priced here on its own expansions
		const int n = cbs::distance_field(blocked, roots, dests, m.W, m.H, cbs::kUnreachable, d.get(), visited, true);
		extra(field_price(n, dests != nullptr));
		FIELD_PROF_END(n, dests != nullptr);
		return { d };
#endif
	}
	Field empty_field() { return {}; }

	// ---- guest pathfinding: plain C++ run as wasm in the bot, the same code in the simulator. Each counts
	// its own work; the simulator charges the bot's measured fuel per unit of it (genome/FUEL.md).
	struct GuestWork
	{
		long long tiles = 0, pops = 0, relax = 0, scans = 0;
	};
	GuestWork last_work;
	std::unique_ptr<std::int32_t[]> gnext_, gprev_, gaux_;
	std::unique_ptr<std::uint32_t[]> gstamp_;
	std::unique_ptr<std::uint16_t[]> gcost_;
	std::uint32_t gen_ = 0;
	void guest_scratch()
	{
		if (gnext_) return;
		const std::size_t n = static_cast<std::size_t>(m.W) * m.H;
		extra(5.0 * n); // once per instance: the scratch arrays (the stamps zeroed)
		gnext_.reset(new std::int32_t[n]), gprev_.reset(new std::int32_t[n]), gaux_.reset(new std::int32_t[n]);
		gcost_.reset(new std::uint16_t[n]), gstamp_.reset(new std::uint32_t[n]());
	}
	// Weighted walking field to `goals`: stepping onto a tile costs 1, or 1 + k on a `slow` tile (k
	// clamped to 0..8); `walls` cannot be entered (goal tiles can). Dijkstra over a bucket queue (Dial:
	// 10 circular buckets of doubly linked tiles, no heap). Distances above 65534 read unreachable.
	Field wfield(const Tiles& goals, const Tiles& walls, const Tiles& slow, double k)
	{
		PRIM_PROF_BEGIN;
		Field f = wfield_(goals, walls, slow, k);
		PRIM_PROF_END(1);
		return f;
	}
	Field wfield_(const Tiles& goals, const Tiles& walls, const Tiles& slow, double k)
	{
		last_work = {};
		if (!goals.b) return empty_field();
		const int W = m.W, H = m.H, P = W + 2; // padded rows: a border of blocked tiles, no bounds tests
		const int NP = P * (H + 2);
		const int kk = static_cast<int>(std::clamp(std::floor(k), 0.0, 8.0));
		if (!wf_cost_) wf_cost_.reset(new std::uint8_t[NP]), wf_next_.reset(new std::int32_t[NP]), wf_prev_.reset(new std::int32_t[NP]);
		std::uint8_t* cost = wf_cost_.get();
		std::int32_t *nx = wf_next_.get(), *pv = wf_prev_.get();
		std::shared_ptr<std::uint16_t[]> dd(new std::uint16_t[NP]);
		std::uint16_t* d = dd.get();
		std::fill(d, d + NP, cbs::kUnreachable);
		std::fill(cost, cost + P, 0), std::fill(cost + NP - P, cost + NP, 0);
		const Bitboard* wb = walls.b.get();
		const Bitboard* sb = slow.b.get();
		std::int32_t head[10];
		for (int& h : head) h = -1;
		long long queued = 0;
		GuestWork wk;
		// the cost of stepping onto each tile (0: blocked), and the goals at distance 0
		for (int y = 0; y < H; ++y)
		{
			std::uint8_t* row = cost + (y + 1) * P;
			row[0] = row[P - 1] = 0;
			for (int x = 0; x < W; ++x)
			{
				const int v = (y + 1) * P + x + 1;
				row[x + 1] = wb && wb->test(x, y) ? 0 : static_cast<std::uint8_t>(1 + (sb && sb->test(x, y) ? kk : 0));
				if (goals.b->test(x, y))
				{
					d[v] = 0, nx[v] = head[0], pv[v] = -1;
					if (head[0] >= 0) pv[head[0]] = v;
					head[0] = v, ++queued;
				}
			}
		}
		wk.tiles = static_cast<long long>(W) * H;
		const int off[8] = { -P - 1, -P, -P + 1, -1, 1, P - 1, P, P + 1 };
		for (int cur = 0, empty = 0; queued > 0;)
		{
			const int b = cur % 10;
			int v = head[b];
			if (v < 0)
			{
				++cur, ++wk.scans;
				if (++empty > 10) break;
				continue;
			}
			empty = 0;
			head[b] = nx[v];
			if (nx[v] >= 0) pv[nx[v]] = -1;
			--queued, ++wk.pops;
			const int dv = d[v];
			for (int i = 0; i < 8; ++i)
			{
				const int u = v + off[i];
				const int c = cost[u];
				if (!c) continue;
				++wk.relax;
				const int nd = dv + c;
				if (nd >= d[u] || nd > 65534) continue;
				if (d[u] != cbs::kUnreachable)
				{
					const int ob = d[u] % 10;
					if (pv[u] >= 0) nx[pv[u]] = nx[u];
					else head[ob] = nx[u];
					if (nx[u] >= 0) pv[nx[u]] = pv[u];
				}
				else ++queued;
				const int nb = nd % 10;
				d[u] = static_cast<std::uint16_t>(nd), nx[u] = head[nb], pv[u] = -1;
				if (head[nb] >= 0) pv[head[nb]] = u;
				head[nb] = u;
			}
		}
		last_work = wk;
		extra(WF_BASE + WF_TILE * wk.tiles + WF_POP * wk.pops + WF_RELAX * wk.relax + WF_SCAN * wk.scans);
		Field f{ dd };
		f.rm = true;
		return f;
	}
	// Tiles strictly nearer (walking, 8 neighbours) to `mine` than to `theirs`, over tiles not in `walls`
	// (sources allowed): two host distance fields and a compare loop in our code. (A two-colour search in
	// our code would cost about a full wfield, ~4.5M fuel on 100 x 100.)
	Tiles territory(const Tiles& mine, const Tiles& theirs, const Tiles& walls)
	{
		PRIM_PROF_BEGIN;
		last_work = {};
		auto out = std::make_shared<Bitboard>();
		if (!mine.b || !mine.b->any(m.H)) return { out };
		Bitboard b1, b2;
		if (walls.b) b1 = *walls.b, b2 = *walls.b;
		b1.andnot(*mine.b);
		const Field f1 = run_field(b1, *mine.b, nullptr);
		Field f2;
		const bool rival = theirs.b && theirs.b->any(m.H);
		if (rival) b2.andnot(*theirs.b), f2 = run_field(b2, *theirs.b, nullptr);
		const std::uint16_t* d1 = f1.d.get();
		const std::uint16_t* d2 = rival ? f2.d.get() : nullptr;
#ifdef GENOME_BOT
		// the host field and the bitboard share the chunk order inside a chunk (entry (y % 8) * 8 + x % 8 is
		// bit (y % 8) * 8 + x % 8): chunk (cy, cx) is field block cy * width + cx, bitboard word cy * stride + cx
		const int cw = static_cast<int>(cbs::hostbb::md.chunked_width), chh = static_cast<int>(cbs::hostbb::md.chunked_height);
		for (int cy = 0; cy < chh; ++cy)
			for (int cx = 0; cx < cw; ++cx)
			{
				std::uint64_t bits = 0;
				const std::uint16_t* a = d1 + (cy * cw + cx) * 64;
				if (d2)
				{
					const std::uint16_t* b = d2 + (cy * cw + cx) * 64;
					for (int i = 0; i < 64; ++i) bits |= static_cast<std::uint64_t>(a[i] < b[i]) << i;
				}
				else
					for (int i = 0; i < 64; ++i) bits |= static_cast<std::uint64_t>(a[i] != cbs::kUnreachable) << i;
				out->w[cy * cbs::hostbb::stride + cx] = bits;
			}
#else
		for (int y = 0; y < m.H; ++y)
			for (int x = 0; x < m.W; ++x)
			{
				const double a = field_at_raw(f1, { x, y }), b = d2 ? field_at_raw(f2, { x, y }) : 1e9;
				if (a < b) out->set(x, y);
			}
#endif
		// tiles: field entries compared (chunks x 64), pops: 1 with a rival set (two fields, a compare per entry)
		last_work.tiles = static_cast<long long>(((m.W + 7) / 8) * ((m.H + 7) / 8)) * 64, last_work.pops = rival ? 1 : 0;
		extra(rival ? TR_BASE2 + TR_ENTRY2 * last_work.tiles : TR_BASE1 + TR_ENTRY1 * last_work.tiles);
		PRIM_PROF_END(4);
		return { out };
	}
	static constexpr double TR_BASE1 = 531, TR_ENTRY1 = 17.15, TR_BASE2 = 641, TR_ENTRY2 = 22.31; // fitted on cambc probes (FUEL.md)
	std::unique_ptr<std::uint8_t[]> wf_cost_;
	std::unique_ptr<std::int32_t[]> wf_next_, wf_prev_;
	// fitted on cambc probes (genome/FUEL.md)
	static constexpr double WF_BASE = 20194, WF_TILE = 85.7, WF_POP = 414.7, WF_RELAX = 0, WF_SCAN = 32.3;

	// A* from `from` to `to` (8 neighbours, unit steps, Chebyshev heuristic), over tiles not in `walls`
	// (`to` is always allowed), expanding at most `budget` tiles. The open set is a bucket queue on
	// (f, h): f never drops and rises by at most 2 per step, so 4 levels of f, each with one doubly
	// linked list per h; the lowest (f, h) goes first (ties: the tile reached last). A parent changes
	// only on a strictly shorter path, neighbours scanned row-major. Returns the length (-1 if not found
	// within the budget) and the first step.
	int astar(Tile from, Tile to, const Tiles& walls, double budget, Tile* step)
	{
		last_work = {};
		if (step) *step = {};
		if (!in_bounds(from) || !in_bounds(to)) return -1;
		if (from == to) return 0;
		const int W = m.W, H = m.H, N = W * H, HM = std::max(W, H) + 1;
		guest_scratch();
		if (!as_head_) as_head_.reset(new std::int32_t[4 * HM]);
		const long long cap = static_cast<long long>(std::clamp(std::floor(budget), 0.0, static_cast<double>(N)));
		// stamps per search: 2 gen = open (g, par, list links valid), 2 gen + 1 = expanded; no per-call clearing
		if (++gen_ >= 0x7FFFFFFFu) std::fill(gstamp_.get(), gstamp_.get() + N, 0u), gen_ = 1;
		std::uint32_t* st = gstamp_.get();
		const std::uint32_t OPEN = 2 * gen_, DONE = 2 * gen_ + 1;
		std::uint16_t* g = gcost_.get();
		std::int32_t *par = gaux_.get(), *nx = gnext_.get(), *pv = gprev_.get(), *head = as_head_.get();
		std::fill(head, head + 4 * HM, -1);
		int minh[4] = { HM, HM, HM, HM }; // per f level, a lower bound of the non-empty h lists
		auto hcost = [&](int x, int y) { return std::max(std::abs(x - to.x), std::abs(y - to.y)); };
		auto link = [&](int v, int f, int h) {
			const int bi = (f & 3) * HM + h;
			nx[v] = head[bi], pv[v] = -1;
			if (head[bi] >= 0) pv[head[bi]] = v;
			head[bi] = v;
			if (h < minh[f & 3]) minh[f & 3] = h;
		};
		auto unlink = [&](int v, int f, int h) {
			const int bi = (f & 3) * HM + h;
			if (pv[v] >= 0) nx[pv[v]] = nx[v];
			else head[bi] = nx[v];
			if (nx[v] >= 0) pv[nx[v]] = pv[v];
		};
		const int s = from.y * W + from.x, t = to.y * W + to.x;
		const int h0 = hcost(from.x, from.y);
		st[s] = OPEN, g[s] = 0, par[s] = -1;
		link(s, h0, h0);
		long long open = 1;
		GuestWork wk;
		const Bitboard* wb = walls.b.get();
		int found = -1;
		for (int f = h0, idle = 0; open > 0 && wk.pops < cap;)
		{
			const int L = f & 3;
			int h = minh[L];
			while (h < HM && head[L * HM + h] < 0) ++h, ++wk.scans;
			if (h >= HM)
			{
				minh[L] = HM, ++f, ++wk.scans;
				if (++idle > 4) break;
				continue;
			}
			idle = 0, minh[L] = h;
			const int v = head[L * HM + h];
			unlink(v, f, h), --open;
			st[v] = DONE, ++wk.pops;
			if (v == t)
			{
				found = g[v];
				break;
			}
			const int vx = v % W, vy = v / W, ng = g[v] + 1;
			for (int y = std::max(0, vy - 1); y <= std::min(H - 1, vy + 1); ++y)
				for (int x = std::max(0, vx - 1); x <= std::min(W - 1, vx + 1); ++x)
				{
					const int u = y * W + x;
					if (u == v || st[u] == DONE || (u != t && wb && wb->test(x, y))) continue;
					++wk.relax;
					const int hu = hcost(x, y);
					if (st[u] == OPEN)
					{
						if (ng >= g[u]) continue;
						unlink(u, g[u] + hu, hu);
					}
					else ++open;
					st[u] = OPEN, g[u] = static_cast<std::uint16_t>(ng), par[u] = v;
					link(u, ng + hu, hu);
				}
		}
		if (found > 0 && step)
		{
			int v = t;
			while (par[v] != s) v = par[v], ++wk.tiles; // tiles: steps walked back along the path
			*step = { v % W, v / W };
		}
		last_work = wk;
#ifdef GENOME_TRACE_ASTAR
		{
			std::uint64_t hw = 0;
			if (wb)
				for (int y = 0; y < H; ++y)
					for (int x = 0; x < W; ++x)
						if (wb->test(x, y)) hw = hw * 1000003u + static_cast<std::uint64_t>(y * W + x + 1);
			std::fprintf(GENOME_TRACE_FILE, "@@AS r%d c%d from %d,%d to %d,%d walls %llx pops %lld relax %lld found %d step %d,%d\n", static_cast<int>(round()), api.champ(), from.x, from.y,
						 to.x, to.y, static_cast<unsigned long long>(hw), wk.pops, wk.relax, found, step ? step->x : -9, step ? step->y : -9);
		}
#endif
		extra(AS_BASE + AS_POP * wk.pops + AS_RELAX * wk.relax + AS_SCAN * wk.scans + AS_BACK * wk.tiles);
		return found;
	}
	std::unique_ptr<std::int32_t[]> as_head_;
	static constexpr double AS_BASE = 1427, AS_POP = 380.9, AS_RELAX = 134.1, AS_SCAN = 27.3, AS_BACK = 15.2;
	Tile path_step(Tile from, Tile to, const Tiles& walls, double budget)
	{
		PRIM_PROF_BEGIN;
		Tile s;
		astar(from, to, walls, budget, &s);
		PRIM_PROF_END(2);
		return s;
	}
	double path_len(Tile from, Tile to, const Tiles& walls, double budget)
	{
		PRIM_PROF_BEGIN;
		const int n = astar(from, to, walls, budget, nullptr);
		PRIM_PROF_END(3);
		return n < 0 ? 1e9 : n;
	}
	// Walking field to `goals` over tiles not in `walls` (goal tiles always allowed), through the
	// memoised distance field the interpreter's move_towards uses (dests = my tile: the bot's memo
	// answers it across turns while the goals stay and the walls do not affect my box). Readable only
	// in my 3 x 3 box and up to my own distance (the part the bot fills and the simulator's search
	// stopped at my tile reaches); elsewhere unreachable, identically in the bot and the simulator.
	// Walking field to one `goal` tile over tiles not in `walls` (the goal always allowed), through the
	// memoised distance field the interpreter's dash_towards uses (root = the goal, dests = my 5 x 5 box
	// without the goal). The search stops at the first layer reaching the box, so only the box tiles at
	// that distance (the box's nearest to the goal) read their distance; every other tile is unreachable,
	// identically in the bot and the simulator. For choosing a dash landing.
	Field dash_field(Tile goal, const Tiles& walls)
	{
		const Unit& u = me_u();
		const Tile c = u.pos;
		if (!in_bounds(goal) || !in_bounds(c) || !(u.state & cbs::state_bit::alive) || goal == c) return empty_field();
		Bitboard blocked, root, box, visited;
		if (walls.b) blocked = *walls.b;
		blocked.reset(goal.v());
		root.set(goal.v());
		cbs::draw_chebyshev(box, m.W, m.H, c.v(), 2.0f);
		box.reset(goal.v());
		if (!box_buf_) box_buf_.reset(new std::uint16_t[static_cast<std::size_t>(m.W) * m.H]);
		std::uint16_t* buf = box_buf_.get();
		api.distance_field(blocked, root, &box, cbs::kUnreachable, buf, visited);
		extra(DASH_FIELD_BASE + DASH_FIELD_CHUNK * chunks());
		std::shared_ptr<std::uint16_t[]> d(new std::uint16_t[25]);
		std::uint16_t lo = cbs::kUnreachable;
		for (int dy = -2; dy <= 2; ++dy)
			for (int dx = -2; dx <= 2; ++dx)
			{
				const Vec2 q{ c.x + dx, c.y + dy };
				const bool in = m.in_bounds(q) && !blocked.test(q) && !(q.x == goal.x && q.y == goal.y);
				const std::uint16_t v = in ? buf[m.idx(q)] : cbs::kUnreachable;
				d[(dy + 2) * 5 + dx + 2] = v;
				if (v < lo) lo = v;
			}
		for (int i = 0; i < 25; ++i)
			if (d[i] != lo) d[i] = cbs::kUnreachable;
		Field f{ d };
		f.bx = c.x, f.by = c.y, f.br = 2;
		return f;
	}
	static constexpr double DASH_FIELD_BASE = 1206, DASH_FIELD_CHUNK = 8.5; // the wrapper beyond the Api's memo price (cambc probes)
	Field box_field(const Tiles& goals, const Tiles& walls)
	{
		const Unit& u = me_u();
		const Tile c = u.pos;
		if (!goals.b || !in_bounds(c) || !(u.state & cbs::state_bit::alive) || !goals.b->any(m.H)) return empty_field();
		Bitboard blocked;
		if (walls.b) blocked = *walls.b;
		blocked.andnot(*goals.b);
		Bitboard dest, visited;
		dest.set(c.v());
		// uninitialised: the Api writes every entry that is read (the bot: the box and the dest)
		if (!box_buf_) box_buf_.reset(new std::uint16_t[static_cast<std::size_t>(m.W) * m.H]);
		std::uint16_t* buf = box_buf_.get();
		api.distance_field(blocked, *goals.b, &dest, cbs::kUnreachable, buf, visited);
		extra(300 + 6.5 * chunks()); // the wrapper in the bot beyond the Api's memo price (probes: near and far goals, 2 maps)
		std::shared_ptr<std::uint16_t[]> d(new std::uint16_t[9]);
		const std::uint16_t mine = buf[m.idx(c.v())];
		for (int dy = -1; dy <= 1; ++dy)
			for (int dx = -1; dx <= 1; ++dx)
			{
				const Vec2 q{ c.x + dx, c.y + dy };
				std::uint16_t v = cbs::kUnreachable;
				if (mine != cbs::kUnreachable && m.in_bounds(q) && !blocked.test(q))
				{
					v = buf[m.idx(q)];
					if (v > mine) v = cbs::kUnreachable;
				}
				d[(dy + 1) * 3 + dx + 1] = v;
			}
		Field f{ d };
		f.bx = c.x, f.by = c.y;
		return f;
	}
	std::unique_ptr<std::uint16_t[]> box_buf_;
	// the host search, exact (9 + 16 x chunks + expansions x chunks; + 2 with a stop set), plus the wrapper's own work
	double field_price(int expansions, bool stopped) const { return 9 + (stopped ? 2 : 0) + (16.0 + expansions) * chunks(); }
	// Nearest tile of `cand` from `from` by walking over tiles not in `walls` (ties: row-major); invalid if none.
	Tile walk_nearest(const Tiles& cand, Tile from, const Tiles& walls)
	{
		if (!cand.b || !in_bounds(from) || !cand.b->any(m.H)) return {};
		Bitboard w;
		if (walls.b) w = *walls.b;
		Vec2 out{ -1, -1 };
		if (!api.nearest_by_walk(w, from.v(), *cand.b, out)) return {};
		return { out.x, out.y };
	}
	double field_at(const Field& f, Tile t) const
	{
		extra(70); // the read costs ~70 in the bot (bounds, chunked index; measured per scored option)
		return field_at_raw(f, t);
	}
	double field_at_raw(const Field& f, Tile t) const
	{
		if (!f.d || !in_bounds(t)) return 1e9;
		if (f.rm)
		{
			const std::uint16_t v = f.d[(t.y + 1) * (m.W + 2) + t.x + 1]; // padded row-major (wfield)
			return v == cbs::kUnreachable ? 1e9 : v;
		}
		if (f.bx >= 0)
		{
			const int dx = t.x - f.bx, dy = t.y - f.by, r = f.br;
			if (dx < -r || dx > r || dy < -r || dy > r) return 1e9;
			const std::uint16_t v = f.d[(dy + r) * (2 * r + 1) + dx + r];
			return v == cbs::kUnreachable ? 1e9 : v;
		}
#ifdef GENOME_BOT
		const int i = ((t.y >> 3) * static_cast<int>(cbs::hostbb::md.chunked_width) + (t.x >> 3)) * 64 + (t.y & 7) * 8 + (t.x & 7);
		const std::uint16_t v = f.d[i];
#else
		const std::uint16_t v = f.d[m.idx(t.v())];
#endif
		return v == cbs::kUnreachable ? 1e9 : v;
	}

	// ---- fights: exact single-hit damage from the game's formulas and the units' host data (items' emblem
	// passives, shields), as the engine applies it (float, in its order). Per pass, per champion: one items
	// read and one buffs read.
	struct FightData
	{
		std::uint64_t pass = 0;
		std::uint32_t passives = 0;
		float shield = 0;
	};
	FightData fight_[32];
	const FightData& fight_data(const Unit& u)
	{
		static const FightData none{};
		if (u.kind != 1 || u.h >= 32) return none;
		FightData& f = fight_[u.h];
		if (f.pass != pass_id)
		{
			f = FightData{};
			f.pass = pass_id;
			std::uint32_t items[cbs::kNumItems] = {};
			if (api.champion_items(u.h, items) == Err::success)
				for (int i = 0; i < cbs::kNumItems; ++i)
					if (items[i] && cbs::item_design(i).passive != cbs::ItemPassive::none) f.passives |= 1u << static_cast<int>(cbs::item_design(i).passive);
			cbs::BuffRecord b[8];
			std::uint32_t n = 0;
			if (api.champion_buff_data(u.h, b, 8, &n) == Err::success)
				for (std::uint32_t i = 0; i < n && i < 8; ++i)
					if (b[i].type == 0) f.shield += b[i].value; // BuffType::shield
			extra(FD_FUEL);
			++fd_fetches_;
		}
		return f;
	}
	long long fd_fetches_ = 0;
	static bool has_ip(const FightData& f, cbs::ItemPassive p) { return f.passives >> static_cast<int>(p) & 1; }
	// Game::apply_outgoing: the missing-health passive, then the monster emblem against camps
	float outgoing(const Unit& a, float amount, bool vs_camp)
	{
		if (a.kind != 1 || a.type < 0) return amount;
		if (cbs::champion_design(static_cast<cbs::ChampionType>(a.type)).passive == cbs::Passive::missing_health_damage)
			amount *= 1.0f + 0.5f * (1.0f - a.health / a.max_health);
		if (vs_camp && has_ip(fight_data(a), cbs::ItemPassive::monster)) amount *= 1.1f;
		return amount;
	}
	// Game::damage_champion's reductions before shields: durability, then jungle against camps
	float incoming(const Unit& b, float amount, bool from_camp)
	{
		const FightData& f = fight_data(b);
		if (has_ip(f, cbs::ItemPassive::durability)) amount *= 0.9f;
		if (from_camp && has_ip(f, cbs::ItemPassive::jungle)) amount *= 0.7f;
		return amount;
	}
	// what one basic attack of a takes off b (before b's shields); 0 if a cannot hurt b that way
	double attack_damage(const Unit& a, const Unit& b)
	{
		PRIM_PROF_BEGIN;
		last_work = {};
		const long long f0 = fd_fetches_;
		extra(AD_FUEL);
		const double r = attack_damage_(a, b);
		last_work.relax = fd_fetches_ - f0, last_work.tiles = b.kind;
		PRIM_PROF_END(5);
		return r;
	}
	double attack_damage_(const Unit& a, const Unit& b)
	{
		if (!a.valid() || !b.valid() || a.kind == b.kind && a.kind == 2) return 0;
		if (a.kind == 2) return incoming(b, a.strength, true); // a camp's attack on a champion
		if (b.kind == 2) return outgoing(a, a.strength, true) * cbs::champion_design(static_cast<cbs::ChampionType>(a.type)).camp_damage_multiplier;
		return incoming(b, outgoing(a, a.strength, false), false);
	}
	// what a's ability in `slot` takes off b (damage, stun and area damage abilities; 0 otherwise)
	double cast_damage(const Unit& a, double slot, const Unit& b)
	{
		extra(CD_FUEL);
		if (a.kind != 1 || !b.valid() || slot < 0 || slot > 1) return 0;
		const auto& ab = cbs::champion_design(static_cast<cbs::ChampionType>(a.type)).abilities[static_cast<int>(slot)];
		if (ab.kind != cbs::AbilityKind::damage && ab.kind != cbs::AbilityKind::cc && ab.kind != cbs::AbilityKind::aoe_damage) return 0;
		const float amount = outgoing(a, ab.modifier * a.focus, b.kind == 2);
		return b.kind == 2 ? amount : incoming(b, amount, false);
	}
	double shield(const Unit& u) { return extra(SH_FUEL), fight_data(u).shield; }
	// basic attacks of a that b survives before dying, plus one: shields absorb first, then health, hit by hit
	// in float as the engine does (1e9 if a cannot hurt b)
	double hits_to_kill(const Unit& a, const Unit& b)
	{
		PRIM_PROF_BEGIN;
		last_work = {};
		const long long f0 = fd_fetches_;
		const double r = hits_to_kill_(a, b);
		last_work.relax = fd_fetches_ - f0;
		PRIM_PROF_END(6);
		return r;
	}
	double hits_to_kill_(const Unit& a, const Unit& b)
	{
		const float d = static_cast<float>(attack_damage_(a, b));
		if (!(d > 0)) return 1e9;
		float sh = b.kind == 1 ? fight_data(b).shield : 0.0f, hp = b.health;
		int n = 0;
		while (hp > 0 && n < 100000)
		{
			float amount = d;
			if (sh > 0)
			{
				if (sh > amount) sh -= amount, amount = 0;
				else amount -= sh, sh = 0;
			}
			hp -= amount, ++n;
		}
		extra(HK_BASE + HK_HIT * n);
		last_work.pops = n;
		return n;
	}
	// fitted on cambc probes (FUEL.md): FD a champion's items and buffs read once per pass; the rest per call
	static constexpr double FD_FUEL = 900, AD_FUEL = 140, CD_FUEL = 204, SH_FUEL = 60, HK_BASE = 236, HK_HIT = 26;

	// ---- raw unit reads (SDK coverage): the host's data as the SDK reports it, no judgement. Unit handles
	// index per-pass caches; a unit out of vision reads as 0.
	struct UnitRaw // the arrays are filled when their stamp is stale, so they need no initialisation
	{
		std::uint64_t items_pass = 0, buffs_pass = 0, camp_pass = 0;
		std::uint32_t items[cbs::kNumItems];
		cbs::BuffRecord buffs[8];
		std::uint32_t nbuffs;
		std::int32_t camp_cd[2];
	};
	UnitRaw raw_ch_[cbs::kMaxChampions];
	UnitRaw raw_camp_[8]; // direct-mapped on the camp handle (no heap: a first use costs nothing extra)
	std::uint32_t raw_camp_h_[8] = { ~0u, ~0u, ~0u, ~0u, ~0u, ~0u, ~0u, ~0u };
	UnitRaw* raw_of(const Unit& u)
	{
		if (u.kind == 1 && u.h < cbs::kMaxChampions) return &raw_ch_[u.h];
		if (u.kind != 2) return nullptr;
		const int i = static_cast<int>(u.h & 7);
		if (raw_camp_h_[i] != u.h) raw_camp_h_[i] = u.h, raw_camp_[i].items_pass = raw_camp_[i].buffs_pass = raw_camp_[i].camp_pass = 0;
		return &raw_camp_[i];
	}
	// cooldown left on slot s (0 ready): a champion's ability, a camp's attack (0) / ability (1)
	double cooldown(const Unit& u, double s)
	{
		const int i = static_cast<int>(s);
		if (i < 0 || i > 1) return 0;
		if (u.kind == 1)
		{
			std::int32_t cd = 0;
			api.champion_cooldown(u.h, static_cast<std::uint32_t>(i), &cd);
			extra(RW_CD);
			return cd;
		}
		UnitRaw* r = raw_of(u);
		if (!r) return 0;
		if (r->camp_pass != pass_id)
		{
			r->camp_pass = pass_id;
			cbs::CampRecord c{};
			r->camp_cd[0] = r->camp_cd[1] = 0;
			if (api.camp(u.h, &c) == Err::success) r->camp_cd[0] = c.cooldowns[0], r->camp_cd[1] = c.cooldowns[1];
			extra(RW_CAMP_FETCH);
		}
		else extra(RW_CAMP_HIT);
		return r->camp_cd[i];
	}
	// a champion's ability design on slot s (any champion; the same table as slot_*)
	const cbs::AbilityProps& uprops(const Unit& u, double s)
	{
		static thread_local cbs::AbilityProps none{};
		const int i = static_cast<int>(s);
		if (u.kind != 1 || u.h >= 32 || i < 0 || i > 1) return none;
		const int k = static_cast<int>(u.h) * 2 + i;
		if (uprops_pass_[k] != pass_id)
		{
			uprops_[k] = {};
			api.champion_ability_props(u.h, static_cast<std::uint32_t>(i), &uprops_[k]);
			uprops_pass_[k] = pass_id;
			extra(RW_AB_FETCH);
		}
		else extra(RW_AB_HIT);
		return uprops_[k];
	}
	cbs::AbilityProps uprops_[64] = {};
	std::uint64_t uprops_pass_[64] = {};
	double ability(const Unit& u, double s, int which)
	{
		const cbs::AbilityProps& p = uprops(u, s);
		switch (which)
		{
		case 0: return p.kind;
		case 1: return p.cooldown;
		case 2: return p.range;
		case 3: return p.radius;
		case 4: return p.targets;
		case 5: return p.modifier;
		case 6: return p.duration;
		default: return p.attributes & 1u;
		}
	}
	// copies of item i a visible champion owns
	double item_count(const Unit& u, double i)
	{
		UnitRaw* r = u.kind == 1 ? raw_of(u) : nullptr;
		if (!r || !item_ok(i)) return 0;
		if (r->items_pass != pass_id)
		{
			r->items_pass = pass_id;
			std::fill(std::begin(r->items), std::end(r->items), 0u);
			api.champion_items(u.h, r->items);
			extra(RW_IT_FETCH);
		}
		else extra(RW_IT_HIT);
		return r->items[static_cast<int>(i)];
	}
	double unit_gold(const Unit& u)
	{
		if (u.kind != 1) return 0;
		std::uint32_t g = 0;
		api.champion_gold(u.h, &g);
		extra(RW_GOLD);
		return g;
	}
	// buffs of type t (0 shield, 1 stun, 2 enhanced attack) on a visible unit: their summed value (shields; the
	// number of buffs for other types), their longest duration left
	const UnitRaw* ubuffs(const Unit& u)
	{
		UnitRaw* r = raw_of(u);
		if (!r) return nullptr;
		if (r->buffs_pass != pass_id)
		{
			r->buffs_pass = pass_id;
			r->nbuffs = 0;
			if (u.kind == 1)
			{
				if (api.champion_buff_data(u.h, r->buffs, 8, &r->nbuffs) != Err::success) r->nbuffs = 0;
			}
			else
			{
				cbs::CampBuffRecord cb[8];
				std::uint32_t n = 0;
				if (api.camp_buffs(u.h, cb, 8, &n) == Err::success)
					for (std::uint32_t i = 0; i < n && i < 8; ++i) r->buffs[r->nbuffs++] = { cb[i].type, cb[i].timer, cb[i].magnitude };
			}
			r->nbuffs = std::min<std::uint32_t>(r->nbuffs, 8);
			extra(u.kind == 1 ? RW_BF_FETCH : RW_BF_CAMP_FETCH);
		}
		else extra(RW_BF_HIT);
		return r;
	}
	double buff_value(const Unit& u, double t)
	{
		const UnitRaw* r = ubuffs(u);
		double v = 0;
		if (r)
			for (std::uint32_t i = 0; i < r->nbuffs; ++i)
				if (r->buffs[i].type == static_cast<std::uint32_t>(t)) v += t == 0 ? r->buffs[i].value : 1; // the SDK has a value for shields only
		return v;
	}
	double buff_turns(const Unit& u, double t)
	{
		const UnitRaw* r = ubuffs(u);
		double v = 0;
		if (r)
			for (std::uint32_t i = 0; i < r->nbuffs; ++i)
				if (r->buffs[i].type == static_cast<std::uint32_t>(t)) v = std::max<double>(v, r->buffs[i].duration);
		return v;
	}
	// turns left on a visible champion's channel (recall, gem submission, teleport); 0 if none
	double channel_left(const Unit& u)
	{
		if (u.kind != 1) return 0;
		std::int32_t t = 0;
		if (api.champion_channel_time(u.h, &t) != Err::success) t = 0;
		extra(RW_CH);
		return t;
	}
	// turns until camp group g respawns (0 if it is not respawning)
	double group_cooldown(double g)
	{
		if (!group_ok(g)) return 0;
		std::int32_t t = 0;
		if (api.camp_group_cooldown(static_cast<std::uint32_t>(g), &t) != Err::success) t = 0;
		extra(RW_GCD);
		return t;
	}
	// a visible altar lock on tile p: hits left to break it (0 none); whether it is the enemy's
	const cbs::AltarLockRecord* lock_at(Tile p)
	{
		if (locks_pass_ != pass_id)
		{
			locks_pass_ = pass_id;
			nlocks_ = 0;
			api.altar_locks(locks_, 16, &nlocks_);
			nlocks_ = std::min<std::uint32_t>(nlocks_, 16);
			extra(RW_LK_FETCH);
		}
		else extra(RW_LK_HIT);
		for (std::uint32_t i = 0; i < nlocks_; ++i)
			if (locks_[i].x == p.x && locks_[i].y == p.y) return &locks_[i];
		return nullptr;
	}
	cbs::AltarLockRecord locks_[16] = {};
	std::uint32_t nlocks_ = 0;
	std::uint64_t locks_pass_ = 0;
	double lock_hits(Tile p)
	{
		const cbs::AltarLockRecord* l = lock_at(p);
		return l ? l->hits_remaining : 0;
	}
	bool lock_enemy(Tile p)
	{
		const cbs::AltarLockRecord* l = lock_at(p);
		return l && static_cast<int>(l->team) != api.team();
	}
	// fitted on cambc probes (calib5, FUEL.md), beyond the Api's price of the call: a call, a record's fetch
	// (once per unit per pass), a cached read
	static constexpr double RW_CD = 40, RW_GOLD = 21, RW_CH = 17, RW_GCD = 47, RW_CAMP_FETCH = 94, RW_CAMP_HIT = 63, RW_AB_FETCH = 73,
							RW_AB_HIT = 45, RW_IT_FETCH = 206, RW_IT_HIT = 31, RW_BF_FETCH = 99, RW_BF_CAMP_FETCH = 90, RW_BF_HIT = 55,
							RW_LK_FETCH = 38, RW_LK_HIT = 22;

	// ---- abilities
	const cbs::AbilityProps& props(int s)
	{
		static thread_local cbs::AbilityProps none{};
		if (s < 0 || s > 1) return none;
		if (props_pass_[s] != pass_id)
		{
			props_[s] = {};
			api.champion_ability_props(self(), static_cast<std::uint32_t>(s), &props_[s]);
			props_pass_[s] = pass_id;
		}
		return props_[s];
	}
	double slot_kind(double s) { return extra(90), props(static_cast<int>(s)).kind; }
	bool slot_ready(double s)
	{
		const int i = static_cast<int>(s);
		if (i < 0 || i > 1 || props(i).kind == 0) return false;
		std::int32_t cd = 1;
		api.champion_cooldown(self(), static_cast<std::uint32_t>(i), &cd);
		extra(90);
		return cd <= 0;
	}
	double slot_range(double s) { return extra(90), props(static_cast<int>(s)).range; }
	double slot_radius(double s) { return props(static_cast<int>(s)).radius; }
	double slot_targets(double s) { return props(static_cast<int>(s)).targets; }
	bool slot_moveless(double s) { return props(static_cast<int>(s)).attributes & 1u; }

	// ---- items
	static bool item_ok(double i) { return i >= 0 && i < cbs::kNumItems; }
	double item_cost(double i) { return item_ok(i) ? cbs::item_design(static_cast<int>(i)).cost : 0; }
	double item_stat(double i, int which)
	{
		if (!item_ok(i)) return 0;
		const auto& d = cbs::item_design(static_cast<int>(i));
		return which == 0 ? d.health_points : which == 1 ? d.strength_points : d.focus_points;
	}
	double item_passive(double i) { return item_ok(i) ? static_cast<int>(cbs::item_design(static_cast<int>(i)).passive) : 0; }
	double items_owned(double i)
	{
		if (!item_ok(i)) return 0;
		load_items();
		return items_[static_cast<int>(i)];
	}
	bool has_lock()
	{
		load_cons();
		return cons_[cbs::consumable::altar_lock] > 0;
	}

	// ---- memory
	double read_shared(double i)
	{
		if (i < 0 || i >= cbs::kSharedMemory) return 0;
		std::uint8_t v = 0;
		api.read_shared_memory(static_cast<std::int32_t>(i), &v, 1);
		extra(8);
		return v;
	}
	void write_shared(double i, double v)
	{
		if (i < 0 || i >= cbs::kSharedMemory) return;
		const std::uint8_t b = static_cast<std::uint8_t>(std::clamp(std::floor(v), 0.0, 255.0));
		api.write_shared_memory(static_cast<std::int32_t>(i), &b, 1);
	}

	// ---- draft (champion types; Cassi & Issac are one pick, reported as CASSI)
	static int choice_to_type(int c) { return c <= 3 ? c : c + 1; }
	static int type_to_choice(int t) { return t <= 3 ? t : t == 4 ? 3 : t - 1; }
	bool picked(bool enemy, double t)
	{
		const int want = type_to_choice(static_cast<int>(t));
		for (std::uint32_t r = 0; r < 6; ++r)
		{
			std::int32_t p = -1;
			if (api.draft_get(enemy ? 1 - api.team() : api.team(), r, &p) == Err::success && p == want) return extra(60), true;
		}
		extra(60);
		return false;
	}

	// ---- the options of the current pass (legal as far as we know; the engine has the last word)
	// the target unit of an option of this pass (an entry of the pass's cached unit lists)
	const Unit& unit_of(const Option& o) const
	{
		extra(20); // o.unit in a gene: ~20 in the bot (score variants)
		static const Unit none{};
		const Units* us = o.usrc == 1 ? &enemies_ : o.usrc == 2 ? &camps_ : o.usrc == 3 ? &allies_ : nullptr;
		if (o.usrc == 4) return me_;
		return us && o.ui >= 0 && o.ui < static_cast<int>(us->size()) ? (*us)[o.ui] : none;
	}
	std::unique_ptr<OptionList> opts_buf = std::make_unique<OptionList>(); // reused by play_turn (24 KB: off the stack)
	std::vector<Option> failed_buf; // options the engine refused this turn
	KindFilter* filter = nullptr;			   // set by play_turn
	// what the loop did this turn, by option kind (read by after() through acted / acted_tile)
	bool acted_[16] = {};
	Tile acted_tile_[16];
	void reset_acted()
	{
		for (int k = 0; k < 16; ++k) acted_[k] = false, acted_tile_[k] = Tile{};
	}
	void note_acted(const Option& o)
	{
		if (o.kind > 0 && o.kind < 16) acted_[o.kind] = true, acted_tile_[o.kind] = o.tile;
	}
	bool acted(double k) const { return k > 0 && k < 16 && acted_[static_cast<int>(k)]; }
	Tile acted_tile(double k) const { return k > 0 && k < 16 ? acted_tile_[static_cast<int>(k)] : Tile{}; }
	// consider(kind), once per kind per pass; kinds it rejects are neither listed nor scored
	bool want(int kind)
	{
		if (!filter || !filter->has_consider()) return true;
		if (want_pass_ != pass_id)
		{
			want_pass_ = pass_id;
			for (auto& w : want_) w = -1;
		}
		if (want_[kind] < 0) want_[kind] = filter->consider_kind(kind) ? 1 : 0;
		return want_[kind];
	}
	std::int8_t want_[16];
	std::uint64_t want_pass_ = 0;

	void options(OptionList& out)
	{
		list_options(out); // priced by section inside (the bot's own listing work, fitted on idle / starter / farmer)
	}
#ifdef GENOME_PROF
	// listing fuel by section (bot: real fuel), summed over a turn's passes: start, shop, move, attack, cast, ward, recall, tribute
	// with the options each section added, and the units / tiles it scanned (lp_scan_)
	std::int64_t lp_[8] = {}, lp_t_ = 0, lp_n_[8] = {}, lp_scan_[8] = {}, lp_act_[8] = {}, lp_scan2_[8] = {}, lp_passes_ = 0;
	int lp_n0_ = 0;
#define LMARK(i) (lp_[i] += lp_t_ - api.fuel_remaining(), lp_n_[i] += out.n - lp_n0_, lp_n0_ = out.n, lp_t_ = api.fuel_remaining())
#define LSCAN(i, k) (lp_scan_[i] += (k))
#define LACT(i) (++lp_act_[i])
#define LSCAN2(i, k) (lp_scan2_[i] += (k))
#else
#define LSCAN2(i, k) ((void)0)
#define LACT(i) ((void)0)
#define LMARK(i) ((void)0)
#define LSCAN(i, k) ((void)0)
#define LACT(i) ((void)0)
#define LSCAN2(i, k) ((void)0)
#endif
	void list_options(OptionList& out)
	{
		out.n = 0;
#ifdef GENOME_PROF
		lp_t_ = api.fuel_remaining(), lp_n0_ = 0, ++lp_passes_;
#endif
		if (api.champ() < 0)
		{
			for (int c = 0; c < cbs::kNumDraftChoices; ++c)
			{
				const int t = choice_to_type(c);
				if (picked(false, t)) continue; // the opponent's picks stay legal (GameRules: Drafting)
				out.add(PICK).champ = static_cast<std::int8_t>(t);
			}
			return;
		}
		const Unit& self_u = me_u();
		const std::uint32_t st = self_u.state;
		const bool alive_now = st & cbs::state_bit::alive;
		if (alive_now && (st & (cbs::state_bit::recalling | cbs::state_bit::submitting)))
		{
			out.add(CANCEL);
			return;
		}
		if (alive_now && (st & cbs::state_bit::teleporting)) return;
		LMARK(0);
		extra(10);
		if ((want(BUY) || want(BUY_LOCK)) && can_shop())
		{
			LACT(1);
			const double g = gold();
			if (want(BUY))
				for (const ShopItem& it : shop_items())
				{
					LSCAN(1, 1);
					extra(24);
					if (it.cost > g) continue;
					// counts in powers of two up to what we can pay: any number in a few passes
					for (int c = 1; c * it.cost <= g; c *= 2)
					{
						Option& o = out.add(BUY);
						o.item = static_cast<std::int8_t>(it.item), o.count = c;
						extra(55);
					}
				}
			if (want(BUY_LOCK) && g >= cbs::consumable_design(cbs::consumable::altar_lock).cost && !has_lock()) out.add(BUY_LOCK);
		}
		LMARK(1);
		if (!alive_now) return extra(250); // a dead champion's turn costs ~250 more in the bot (starter games)
		const Tile p = self_u.pos;
		const int W = m.W, H = m.H;
		LACT(0);
		extra(40);
		const int n_move = out.n;
		if ((st & cbs::state_bit::can_move) && want(MOVE))
		{
			LACT(2);
			for (int y = std::max(0, p.y - 1); y <= std::min(H - 1, p.y + 1); ++y)
			{
				const std::uint8_t* row = row_classes(y);
				for (int x = std::max(0, p.x - 1); x <= std::min(W - 1, p.x + 1); ++x)
				{
					if ((x == p.x && y == p.y) || (row[x] & (kWall | kHole | kAltar | kEnemySpawn)) || occupied(x, y)) continue;
					out.add(MOVE).tile = { x, y };
				}
			}
			extra(421 + 1.24 * chunks() + 70.0 * (out.n - n_move));
		}
		LMARK(2);
		if ((st & cbs::state_bit::can_attack) && want(ATTACK))
		{
			LACT(3);
			add_units(out, ATTACK, -1, enemies(), 1, self_u.attack_range, p);
			add_units(out, ATTACK, -1, camps(), 2, self_u.attack_range, p);
		}
		LMARK(3);
		if ((st & cbs::state_bit::can_cast) && want(CAST))
			for (int s = 0; s < 2; ++s)
			{
				LACT(4);
				extra(248);
				if (!slot_ready(s)) continue;
				LSCAN2(5, 1); // ready slots (counted under ward's second column)
				const auto& pr = props(s);
				const double reach = pr.range + 0.5;
				if (pr.targets & cbs::target::enemies) add_units(out, CAST, s, enemies(), 1, reach, p);
				if (pr.targets & cbs::target::camps) add_units(out, CAST, s, camps(), 2, reach, p);
				if (pr.targets & cbs::target::allies) add_units(out, CAST, s, allies(), 3, reach, p);
				if (pr.targets & cbs::target::self)
				{
					Option& o = unit_option(out, CAST, self_u, 4, 0);
					o.slot = static_cast<std::int8_t>(s);
				}
				if (pr.targets & cbs::target::ground)
				{
					const int r = static_cast<int>(std::floor(pr.range));
					tile_options(out, CAST, s, p, r, true);
				}
			}
		LMARK(4);
		{
			cbs::WardResources wr{};
			api.champion_wards(self(), &wr);
			LACT(5);
			extra(168);
			if (wr.charges > 0 && want(WARD)) tile_options(out, WARD, -1, p, static_cast<int>(cbs::settings().ward_placement_radius), false);
		}
		LMARK(5);
		LACT(6);
		extra(11);
		if (!(row_classes(p.y)[p.x] & kMySpawn) && want(RECALL)) out.add(RECALL), extra(50);
		LMARK(6);
		const double g = gems();
		const bool tribute = g > 0 && want(TRIBUTE), lock = want(LOCK) && has_lock();
		LACT(7);
		if (tribute || lock)
		{
			LSCAN(7, m.altar_list.size());
			extra(59.0 * m.altar_list.size());
			for (Vec2 a : m.altar_list)
			{
				const int d = cbs::chebyshev(a, p.v());
				// at an enemy-locked altar a tribute is legal too: it hits the lock (5 hits clear it)
				if (tribute && d <= cbs::settings().submit_gems_range) out.add(TRIBUTE).tile = { a.x, a.y };
				if (lock && d <= 2) out.add(LOCK).tile = { a.x, a.y };
			}
		}
		LMARK(7);
	}
	// The tiles within Chebyshev r of p that are not walls (row-major; ground casts skip p itself).
	void tile_options(OptionList& out, int kind, int slot, Tile p, int r, bool skip_self)
	{
		const int W = m.W;
		const int x0 = std::max(0, p.x - r), x1 = std::min(W - 1, p.x + r);
		const int scanned = (x1 - x0 + 1) * (std::min(m.H - 1, p.y + r) - std::max(0, p.y - r) + 1);
		LSCAN(kind == WARD ? 5 : 4, scanned);
		const int n0 = out.n;
		for (int y = std::max(0, p.y - r), y1 = std::min(m.H - 1, p.y + r); y <= y1; ++y)
		{
			const std::uint8_t* row = row_classes(y);
			for (int x = x0; x <= x1; ++x)
			{
				if ((row[x] & kWall) || (skip_self && x == p.x && y == p.y)) continue;
				Option& o = out.add(kind);
				o.slot = static_cast<std::int8_t>(slot), o.tile = { x, y };
			}
		}
		extra(kind == WARD ? 17.8 * scanned + 40.0 * (out.n - n0) : 56.0 * scanned);
	}
	void add_units(OptionList& out, int kind, int slot, const Units& us, int src, double reach, Tile p)
	{
		if (kind == ATTACK) LSCAN(3, us.size());
		else LSCAN2(4, us.size()), extra(75.0 * us.size());
		for (int i = 0; i < static_cast<int>(us.size()); ++i)
			if (dist_raw(p, us[i].pos) <= reach) unit_option(out, kind, us[i], src, i).slot = static_cast<std::int8_t>(slot), extra(kind == ATTACK ? 97 : 0);
	}

	// Do one option; false if the engine refused it (it is then skipped for the rest of the turn).
	bool execute(const Option& o)
	{
#ifndef GENOME_BOT
		// GENOME_CHECK_FIGHT=1 (simulator): every attack / damage cast checks the predicted damage against the
		// target's actual health and shield loss (@@FC lines on stderr)
		static const bool check = std::getenv("GENOME_CHECK_FIGHT") != nullptr;
		if (check && (o.kind == ATTACK || o.kind == CAST) && o.ukind != 0)
		{
			const Unit tgt = unit_of(o), self = me_u();
			const double pred = o.kind == ATTACK ? attack_damage(self, tgt) : cast_damage(self, o.slot, tgt);
			auto pool = [&]() -> double {
				const auto& g = api.game();
				if (o.ukind == 1)
				{
					const auto& c = g.champs[o.uh];
					double sh = 0;
					for (int i = 0; i < c.buffs.n; ++i)
						if (c.buffs.b[i].type == cbs::BuffType::shield) sh += c.buffs.b[i].value;
					return c.alive ? c.hp + sh : 0;
				}
				return g.camps[o.uh].life == cbs::CampLife::dead ? 0 : g.camps[o.uh].hp;
			};
			const double before = pool();
			const bool r = execute_(o);
			const double after = pool();
			const bool splash = cbs::champion_design(static_cast<cbs::ChampionType>(self.type)).passive == cbs::Passive::splash_attack;
			if (r && after > 0 && !splash && o.ukind == 1 && !(cbs::champion_design(static_cast<cbs::ChampionType>(tgt.type)).passive == cbs::Passive::retaliation))
				std::fprintf(stderr, "@@FC kind %d pred %.4f actual %.4f %s\n", o.kind, pred, before - after, std::fabs(pred - (before - after)) < 1e-3 ? "ok" : "BAD");
			else if (r && after > 0 && o.ukind == 2)
				std::fprintf(stderr, "@@FC kind %d camp pred %.4f actual %.4f %s\n", o.kind, pred, before - after, std::fabs(pred - (before - after)) < 1e-3 ? "ok" : "BAD");
			return r;
		}
#endif
		return execute_(o);
	}
	bool execute_(const Option& o)
	{
		std::int32_t ok = 0;
		Err e = Err::invalid_action;
		switch (o.kind)
		{
		case PICK: e = api.draft_champion(type_to_choice(o.champ)); ok = 1; break;
		case MOVE: e = api.move_to(o.tile.v(), &ok); break;
		case ATTACK: e = api.attack(static_cast<std::uint32_t>(o.ukind == 1 ? cbs::EntityKind::champion : cbs::EntityKind::camp), o.uh), ok = 1; break;
		case CAST:
		{
			const std::uint32_t kind = static_cast<std::uint32_t>(
				!o.ukind ? cbs::EntityKind::none : o.ukind == 1 ? cbs::EntityKind::champion : cbs::EntityKind::camp);
			const Vec2 at = o.tile.v(); // a unit target's tile is its position
			e = api.cast(static_cast<std::uint32_t>(o.slot), kind, o.ukind ? o.uh : 0, at, &ok);
			break;
		}
		case WARD: e = api.place_ward(o.tile.v(), &ok); break;
		case BUY: e = api.buy_item(static_cast<std::uint32_t>(o.item), static_cast<std::uint32_t>(o.count)), ok = 1; break;
		case BUY_LOCK: e = api.buy_consumable(cbs::consumable::altar_lock), ok = 1; break;
		case RECALL: e = api.recall(), ok = 1; break;
		case TRIBUTE: e = api.submit_gems(o.tile.v()), ok = 1; break;
		case CANCEL: e = api.cancel_channel(), ok = 1; break;
		case LOCK: e = api.use_consumable(cbs::consumable::altar_lock, o.tile.v(), &ok); break;
		default: break;
		}
		return e == Err::success && ok;
	}

private:
	std::uint32_t self_ = 0;
	Unit me_;
	Units enemies_, allies_, camps_;
	double gems_ = 0, gold_ = 0;
	bool have_me_ = false, have_enemies_ = false, have_allies_ = false, have_camps_ = false, have_gems_ = false, have_gold_ = false,
		 have_occ_ = false, have_items_ = false, have_cons_ = false;
	Bitboard occ_[3];
	std::uint32_t items_[cbs::kNumItems] = {}, cons_[cbs::kNumConsumables] = {};
	cbs::AbilityProps props_[2] = {};
	std::uint64_t props_pass_[2] = { 0, 0 };
	std::shared_ptr<const Bitboard> altars_, walls_, bushes_, holes_, myspawn_, espawn_, campsp_;
	std::shared_ptr<const Bitboard> type_sp_[static_cast<int>(cbs::CampType::count)];
	struct CampAt
	{
		int tile, camp;
	};
	static std::size_t camp_hash(int key, std::size_t cap) { return (static_cast<std::uint32_t>(key) * 2654435761u >> 8) & (cap - 1); }
	std::vector<CampAt> camp_at_;
	std::uint64_t rng_ = 1;
	template <class Fill>
	Tiles sdk_mask(Fill&& fill)
	{
		auto b = std::make_shared<Bitboard>();
		fill(*b);
		return { b };
	}

	static Unit from_champ(std::uint32_t h, const cbs::ChampionInfo& ci)
	{
		Unit u;
		u.kind = 1, u.h = h, u.type = ci.type, u.pos = { ci.x, ci.y };
		u.health = ci.health, u.max_health = ci.max_health, u.strength = ci.strength, u.focus = ci.focus;
		u.attack_range = ci.attack_range, u.move_speed = ci.move_speed, u.state = ci.state;
		return u;
	}
	void champs(bool enemy, Units& out)
	{
		out.clear();
		std::uint32_t ids[16], n = 0;
		if (enemy) api.enemies(ids, 16, &n);
		else api.allies(ids, 16, &n);
		for (std::uint32_t i = 0; i < n && i < 16; ++i)
		{
			if (!enemy && ids[i] == self()) continue;
			cbs::ChampionInfo ci{};
			if (api.champion(ids[i], &ci) != Err::success || !(ci.state & cbs::state_bit::alive)) continue;
			Unit u = from_champ(ids[i], ci);
			u.enemy = enemy;
			out.push_back(u);
		}
		extra(enemy ? 250 + 170 * out.size() : 170 * out.size());
	}
	Option& unit_option(OptionList& out, int kind, const Unit& u, int src, int i)
	{
		Option& o = out.add(kind);
		o.tile = u.pos, o.ukind = static_cast<std::int8_t>(u.kind), o.uh = u.h, o.usrc = static_cast<std::int8_t>(src), o.ui = static_cast<std::int16_t>(i);
		return o;
	}
	// Static terrain class per tile, as plain bytes: one host bitboard test costs ~120 fuel in the bot.
	enum : std::uint8_t { kWall = 1, kHole = 2, kAltar = 4, kEnemySpawn = 8, kMySpawn = 16 };
	static constexpr double ROW_FUEL_BASE = 0, ROW_FUEL_PER_TILE = 16; // a row's first build in the bot (~1.6k per 100-tile row)
	// kSpread[b]: bit i of b moved to bit 0 of byte i
	static constexpr std::array<std::uint64_t, 256> kSpread = [] {
		std::array<std::uint64_t, 256> t{};
		for (int b = 0; b < 256; ++b)
			for (int i = 0; i < 8; ++i)
				if (b >> i & 1) t[b] |= std::uint64_t{ 1 } << (8 * i);
		return t;
	}();
	struct ShopItem
	{
		int item, cost;
	};
	std::vector<ShopItem> shop_; // the purchasable items, in item order (static)
	const std::vector<ShopItem>& shop_items()
	{
		if (shop_.empty())
			for (int i = 0; i < cbs::kNumItems; ++i)
				if (cbs::item_design(i).purchasable) shop_.push_back({ i, static_cast<int>(cbs::item_design(i).cost) });
		return shop_;
	}
	// Terrain classes of a map row, built the first time the row is read (the whole W x H table at once
	// cost ~51k fuel on a 100 x 100 map's first turn; a row costs ~W/8 chunk words per mask).
	std::unique_ptr<std::uint8_t[]> cls_;
	std::vector<std::uint8_t> row_built_;
	const std::uint8_t* row_classes(int y)
	{
		if (!cls_) cls_.reset(new std::uint8_t[static_cast<std::size_t>(m.W) * m.H]), row_built_.assign(m.H, 0);
		std::uint8_t* row = cls_.get() + static_cast<std::size_t>(y) * m.W;
		if (!row_built_[y]) build_row(y, row), row_built_[y] = 1;
		return row;
	}
	void build_row(int y, std::uint8_t* row)
	{
		const Bitboard* masks[5] = { &m.walls, &m.holes, &m.altars, &m.spawn_mask[1 - api.team()], &m.spawn_mask[api.team()] };
#ifdef GENOME_BOT
		// one byte of each mask's chunk word per 8 tiles of the row, spread to 8 class bytes by table
		const int base = (y >> 3) * cbs::hostbb::stride, sh = (y & 7) * 8;
		for (int cx = 0, x0 = 0; x0 < m.W; ++cx, x0 += 8)
		{
			std::uint64_t v = 0;
			for (int k = 0; k < 5; ++k) v |= kSpread[(masks[k]->w[base + cx] >> sh) & 0xFFu] << k;
			if (x0 + 8 <= m.W) std::memcpy(row + x0, &v, 8);
			else
				for (int i = 0; x0 + i < m.W; ++i) row[x0 + i] = static_cast<std::uint8_t>(v >> (8 * i));
		}
#else
		for (int x = 0; x < m.W; ++x)
		{
			std::uint8_t c = 0;
			for (int k = 0; k < 5; ++k) c |= static_cast<std::uint8_t>(masks[k]->test(x, y)) << k;
			row[x] = c;
		}
		extra(ROW_FUEL_BASE + ROW_FUEL_PER_TILE * m.W);
#endif
	}
	std::vector<std::shared_ptr<const Bitboard>> group_tiles_;
	// a unit stands on (x, y): the three SDK occupancy masks, tested per tile (no board unions)
	bool occupied(int x, int y)
	{
		if (!have_occ_)
		{
			api.ally_occupancy(occ_[0]);
			api.enemy_occupancy(occ_[1]);
			api.camp_occupancy(occ_[2], 0);
			have_occ_ = true;
		}
		return occ_[0].test(x, y) || occ_[1].test(x, y) || occ_[2].test(x, y);
	}
	void load_items()
	{
		if (have_items_) return;
		std::fill(std::begin(items_), std::end(items_), 0u);
		api.champion_items(self(), items_);
		have_items_ = true;
		extra(210);
	}
	void load_cons()
	{
		if (have_cons_) return;
		std::fill(std::begin(cons_), std::end(cons_), 0u);
		api.champion_consumables(self(), cons_);
		have_cons_ = true;
		extra(73);
	}
	template <class Fill>
	Tiles stat(std::shared_ptr<const Bitboard>& slot, Fill&& fill)
	{
		if (!slot)
		{
			auto b = std::make_shared<Bitboard>();
			fill(*b);
			slot = b;
		}
		return { slot };
	}
	Tiles combine(const Tiles& a, const Tiles& b, int op)
	{
		auto r = std::make_shared<Bitboard>();
		if (a.b) *r = *a.b;
		if (op == 0 && b.b) *r |= *b.b;
		if (op == 1)
		{
			if (b.b) *r &= *b.b;
			else r->clear();
		}
		if (op == 2 && b.b) r->andnot(*b.b);
		return { r };
	}
};

// Generated genes derive from this.
struct GenesBase : KindFilter
{
	explicit GenesBase(Ctx& x) : X(x) {}
	virtual ~GenesBase() = default;
	virtual double score_option(const Option& o) = 0;
	virtual void run_update() = 0;
	virtual void run_after() {}
	// The optional reserve() entry gene: no new pass of the loop starts with less fuel left than this
	// (read once per turn, after update()).
	static constexpr double kDefaultReserve = 15000;
	virtual double reserve_fuel() { return kDefaultReserve; }
	bool consider_kind(int) override { return true; }
	bool has_consider() const override { return false; }
	Ctx& X;
};

using MakeGenes = GenesBase* (*)(Ctx&);

// One turn of the fixed loop. Returns the number of actions taken.
inline int play_turn(Ctx& X, GenesBase& g, int max_passes = 16)
{
	OptionList& opts = *X.opts_buf;
	std::vector<Option>& failed = X.failed_buf;
	failed.clear();
	auto same = [](const Option& a, const Option& b) {
		return a.kind == b.kind && a.ukind == b.ukind && a.uh == b.uh && a.tile == b.tile && a.slot == b.slot && a.item == b.item &&
			   a.champ == b.champ && a.count == b.count;
	};
	const bool draft = X.api.champ() < 0;
	X.filter = &g;
#ifdef GENOME_PROF
#ifndef GENOME_PROF_EVERY
#define GENOME_PROF_EVERY 50
#endif
	// fuel by phase (bot build: real fuel from the engine); printed every 50th round
	std::int64_t f_opt = 0, f_score = 0, f_exec = 0, t0 = X.api.fuel_remaining(), tp, start = t0;
	const long long ops0 = X.ops;
	int npass = 0, nopts = 0;
#define PROF_MARK(acc) (tp = X.api.fuel_remaining(), acc += t0 - tp, t0 = tp)
#else
#define PROF_MARK(acc) ((void)0)
#endif
	// GENOME_FUEL=N: passes and turns that spent more than N fuel (simulator diagnostics, @@FP / @@F lines on stderr)
	static const long fuel_trace = std::getenv("GENOME_FUEL") ? std::atol(std::getenv("GENOME_FUEL")) : -1;
#ifndef GENOME_TRACE_ON
#define GENOME_TRACE_ON 0 // 1: trace in the bot too (no environment there)
#endif
#ifdef GENOME_BOT
#define GENOME_TRACE_OUT stdout // the replay keeps the bot's stdout
#else
#define GENOME_TRACE_OUT stderr
#endif
	static const bool trace = GENOME_TRACE_ON || std::getenv("GENOME_TRACE");
#ifdef GENOME_PROF
	static int play_turns = 0;
	if (!draft) ++play_turns;
	const bool t1 = !draft && play_turns == 1;
	if (!draft && play_turns == 2)
	{
		std::printf("@@T1 c%d marks", X.api.champ());
		for (int i = 0; i < n_t1_marks; ++i) std::printf(" %lld", static_cast<long long>(t1_marks[i]));
		std::printf("\n");
		for (const auto& gs : gene_stats)
			if (gs.name && gs.calls) std::printf("@@T1G %s calls %lld fuel %lld self %lld\n", gs.name, gs.calls, gs.fuel, gs.self);
	}
	if (t1) t1_mark(X.api.fuel_remaining()); // play_turn start
	// GENOME_TURN_CALLS=1 (simulator): team 0's calls per gene and options listed, every play turn (@@TC lines)
	static const bool turn_calls = std::getenv("GENOME_TURN_CALLS") != nullptr;
	if (turn_calls && !draft) std::fill(std::begin(X.turn_calls_buf), std::end(X.turn_calls_buf), 0), GeneScope::turn_calls = X.turn_calls_buf;
#endif
	X.new_pass();
	X.reset_acted();
	if (!draft) g.run_update();
#ifdef GENOME_PROF
	if (t1) t1_mark(X.api.fuel_remaining()); // after update()
#endif
	const double reserve = draft ? 0.0 : g.reserve_fuel();
	int acted = 0;
	for (int pass = 0; pass < max_passes; ++pass)
	{
		// the pass guard: a later pass starts only with at least reserve() fuel left
		if (pass > 0 && !draft && static_cast<double>(X.api.fuel_remaining()) < reserve) break;
		if (!draft) X.extra(pass == 0 ? 575 : 1074); // a pass's own work in the bot (fitted per turn: seed and v23, identical games)
		X.new_pass();
#ifdef GENOME_PROF
		std::int64_t f_upd = 0;
		PROF_MARK(f_upd);
		++npass;
#endif
		X.options(opts);
		PROF_MARK(f_opt);
#ifdef GENOME_PROF
		nopts += static_cast<int>(opts.size());
#endif
		const Option* best = nullptr;
		double bs = 0;
		for (const Option& o : opts)
		{
			bool skip = false;
			for (const Option& f : failed) skip |= same(o, f);
			if (skip) continue;
			X.extra(30); // the loop's own work per option scored in the bot (call, compare), beyond the gene's operations
			const double s = g.score_option(o);
			if (!best || s > bs) best = &o, bs = s;
		}
		PROF_MARK(f_score);
		// the draft must pick; everything else needs a positive score
		if (!best || (!draft && bs <= 0)) break;
		const bool ok = X.execute(*best);
		PROF_MARK(f_exec);
		if (trace)
			std::fprintf(GENOME_TRACE_OUT, "@@G r%d t%d c%d pos %d,%d kind %d score %.2f tile %d,%d unit %d:%u slot %d item %d champ %d ok %d of %d camps %zu st %u ar %d mind %.0f gold %.0f shop %d\n",
						 static_cast<int>(X.round()), X.api.team(), X.api.champ(), X.me_u().pos.x, X.me_u().pos.y, best->kind, bs, best->tile.x,
						 best->tile.y, best->ukind, best->uh, best->slot, best->item, best->champ, ok, opts.size(), X.camps().size(), X.me_u().state, X.me_u().attack_range, [&] { double d = 1e9; for (const Unit& u : X.camps()) d = std::min(d, X.dist_raw(X.me_u().pos, u.pos)); return d; }(), X.gold(), (int)X.can_shop());
#ifdef GENOME_PROF
		if (t1) t1_mark(f_opt), t1_mark(f_score), t1_mark(X.api.fuel_remaining()); // per pass: listing, scoring so far; fuel left
#endif
		if (ok) ++acted, X.note_acted(*best);
		else failed.push_back(*best);
		if (fuel_trace >= 0 && X.api.spent > fuel_trace)
			std::fprintf(stderr, "@@FP r%d t%d c%d pass %d spent %lld kind %d ok %d options %d\n", static_cast<int>(X.round()), X.api.team(),
						 X.api.champ(), pass, static_cast<long long>(X.api.spent), best->kind, ok ? 1 : 0, opts.size());
		if (draft) break;
	}
	if (!draft)
	{
		X.new_pass(); // after() sees the state after this turn's actions
		g.run_after();
	}
#ifdef GENOME_PROF
	if (!draft && X.api.champ() == 0 && static_cast<int>(X.round()) % 500 == 0)
		for (const auto& gs : gene_stats)
			if (gs.name) std::printf("@@GENE r%d %s calls %lld fuel %lld per %.0f self %lld kids %lld\n", static_cast<int>(X.round()), gs.name, gs.calls, gs.fuel, gs.calls ? double(gs.fuel) / gs.calls : 0.0, gs.self, gs.kids);
	// the field records, a few per turn from round 600 (a long print can be suspended and lost)
	static int field_printed = 0, prim_printed = 0;
	if (!draft && X.api.champ() == 0 && static_cast<int>(X.round()) >= 600)
		for (int i = 0; i < 4 && prim_printed < n_prim_recs; ++i, ++prim_printed)
		{
			const PrimRec& r = prim_recs[prim_printed];
			std::printf("@@PRIM %d fuel %lld tiles %lld pops %lld relax %lld scans %lld chunks %.0f\n", r.prim, r.fuel, r.n[0], r.n[1], r.n[2], r.n[3], X.chunks());
		}
	if (!draft && X.api.champ() == 0 && static_cast<int>(X.round()) >= 600)
		for (int i = 0; i < 4 && field_printed < n_field_recs; ++i, ++field_printed)
			std::printf("@@FIELD %d stop %d fuel %lld chunks %.0f\n", field_recs[field_printed].expansions, field_recs[field_printed].stopped,
						field_recs[field_printed].fuel, X.chunks());
	if (!draft && (GENOME_PROF_EVERY <= 1 || static_cast<int>(X.round()) % GENOME_PROF_EVERY == 1))
		std::printf("@@P t%d r%d c%d passes %d opts %d options %lld score %lld exec %lld left %lld ops %lld turn %lld\n", X.api.team(), static_cast<int>(X.round()),
					X.api.champ(), npass, nopts, static_cast<long long>(f_opt), static_cast<long long>(f_score),
					static_cast<long long>(f_exec), static_cast<long long>(X.api.fuel_remaining()), X.ops - ops0,
					static_cast<long long>(start - X.api.fuel_remaining()));
	if (!draft && (GENOME_PROF_EVERY <= 1 || static_cast<int>(X.round()) % GENOME_PROF_EVERY == 1))
	{
		std::printf("@@L t%d r%d c%d passes %lld chunks %.0f", X.api.team(), static_cast<int>(X.round()), X.api.champ(), (long long)X.lp_passes_, X.chunks());
		for (int i = 0; i < 8; ++i) std::printf(" | %lld %lld %lld %lld %lld", (long long)X.lp_[i], (long long)X.lp_n_[i], (long long)X.lp_scan_[i], (long long)X.lp_act_[i], (long long)X.lp_scan2_[i]);
		std::printf("\n");
	}
	for (int i = 0; i < 8; ++i) X.lp_[i] = X.lp_n_[i] = X.lp_scan_[i] = X.lp_act_[i] = X.lp_scan2_[i] = 0;
	X.lp_passes_ = 0;
#endif
#ifdef GENOME_PROF
	if (turn_calls && !draft && X.api.team() == 0)
	{
		std::printf("@@TC r%d c%d passes %d opts %d", static_cast<int>(X.round()), X.api.champ(), npass, nopts);
		for (int i = 0; i < 256; ++i)
			if (X.turn_calls_buf[i]) std::printf(" %d:%d", i, X.turn_calls_buf[i]);
		std::printf("\n");
		GeneScope::turn_calls = nullptr;
	}
#endif
	if (fuel_trace >= 0 && X.api.spent > fuel_trace)
		std::fprintf(stderr, "@@F r%d t%d c%d spent %lld acted %d draft %d\n", static_cast<int>(X.round()), X.api.team(), X.api.champ(),
					 static_cast<long long>(X.api.spent), acted, draft ? 1 : 0);
	return acted;
}

// A simulator Player running one genome (one GenesBase per bot instance).
class GenomePlayer : public cbs::Player
{
public:
	explicit GenomePlayer(MakeGenes make) : make_(make) {}
	const cbs::PriceTable* prices() const override { return &cbs::PriceTable::bot_wrapper(); }
	cbs::BotBody make_bot(int, int) override
	{
		MakeGenes make = make_;
		return [make](Api& api) {
			Ctx X(api);
			std::unique_ptr<GenesBase> g(make(X));
#ifdef GENOME_PROF
			if (api.champ() >= 0) t1_mark(api.fuel_remaining()); // runtime and genes made
#endif
			// the bot's one-off start-up on a champion's first turn (map and game built from the engine,
			// runtime tables): first-turn fuel minus the simulator's, idle genome on 8 maps (err < 4.5k)
			if (api.champ() >= 0)
			{
				const auto& m = api.map();
				std::int64_t holes = 0;
				for (int y = 0; y < m.H; ++y)
					for (int x = 0; x < m.W; ++x) holes += m.holes.test(x, y);
				X.extra(17444 + 3.13 * m.W * m.H + 35.5 * holes + 376.0 * m.camps.size());
			}
			for (;;)
			{
				play_turn(X, *g);
				api.end_turn();
			}
		};
	}

private:
	MakeGenes make_;
};
} // namespace genome
