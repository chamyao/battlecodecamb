// Genome runtime (docs/GENOME.md): the primitives genes call, the legal options of a turn and the fixed
// loop (list legal options, score each, do the best if its score > 0, look again).
//
// Written against cbs::Api, so the same code runs in the simulator (every engine call priced by the
// Api; genes' own operations charged through F(n)) and, later, in the bot over the real imports.
// Generated genes (genome/lang.py) include this header and derive from GenesBase.
#pragma once
#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cstdint>
#include <memory>
#include <vector>
#include "cbs/api.h"
#include "cbs/runner.h"

#ifndef GENOME_OP_FUEL
#define GENOME_OP_FUEL 4 // fuel per own operation (placeholder until calibrated against cambc)
#endif
#ifdef GENOME_BOT
#ifdef GENOME_PROF
#define F(n) (X.ops += (n))
#else
#define F(n) ((void)0)
#endif
#else
#define F(n) X.charge_ops(n)
#endif

namespace genome
{
#ifdef GENOME_PROF
// Inclusive fuel and calls per gene (real fuel in the bot), printed every GENOME_PROF_GENES rounds.
struct GeneStat
{
	const char* name = nullptr;
	long long calls = 0, fuel = 0;
};
inline GeneStat gene_stats[256];
struct GeneScope
{
	GeneStat& s;
	cbs::Api& api;
	std::int64_t t0;
	GeneScope(GeneStat& s, cbs::Api& api) : s(s), api(api), t0(api.fuel_remaining()) { ++s.calls; }
	~GeneScope() { s.fuel += t0 - api.fuel_remaining(); }
};
#define GENE_PROF(i, nm) genome::gene_stats[i].name = nm; genome::GeneScope gene_scope_(genome::gene_stats[i], X.api)
#else
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
struct Field
{
	std::shared_ptr<const std::vector<std::uint16_t>> d;
};
enum OptionKind
{
	PICK = 1, MOVE, ATTACK, CAST, WARD, BUY, RECALL, TRIBUTE, CANCEL, LOCK, BUY_LOCK
};
// Small on purpose: copying costs ~1 fuel per byte in the bot. The target unit lives in the pass's
// unit table (Ctx::unit_of); ukind/uh identify it across passes.
struct Option
{
	int kind = 0;
	int slot = -1, item = -1, champ = -1;
	Tile tile;
	int ukind = 0;
	std::uint32_t uh = 0;
	int ui = -1;
	int count = 1; // BUY: units bought at once (the SDK's buy_item count)
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
	// Simulator only: the runtime's own work in the bot beyond what the Api already prices (fitted
	// from genome/examples/calib.genome profiled in cambc; docs in genome/FUEL.md). Compiled away in the bot.
	void extra(double fuel)
	{
#ifndef GENOME_BOT
		if (fuel > 0) api.compute(static_cast<std::int64_t>(fuel));
#endif
	}
	double chunks() const { return ((m.W + 7) / 8) * ((m.H + 7) / 8); }
	void charge_ops(long n)
	{
		ops += n;
		api.compute(n * GENOME_OP_FUEL);
	}

	void new_pass()
	{
		pass_id = pass_counter()++;
		have_me_ = have_enemies_ = have_allies_ = have_camps_ = have_gems_ = have_gold_ = have_occ_ = have_items_ = false;
	}

	// ---- self
	const Unit& me()
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
	std::uint32_t self() { return me(), self_; }
	bool alive() { return me().state & cbs::state_bit::alive; }
	bool my_state(std::uint32_t bits) { return api.champ() >= 0 && (me().state & bits); }
	bool channeling() { return my_state(cbs::state_bit::recalling | cbs::state_bit::submitting | cbs::state_bit::teleporting); }
	// uniform integer in [0, n) from this instance's generator (generic operation, no engine call)
	double rand(double n)
	{
		rng_ ^= rng_ << 13, rng_ ^= rng_ >> 7, rng_ ^= rng_ << 17;
		const double k = std::floor(n);
		return k >= 1 ? static_cast<double>((rng_ >> 11) % static_cast<std::uint64_t>(std::min(k, 1e9))) : 0.0;
	}
	void set_priority(double p) { api.set_priority(static_cast<std::int32_t>(std::clamp(p, -1e6, 1e6))); }
	double gems()
	{
		if (!have_gems_) gems_ = unit_gems(me()), have_gems_ = true, extra(27);
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
		return enemies_;
	}
	const Units& allies()
	{
		if (!have_allies_) champs(false, allies_), have_allies_ = true;
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
			extra(600 + 80 * camps_.size());
		}
		return camps_;
	}
	double unit_gems(const Unit& u)
	{
		if (u.kind != 1) return 0;
		std::uint32_t g = 0;
		api.champion_gems(u.h, &g);
		return g;
	}
	bool unit_state(const Unit& u, std::uint32_t bit) { return u.kind == 1 && (u.state & bit); }
	bool camp_awake(const Unit& u)
	{
		if (u.kind != 2) return false;
		std::uint32_t life = 0;
		return api.camp_state(u.h, &life) == Err::success && life == static_cast<std::uint32_t>(cbs::CampLife::awake);
	}
	Tile camp_spawn(const Unit& u) const
	{
		if (u.kind != 2 || u.h >= m.camps.size()) return {};
		return { m.camps[u.h].pos.x, m.camps[u.h].pos.y };
	}
	// static map: the camp spawning on a tile (its type / group), -1 if none
	int camp_index(Tile t)
	{
		if (!in_bounds(t)) return -1;
		if (camp_at_.empty())
		{
			camp_at_.assign(static_cast<std::size_t>(m.W) * m.H, -1);
			for (std::size_t c = 0; c < m.camps.size(); ++c) camp_at_[m.idx(m.camps[c].pos)] = static_cast<int>(c);
		}
		return camp_at_[m.idx(t.v())];
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
		extra(41);
		return s == static_cast<std::uint32_t>(want);
	}
	bool group_respawning(double g) { return group_in_state(g, cbs::GroupState::respawning); }
	bool group_reward(double g) { return group_in_state(g, cbs::GroupState::reward); }
	Tiles group_tiles(double g)
	{
		if (!group_ok(g)) return { std::make_shared<Bitboard>() };
		// static: built once per group (each host bit set costs ~170 fuel in the bot)
		if (group_tiles_.empty()) group_tiles_.resize(m.groups.size());
		extra(30);
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
		extra(150);
		return v;
	}

	// ---- static map (built once per instance)
	Tiles altars() { return stat(altars_, [&](Bitboard& b) { b = m.altars; }); }
	Tiles walls() { return stat(walls_, [&](Bitboard& b) { b = m.walls; }); }
	Tiles bushes() { return stat(bushes_, [&](Bitboard& b) { b = m.bushes; }); }
	Tiles holes() { return stat(holes_, [&](Bitboard& b) { b = m.holes; }); }
	Tiles spawn(bool enemy)
	{
		return stat(enemy ? espawn_ : myspawn_, [&](Bitboard& b) { b = m.spawn_mask[enemy ? 1 - api.team() : api.team()]; });
	}
	Tiles camp_spawns()
	{
		return stat(campsp_, [&](Bitboard& b) {
			for (const auto& c : m.camps) b.set(c.pos);
		});
	}
	// spawn tiles of the camps of one type (static map)
	Tiles type_spawns(double k)
	{
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
	Tiles vision() { return sdk_mask([&](Bitboard& b) { api.vision(b); }); }
	Tiles ally_tiles() { return sdk_mask([&](Bitboard& b) { api.ally_occupancy(b); }); }
	Tiles enemy_tiles() { return sdk_mask([&](Bitboard& b) { api.enemy_occupancy(b); }); }
	Tiles camp_tiles() { return sdk_mask([&](Bitboard& b) { api.camp_occupancy(b, 0); }); }
	double width() const { return m.W; }
	double height() const { return m.H; }

	// ---- geometry
	bool in_bounds(Tile t) const { return t.valid() && m.in_bounds(t.v()); }
	double dist(Tile a, Tile b) const { return a.valid() && b.valid() ? cbs::chebyshev(a.v(), b.v()) : 1e9; }
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
		extra(120 + 52.0 * s.b->count(m.H));
		return best;
	}
	double size(const Tiles& s)
	{
		extra(80 + 1.0 * chunks());
		return s.b ? s.b->count(m.H) : 0;
	}
	bool contains(const Tiles& s, Tile t) { return extra(120), s.b && in_bounds(t) && s.b->test(t.v()); }
	Tiles tiles_or(const Tiles& a, const Tiles& b) { return extra(224 + 3.1 * chunks()), combine(a, b, 0); }
	Tiles tiles_and(const Tiles& a, const Tiles& b) { return extra(224 + 3.1 * chunks()), combine(a, b, 1); }
	Tiles tiles_minus(const Tiles& a, const Tiles& b) { return extra(225 + 4.0 * chunks()), combine(a, b, 2); }
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
		int count[cbs::kMaxDim + 1] = {};
		for (std::uint32_t i = 0; i < n; ++i) ++count[buf[i].y + 1];
		for (int y = 0; y < m.H; ++y) count[y + 1] += count[y];
		out.resize(n);
		for (std::uint32_t i = 0; i < n; ++i) out[count[buf[i].y]++] = Tile{ buf[i].x, buf[i].y };
#else
		s.b->for_each(m.H, [&](int x, int y) { out.push_back({ x, y }); });
		const_cast<Ctx*>(this)->extra(970 + 1.0 * chunks() + 81.0 * out.size());
#endif
		return out;
	}
	// Walking distance field to `goals` (walls, holes, altars and the enemy spawn block; goal tiles
	// themselves are allowed). One engine distance-field call, priced by the Api.
	Field field(const Tiles& goals)
	{
		auto d = std::make_shared<std::vector<std::uint16_t>>(static_cast<std::size_t>(m.W) * m.H, cbs::kUnreachable);
		if (goals.b && goals.b->any(m.H))
		{
			Bitboard blocked = m.walls, visited;
			blocked |= m.holes;
			blocked |= m.altars;
			blocked |= m.spawn_mask[1 - api.team()];
			blocked.andnot(*goals.b);
			api.distance_field(blocked, *goals.b, nullptr, cbs::kUnreachable, d->data(), visited);
			extra(97 * chunks() - 320);
		}
		return { d };
	}
	// Walking distance field to `goals` over every tile not in `walls` (goal tiles always allowed). The
	// search stops after the first distance layer that reaches a tile of `stop` (empty: the whole map);
	// tiles beyond it read as unreachable.
	Field field_avoid(const Tiles& goals, const Tiles& walls, const Tiles& stop)
	{
		auto d = std::make_shared<std::vector<std::uint16_t>>(static_cast<std::size_t>(m.W) * m.H, cbs::kUnreachable);
		if (goals.b && goals.b->any(m.H))
		{
			Bitboard blocked, visited;
			if (walls.b) blocked = *walls.b;
			blocked.andnot(*goals.b);
			const bool stops = stop.b && stop.b->any(m.H);
			api.distance_field(blocked, *goals.b, stops ? stop.b.get() : nullptr, cbs::kUnreachable, d->data(), visited);
		}
		return { d };
	}
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
		if (!f.d || !in_bounds(t)) return 1e9;
		const std::uint16_t v = (*f.d)[m.idx(t.v())];
		return v == cbs::kUnreachable ? 1e9 : v;
	}

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
		load_items();
		return cons_[cbs::consumable::altar_lock] > 0;
	}

	// ---- memory
	double read_shared(double i)
	{
		if (i < 0 || i >= cbs::kSharedMemory) return 0;
		std::uint8_t v = 0;
		api.read_shared_memory(static_cast<std::int32_t>(i), &v, 1);
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
	const Unit& unit_of(const Option& o) const
	{
		static const Unit none{};
		return o.ui >= 0 && o.ui < static_cast<int>(opt_units_.size()) ? opt_units_[o.ui] : none;
	}
	std::vector<Option> opts_buf, failed_buf; // reused by play_turn (no reallocation per pass)
	KindFilter* filter = nullptr;			   // set by play_turn
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

	void options(std::vector<Option>& out)
	{
		list_options(out);
		extra(190.0 * out.size()); // listing work per option in the bot (copies, checks), fitted on farmer/starter games
	}
	void list_options(std::vector<Option>& out)
	{
		out.clear();
		opt_units_.clear();
		if (api.champ() < 0)
		{
			for (int c = 0; c < cbs::kNumDraftChoices; ++c)
			{
				const int t = choice_to_type(c);
				if (picked(false, t)) continue; // the opponent's picks stay legal (GameRules: Drafting)
				Option o;
				o.kind = PICK, o.champ = t;
				out.push_back(o);
			}
			return;
		}
		const Unit& self_u = me();
		const std::uint32_t st = self_u.state;
		const bool alive_now = st & cbs::state_bit::alive;
		if (alive_now && (st & (cbs::state_bit::recalling | cbs::state_bit::submitting)))
		{
			Option o;
			o.kind = CANCEL;
			out.push_back(o);
			return;
		}
		if (alive_now && (st & cbs::state_bit::teleporting)) return;
		if ((want(BUY) || want(BUY_LOCK)) && can_shop())
		{
			const double g = gold();
			for (int i = 0; i < cbs::kNumItems; ++i)
			{
				const auto& d = cbs::item_design(i);
				if (!d.purchasable || d.cost > g || !want(BUY)) continue;
				// counts in powers of two up to what we can pay: any number in a few passes
				for (int c = 1; c * d.cost <= g; c *= 2)
				{
					Option o;
					o.kind = BUY, o.item = i, o.count = c;
					out.push_back(o);
				}
			}
			if (want(BUY_LOCK) && g >= cbs::consumable_design(cbs::consumable::altar_lock).cost && !has_lock())
			{
				Option o;
				o.kind = BUY_LOCK;
				out.push_back(o);
			}
		}
		if (!alive_now) return;
		const Tile p = self_u.pos;
		if ((st & cbs::state_bit::can_move) && want(MOVE))
		{
			const Bitboard& occ = occupancy();
			for (int dy = -1; dy <= 1; ++dy)
				for (int dx = -1; dx <= 1; ++dx)
				{
					const Vec2 q{ p.x + dx, p.y + dy };
					if ((!dx && !dy) || !m.in_bounds(q) || (tclass(q) & (kWall | kHole | kAltar | kEnemySpawn)) || occ.test(q)) continue;
					Option o;
					o.kind = MOVE, o.tile = { q.x, q.y };
					out.push_back(o);
				}
		}
		if ((st & cbs::state_bit::can_attack) && want(ATTACK))
		{
			for (const Unit& u : enemies())
				if (dist(p, u.pos) <= self_u.attack_range) out.push_back(target_option(ATTACK, u));
			for (const Unit& u : camps())
				if (dist(p, u.pos) <= self_u.attack_range) out.push_back(target_option(ATTACK, u));
		}
		if ((st & cbs::state_bit::can_cast) && want(CAST))
			for (int s = 0; s < 2; ++s)
			{
				if (!slot_ready(s)) continue;
				const auto& pr = props(s);
				const double reach = pr.range + 0.5;
				auto add_units = [&](const Units& us) {
					for (const Unit& u : us)
						if (dist(p, u.pos) <= reach)
						{
							Option o = target_option(CAST, u);
							o.slot = s;
							out.push_back(o);
						}
				};
				if (pr.targets & cbs::target::enemies) add_units(enemies());
				if (pr.targets & cbs::target::camps) add_units(camps());
				if (pr.targets & cbs::target::allies) add_units(allies());
				if (pr.targets & cbs::target::self)
				{
					Option o = target_option(CAST, self_u);
					o.slot = s;
					out.push_back(o);
				}
				if (pr.targets & cbs::target::ground)
				{
					const int r = static_cast<int>(std::floor(pr.range));
					for (int dy = -r; dy <= r; ++dy)
						for (int dx = -r; dx <= r; ++dx)
						{
							const Vec2 q{ p.x + dx, p.y + dy };
							if ((!dx && !dy) || !m.in_bounds(q) || (tclass(q) & kWall)) continue;
							Option o;
							o.kind = CAST, o.slot = s, o.tile = { q.x, q.y };
							out.push_back(o);
						}
				}
			}
		{
			cbs::WardResources wr{};
			api.champion_wards(self(), &wr);
			if (wr.charges > 0 && want(WARD))
			{
				const int r = static_cast<int>(cbs::settings().ward_placement_radius);
				for (int dy = -r; dy <= r; ++dy)
					for (int dx = -r; dx <= r; ++dx)
					{
						const Vec2 q{ p.x + dx, p.y + dy };
						if (!m.in_bounds(q) || (tclass(q) & kWall)) continue;
						Option o;
						o.kind = WARD, o.tile = { q.x, q.y };
						out.push_back(o);
					}
			}
		}
		if (!(tclass(p.v()) & kMySpawn) && want(RECALL))
		{
			Option o;
			o.kind = RECALL;
			out.push_back(o);
		}
		const bool lock = has_lock();
		const double g = gems();
		if ((g > 0 && want(TRIBUTE)) || (lock && want(LOCK)))
		{
			for (Vec2 a : m.altar_list)
			{
				const int d = cbs::chebyshev(a, p.v());
				// at an enemy-locked altar a tribute is legal too: it hits the lock (5 hits clear it)
				if (g > 0 && d <= cbs::settings().submit_gems_range)
				{
					Option o;
					o.kind = TRIBUTE, o.tile = { a.x, a.y };
					out.push_back(o);
				}
				if (lock && d <= 2)
				{
					Option o;
					o.kind = LOCK, o.tile = { a.x, a.y };
					out.push_back(o);
				}
			}
		}
	}

	// Do one option; false if the engine refused it (it is then skipped for the rest of the turn).
	bool execute(const Option& o)
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
	Units enemies_, allies_, camps_, opt_units_;
	double gems_ = 0, gold_ = 0;
	bool have_me_ = false, have_enemies_ = false, have_allies_ = false, have_camps_ = false, have_gems_ = false, have_gold_ = false,
		 have_occ_ = false, have_items_ = false;
	Bitboard occ_;
	std::uint32_t items_[cbs::kNumItems] = {}, cons_[cbs::kNumConsumables] = {};
	cbs::AbilityProps props_[2] = {};
	std::uint64_t props_pass_[2] = { 0, 0 };
	std::shared_ptr<const Bitboard> altars_, walls_, bushes_, holes_, myspawn_, espawn_, campsp_;
	std::shared_ptr<const Bitboard> type_sp_[static_cast<int>(cbs::CampType::count)];
	std::vector<int> camp_at_;
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
	Option target_option(int kind, const Unit& u)
	{
		Option o;
		o.kind = kind, o.tile = u.pos, o.ukind = u.kind, o.uh = u.h, o.ui = static_cast<int>(opt_units_.size());
		opt_units_.push_back(u);
		return o;
	}
	// Static terrain class per tile, as plain bytes: one host bitboard test costs ~120 fuel in the bot.
	enum : std::uint8_t { kWall = 1, kHole = 2, kAltar = 4, kEnemySpawn = 8, kMySpawn = 16 };
	std::vector<std::uint8_t> cls_;
	std::uint8_t tclass(Vec2 q)
	{
		if (cls_.empty())
		{
			cls_.assign(static_cast<std::size_t>(m.W) * m.H, 0);
			auto mark = [&](const Bitboard& b, std::uint8_t bit) { b.for_each_unordered(m.H, [&](int x, int y) { cls_[y * m.W + x] |= bit; }); };
			mark(m.walls, kWall), mark(m.holes, kHole), mark(m.altars, kAltar);
			mark(m.spawn_mask[1 - api.team()], kEnemySpawn), mark(m.spawn_mask[api.team()], kMySpawn);
		}
		return cls_[m.idx(q)];
	}
	std::vector<std::shared_ptr<const Bitboard>> group_tiles_;
	const Bitboard& occupancy()
	{
		if (!have_occ_)
		{
			Bitboard t;
			api.ally_occupancy(occ_);
			api.enemy_occupancy(t);
			occ_ |= t;
			api.camp_occupancy(t, 0);
			occ_ |= t;
			have_occ_ = true;
		}
		return occ_;
	}
	void load_items()
	{
		if (have_items_) return;
		std::fill(std::begin(items_), std::end(items_), 0u);
		std::fill(std::begin(cons_), std::end(cons_), 0u);
		api.champion_items(self(), items_);
		api.champion_consumables(self(), cons_);
		have_items_ = true;
		extra(260);
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
	bool consider_kind(int) override { return true; }
	bool has_consider() const override { return false; }
	Ctx& X;
};

using MakeGenes = GenesBase* (*)(Ctx&);

// One turn of the fixed loop. Returns the number of actions taken.
inline int play_turn(Ctx& X, GenesBase& g, int max_passes = 16)
{
	std::vector<Option>& opts = X.opts_buf;
	std::vector<Option>& failed = X.failed_buf;
	failed.clear();
	if (opts.capacity() < 256) opts.reserve(256);
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
	X.new_pass();
	if (!draft) g.run_update();
	int acted = 0;
	for (int pass = 0; pass < max_passes; ++pass)
	{
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
			const double s = g.score_option(o);
			if (!best || s > bs) best = &o, bs = s;
		}
		PROF_MARK(f_score);
		// the draft must pick; everything else needs a positive score
		if (!best || (!draft && bs <= 0)) break;
		const bool ok = X.execute(*best);
		PROF_MARK(f_exec);
		if (std::getenv("GENOME_TRACE"))
			std::fprintf(stderr, "@@G r%d t%d c%d pos %d,%d kind %d score %.2f tile %d,%d unit %d:%u slot %d item %d champ %d ok %d of %zu camps %zu st %u ar %d mind %.0f gold %.0f shop %d\n",
						 static_cast<int>(X.round()), X.api.team(), X.api.champ(), X.me().pos.x, X.me().pos.y, best->kind, bs, best->tile.x,
						 best->tile.y, best->ukind, best->uh, best->slot, best->item, best->champ, ok, opts.size(), X.camps().size(), X.me().state, X.me().attack_range, [&] { double d = 1e9; for (const Unit& u : X.camps()) d = std::min(d, X.dist(X.me().pos, u.pos)); return d; }(), X.gold(), (int)X.can_shop());
		if (ok) ++acted;
		else failed.push_back(*best);
		if (fuel_trace >= 0 && X.api.spent > fuel_trace)
			std::fprintf(stderr, "@@FP r%d t%d c%d pass %d spent %lld kind %d ok %d options %zu\n", static_cast<int>(X.round()), X.api.team(),
						 X.api.champ(), pass, static_cast<long long>(X.api.spent), best->kind, ok ? 1 : 0, opts.size());
		if (draft) break;
	}
#ifdef GENOME_PROF
	if (!draft && X.api.champ() == 0 && static_cast<int>(X.round()) % 500 == 0)
		for (const auto& gs : gene_stats)
			if (gs.name) std::printf("@@GENE r%d %s calls %lld fuel %lld per %.0f\n", static_cast<int>(X.round()), gs.name, gs.calls, gs.fuel, gs.calls ? double(gs.fuel) / gs.calls : 0.0);
	if (!draft && (GENOME_PROF_EVERY <= 1 || static_cast<int>(X.round()) % GENOME_PROF_EVERY == 1))
		std::printf("@@P t%d r%d c%d passes %d opts %d options %lld score %lld exec %lld left %lld ops %lld turn %lld\n", X.api.team(), static_cast<int>(X.round()),
					X.api.champ(), npass, nopts, static_cast<long long>(f_opt), static_cast<long long>(f_score),
					static_cast<long long>(f_exec), static_cast<long long>(X.api.fuel_remaining()), X.ops - ops0,
					static_cast<long long>(start - X.api.fuel_remaining()));
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
