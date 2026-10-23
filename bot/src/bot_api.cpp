// Bot-side implementation of cbs::Api: the same class the simulator uses, backed by the
// engine's raw host imports (sdk/cpp/imports.h) instead of a simulated Game. This lets the
// policy interpreter (interp/src/policy.cpp) run unchanged in the real bot.
//
// Notes:
// - cbs::Bitboard is the bot's host-backed version (bot/bitboard_host.h), already in the
//   engine's chunked layout, so boards go to and from the imports without conversion.
// - distance_field() uses the host primitive (30-200x cheaper than cbs code compiled to
//   wasm, docs/FUEL.md) and, to stay cheap, only materialises distances on tiles within
//   Chebyshev 2 of this champion and on the `dests` tiles; every other entry reads as
//   unreachable (`visited` is the engine's). That covers every read the interpreter makes.
// - Charges are not enforced here: the engine meters real fuel.
#include <cambc.h>
#include <algorithm>
#include <cstring>
#include <cstdio>
#include "cbs/api.h"
#include "bot_api.h"

namespace cbs
{
namespace
{
using namespace cambc::detail;

const metadata& md = hostbb::md;
constexpr int kFieldWords = 13 * 13 * 64; // u16 entries

Err E(std::int32_t rc) { return static_cast<Err>(rc); }
} // namespace

// The bot only needs the map from Game (sim/src/game.cpp is not linked).
Game::Game(std::shared_ptr<const Map> map) : map_(std::move(map)) {}

// ---- static map ------------------------------------------------------------

std::shared_ptr<const Map> build_map_from_engine()
{
	hostbb::init();
	auto m = std::make_shared<Map>();
	m->W = md.width;
	m->H = md.height;
	Bitboard* masks[4] = { &m->walls, &m->bushes, &m->holes, &m->altars };
	for (int k = 0; k < 4; ++k)
		if (sdk_bc_map_mask(k, masks[k]->w) != 0) masks[k]->clear();
	for (int t = 0; t < 2; ++t)
	{
		aabb a{};
		sdk_spawn_region(t, &a);
		m->spawn[t] = { a.min_x, a.min_y, a.max_x, a.max_y };
		for (int y = a.min_y; y < a.max_y; ++y)
			for (int x = a.min_x; x < a.max_x; ++x) m->spawn_mask[t].set(x, y);
	}
	m->camp_at.assign(static_cast<std::size_t>(m->W) * m->H, -1);
	std::uint32_t ng = 0;
	sdk_map_num_camp_groups(&ng);
	m->groups.resize(ng);
	std::vector<std::uint32_t> hs(512);
	for (std::uint32_t g = 0; g < ng; ++g)
	{
		std::uint32_t n = 0;
		if (sdk_map_camp_group_camps(g, hs.data(), static_cast<std::uint32_t>(hs.size()), &n) != 0) continue;
		for (std::uint32_t i = 0; i < n; ++i)
		{
			const std::uint32_t h = hs[i];
			camp_info ci{};
			if (sdk_map_camp_info(h, &ci) != 0) continue;
			if (m->camps.size() <= h) m->camps.resize(h + 1);
			m->camps[h] = { static_cast<CampType>(ci.type), { ci.x, ci.y }, static_cast<int>(g) };
			m->groups[g].camps.push_back(static_cast<int>(h));
			if (m->in_bounds({ ci.x, ci.y })) m->camp_at[m->idx({ ci.x, ci.y })] = static_cast<int>(h);
		}
		std::sort(m->groups[g].camps.begin(), m->groups[g].camps.end());
	}
	m->altars.for_each(m->H, [&](int x, int y) { m->altar_list.push_back({ x, y }); });
	return m;
}

// ---- Api ----------------------------------------------------------------------

Api::Api(Game& g, int team, int champ, const PriceTable* prices) : g_(g), team_(team), champ_(champ), prices_(prices) {}

std::int32_t Api::my_champion() { return champ_; }
std::int32_t Api::my_team() { return team_; }

Err Api::champion(std::uint32_t h, ChampionInfo* out)
{
	static_assert(sizeof(ChampionInfo) == sizeof(champion_info));
	champion_info ci{};
	const std::int32_t rc = sdk_champion(h, &ci);
	std::memcpy(out, &ci, sizeof ci);
	return E(rc);
}
Err Api::allies(std::uint32_t* out, std::uint32_t cap, std::uint32_t* count) { return E(sdk_allies(out, cap, count)); }
Err Api::enemies(std::uint32_t* out, std::uint32_t cap, std::uint32_t* count) { return E(sdk_enemies(out, cap, count)); }
Err Api::champion_gems(std::uint32_t h, std::uint32_t* out) { return E(sdk_champion_gems(h, out)); }
Err Api::champion_gold(std::uint32_t h, std::uint32_t* out) { return E(sdk_champion_gold(h, out)); }
Err Api::champion_cooldown(std::uint32_t h, std::uint32_t slot, std::int32_t* out) { return E(sdk_champion_cooldown(h, slot, out)); }
Err Api::champion_consumables(std::uint32_t h, std::uint32_t* out) { return E(sdk_champion_consumables(h, out)); }
Err Api::champion_ability_props(std::uint32_t h, std::uint32_t slot, AbilityProps* out)
{
	ability_props ap{};
	const std::int32_t rc = sdk_champion_ability_props(h, slot, &ap);
	*out = {};
	out->kind = ap.kind;
	out->cooldown = ap.cooldown;
	out->max_charges = ap.max_charges;
	out->targets = ap.targets;
	out->attributes = ap.attributes;
	return E(rc);
}
Err Api::camp(std::uint32_t h, CampRecord* out)
{
	static_assert(sizeof(CampRecord) == sizeof(cambc::detail::camp_state));
	cambc::detail::camp_state cs{};
	const std::int32_t rc = sdk_camp(h, &cs);
	std::memcpy(out, &cs, sizeof cs);
	return E(rc);
}
Err Api::camp_group_state(std::uint32_t g, std::uint32_t* out) { return E(sdk_camp_group_state(g, out)); }
Err Api::altar_locks(AltarLockRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	static_assert(sizeof(AltarLockRecord) == sizeof(altar_lock_info));
	return E(sdk_altar_locks(reinterpret_cast<altar_lock_info*>(out), cap, count));
}
Err Api::submitted_gems(std::uint32_t team, std::uint32_t* out) { return E(sdk_bc_submitted_gems(team, out)); }
Err Api::round_number(std::uint32_t* out) { return E(sdk_bc_round_number(out)); }

Err Api::ally_occupancy(Bitboard& out)
{
	const Err e = E(sdk_ally_occupancy(out.w));
	if (e != Err::success) out.clear();
	return e;
}
Err Api::enemy_occupancy(Bitboard& out)
{
	const Err e = E(sdk_enemy_occupancy(out.w));
	if (e != Err::success) out.clear();
	return e;
}
Err Api::camp_occupancy(Bitboard& out, int which)
{
	const std::int32_t rc = which == 1 ? sdk_awake_camp_occupancy(out.w) : which == 2 ? sdk_asleep_camp_occupancy(out.w) : sdk_camp_occupancy(out.w);
	if (rc != 0) out.clear();
	return E(rc);
}

Err Api::read_shared_memory(std::int32_t off, std::uint8_t* out, std::uint32_t n) { return E(sdk_read_shared_memory(off, out, n)); }
Err Api::write_shared_memory(std::int32_t off, const std::uint8_t* in, std::uint32_t n) { return E(sdk_write_shared_memory(off, in, n)); }
Err Api::read_draft_memory(std::int32_t off, std::uint8_t* out, std::uint32_t n) { return E(sdk_read_draft_memory(off, out, n)); }
Err Api::submit_draft_memory(const std::uint8_t* in, std::uint32_t n) { return E(sdk_bc_submit_draft_memory(in, n)); }

Err Api::move_to(Vec2 p, std::int32_t* ok) { return E(sdk_move_to(p.x, p.y, ok)); }
Err Api::attack(std::uint32_t kind, std::uint32_t h) { return E(sdk_attack(kind, h)); }
Err Api::cast(std::uint32_t slot, std::uint32_t kind, std::uint32_t h, Vec2 p, std::int32_t* ok) { return E(sdk_cast(slot, kind, h, p.x, p.y, ok)); }
Err Api::buy_item(std::uint32_t item, std::uint32_t count) { return E(sdk_buy_item(item, count)); }
Err Api::buy_consumable(std::uint32_t type) { return E(sdk_buy_consumable(type)); }
Err Api::use_consumable(std::int32_t type, Vec2 p, std::int32_t* ok)
{
	return E(sdk_use_consumable(static_cast<std::uint32_t>(type), p.x, p.y, ok));
}
Err Api::recall() { return E(sdk_recall()); }
Err Api::submit_gems(Vec2 altar) { return E(sdk_submit_gems(altar.x, altar.y)); }
Err Api::place_ward(Vec2 p, std::int32_t* ok) { return E(sdk_place_ward(p.x, p.y, ok)); }
Err Api::set_priority(std::int32_t p) { return E(sdk_set_priority(p)); }

Err Api::draft_get(std::int32_t team, std::uint32_t round, std::int32_t* out) { return E(sdk_draft_get(team, round, out)); }
Err Api::draft_champion(std::int32_t choice) { return E(sdk_draft_champion(choice)); }

// ---- distance fields ----------------------------------------------------------
//
// Host fields cost 16 * chunks + chunks per BFS layer (2.7k + 169 per layer on 100x100), and
// the host's ComputeTo runs until *every* dest is reached. Callers only need the field up to
// the nearest dest (the simulator's semantics), so requests are narrowed and memoised:
//
// - If the champion's tile is a dest, searching to it alone gives every value up to the
//   nearest dest (which is no farther).
// - A field depends only on (walls, roots, max_distance) up to its stopping layer L: a BFS
//   stopped at L holds the exact distance of every tile at most L away. A request with the
//   same roots is answered from a cached field when the walls are identical and its own
//   stopping layer S (its nearest dest) is at most L (or the cached search ran to completion);
//   or, for requests whose dests lie in the 5x5 box around the champion (move_towards,
//   dash_towards, nearest_by_walk's first step), when the walls differ only in tiles that
//   provably cannot change any box distance (box_unaffected) and S <= L.
//   Values beyond S read as unreachable, exactly as a search stopped at S leaves them.
// Typical hits: fields rooted at a fixed goal (a camp tile, the candidate set) on consecutive
// turns, since the champion's own tile is never a wall and units elsewhere rarely matter.
//
// BOT_VERIFY checks every answer against a fresh host search (debug only).
namespace
{
struct FieldSlot
{
	Bitboard walls, roots;
	alignas(16) std::uint16_t field[kFieldWords];
	int depth = -1;		   // last layer expanded; -1 = empty slot
	bool complete = false; // the search ran out of tiles (every reachable tile is exact)
	int maxd = 0;
	std::uint64_t used = 0;
};
constexpr int kSlots = 6;
FieldSlot* slots = nullptr;
std::uint64_t slot_clock = 0;
alignas(16) std::uint64_t delta_w[hostbb::kWords];
hostbb::Pos delta_pos[64];
#ifdef BOT_VERIFY
alignas(16) std::uint16_t verify_field[kFieldWords];
long verify_checks = 0, verify_fails = 0;
#endif

inline int fidx(int x, int y) { return ((y >> 3) * static_cast<int>(md.chunked_width) + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7); }
inline int cheb(int x, int y, Vec2 p) { return std::max(std::abs(x - p.x), std::abs(y - p.y)); }

// Can the walls of `sl` be replaced by `walls` without changing the distance of any tile in
// the 5x5 box around `me` that the cached field knows (<= L), or making any other box tile
// closer than L + 1? Let A be the tiles that became walls and R the tiles that opened.
//  - An old shortest path to q passes through a in A only if d(a) + cheb(a, q) <= d(q) <= L.
//    So d(a) + cheb(a, me) - 2 > L rules a out for every q in the box: old paths survive.
//  - A new path that uses R enters its first r in R from a neighbour n reached without R,
//    so it is at least min_n d(n) + 1 + cheb(r, q) long. min_n d(n) + 1 + cheb(r, me) - 2
//    >= L + 1 rules every such path out of beating the old value (or L + 1).
// Unknown distances (beyond L) are taken as L + 1: a lower bound, so the test stays sound.
bool box_unaffected(const FieldSlot& sl, const Bitboard& walls, const Bitboard& roots, Vec2 me, int W, int H)
{
	sdk_Bitboard_Xor(sl.walls.w, walls.w, delta_w);
	std::uint32_t n = 0;
	sdk_Bitboard_GetSetBits(delta_w, delta_pos, 64, &n);
	if (n > 64) return false;
	const int L = sl.depth;
	auto d = [&](int x, int y) {
		const int v = sl.field[fidx(x, y)];
		return v <= L ? v : L + 1;
	};
	for (std::uint32_t i = 0; i < n; ++i)
	{
		const int x = delta_pos[i].x, y = delta_pos[i].y;
		if (roots.test(x, y)) return false;
		const int c = cheb(x, y, me);
		if (walls.test(x, y))
		{
			if (d(x, y) + c - 2 <= L) return false;
		}
		else
		{
			int lb = 0x10000;
			for (int yy = std::max(0, y - 1); yy <= std::min(H - 1, y + 1); ++yy)
				for (int xx = std::max(0, x - 1); xx <= std::min(W - 1, x + 1); ++xx)
					if ((xx != x || yy != y) && !sl.walls.test(xx, yy)) lb = std::min(lb, d(xx, yy) + 1);
			if (lb + c - 2 < L + 1) return false;
		}
	}
	return true;
}

struct FieldAnswer
{
	const std::uint16_t* f;
	int limit; // values above this read as unreachable (-1: none)
	int count; // the stopping layer (expansion count of an equivalent fresh search)
	std::uint16_t at(int x, int y) const
	{
		const std::uint16_t v = f[fidx(x, y)];
		return limit >= 0 && v > limit ? kUnreachable : v;
	}
};

// `me` is the champion's tile (have_me false for the draft bot).
FieldAnswer field_query(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, bool have_me, Vec2 me,
						int W, int H)
{
	if (!slots) slots = new FieldSlot[kSlots];
	const auto maxd = static_cast<std::uint16_t>(std::clamp(max_distance, 0, 0xFFFF));
	// Nearest dest in a cached field (0x10000 if none within its depth); -1 if need_box and
	// some dest lies outside the box around the champion.
	auto nearest = [&](const FieldSlot& sl, bool need_box) {
		int best = 0x10000;
		const int L = sl.depth;
		dests->for_each_unordered(H, [&](int x, int y) {
			if (best < 0) return;
			if (need_box && cheb(x, y, me) > 2)
			{
				best = -1;
				return;
			}
			const int v = sl.field[fidx(x, y)];
			if (v <= L && v < best) best = v;
		});
		return best;
	};
	FieldAnswer ans{ nullptr, -1, 0 };
	FieldSlot* use = nullptr;
	for (int i = 0; i < kSlots && !use; ++i)
	{
		FieldSlot& sl = slots[i];
		if (sl.depth < 0 || sl.maxd != maxd || !(sl.roots == roots)) continue;
		if (sl.walls == walls)
		{
			if (!dests)
			{
				if (sl.complete) use = &sl;
				continue;
			}
			const int best = nearest(sl, false);
			if (best <= sl.depth) use = &sl, ans.limit = best;
			else if (sl.complete) use = &sl; // no dest reachable: a fresh search would run to completion
		}
		else if (dests && have_me)
		{
			const int best = nearest(sl, true);
			if (best >= 0 && best <= sl.depth && box_unaffected(sl, walls, roots, me, W, H)) use = &sl, ans.limit = best;
		}
	}
	if (use)
		ans.count = ans.limit >= 0 ? ans.limit : use->depth;
	else
	{
		use = &slots[0];
		for (int i = 1; i < kSlots; ++i)
			if (slots[i].used < use->used) use = &slots[i];
		Bitboard visited, me_only;
		const Bitboard* sd = dests;
		if (dests && have_me && dests->test(me))
		{
			me_only.set(me);
			sd = &me_only;
		}
		std::uint16_t count = 0;
		if (sd)
			sdk_DistanceField_ComputeToWithExpansionCount(walls.w, roots.w, sd->w, visited.w, use->field, maxd, &count);
		else
			sdk_DistanceField_ComputeWithExpansionCount(walls.w, roots.w, visited.w, use->field, maxd, &count);
		use->walls = walls;
		use->roots = roots;
		use->maxd = maxd;
		use->depth = count;
		// Stopped early only if a dest was reached (visited = every reached tile) or at maxd.
		bool reached = false;
		if (sd)
		{
			visited &= *sd;
			reached = visited.any(H);
		}
		use->complete = !reached && count < maxd;
		if (dests)
		{
			const int best = nearest(*use, false);
			if (best <= use->depth) ans.limit = best;
		}
		ans.count = ans.limit >= 0 ? ans.limit : count;
	}
	use->used = ++slot_clock;
	ans.f = use->field;
#ifdef BOT_VERIFY
	{
		// A fresh search with the simulator's semantics (stop at the first layer touching a
		// dest) must agree on every tile it reached.
		Bitboard v;
		std::uint16_t c = 0;
		if (dests)
			sdk_DistanceField_ComputeToWithExpansionCount(walls.w, roots.w, dests->w, v.w, verify_field, maxd, &c);
		else
			sdk_DistanceField_ComputeWithExpansionCount(walls.w, roots.w, v.w, verify_field, maxd, &c);
		int stop = 0x10000;
		if (dests)
			dests->for_each_unordered(H, [&](int x, int y) { stop = std::min<int>(stop, verify_field[fidx(x, y)]); });
		// The contract covers the dests and the 5x5 box around the champion.
		int bad = 0;
		auto check = [&](int x, int y) {
			int want = verify_field[fidx(x, y)];
			if (stop < 0x10000 && want > stop) want = kUnreachable;
			bad += ans.at(x, y) != want;
		};
		if (have_me)
			for (int y = std::max(0, me.y - 2); y <= std::min(H - 1, me.y + 2); ++y)
				for (int x = std::max(0, me.x - 2); x <= std::min(W - 1, me.x + 2); ++x) check(x, y);
		if (dests) dests->for_each_unordered(H, check);
		if (++verify_checks % 2000 == 0) std::printf("@@VERIFY checks=%ld fails=%ld\n", verify_checks, verify_fails);
		if (bad)
		{
			++verify_fails;
			std::printf("@@VERIFY field mismatch tiles=%d limit=%d count=%d stop=%d\n", bad, ans.limit, ans.count, stop);
		}
	}
#endif
	return ans;
}
} // namespace

int Api::distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, std::uint16_t* dist,
						Bitboard& visited)
{
	const int W = g_.map().W, H = g_.map().H;
	champion_info ci{};
	const bool have_me = champ_ >= 0 && sdk_champion(static_cast<std::uint32_t>(champ_), &ci) == 0;
	const Vec2 me{ ci.x, ci.y };
	const FieldAnswer ans = field_query(walls, roots, dests, max_distance, have_me, me, W, H);
	// Only the dests and the 5x5 box around the champion are written: those are the only
	// entries the interpreter reads after a call (every other entry is unspecified, and
	// `visited` is not maintained: no caller reads it).
	auto put = [&](int x, int y) { dist[y * W + x] = ans.at(x, y); };
	if (have_me)
		for (int y = std::max(0, me.y - 2); y <= std::min(H - 1, me.y + 2); ++y)
			for (int x = std::max(0, me.x - 2); x <= std::min(W - 1, me.x + 2); ++x) put(x, y);
	if (dests) dests->for_each_unordered(H, put);
	return ans.count;
}

// Same answer as the simulator's (origin-rooted search, nearest candidate, ties row-major),
// computed as: D = distance to the nearest candidate from a search rooted at the candidates
// with `origin` as its only dest (distances are symmetric; rooted at a fixed set, so the
// memo usually answers it on later turns), then the candidates within D of `origin`, which
// are all exactly D away, and the first of them in row-major order.
bool Api::nearest_by_walk(const Bitboard& walls, Vec2 origin, const Bitboard& cand, Vec2& out)
{
	const int W = g_.map().W, H = g_.map().H;
	champion_info ci{};
	const bool have_me = champ_ >= 0 && sdk_champion(static_cast<std::uint32_t>(champ_), &ci) == 0 && ci.x == origin.x && ci.y == origin.y;
	Bitboard o;
	o.set(origin);
	const FieldAnswer ans = field_query(walls, cand, &o, kUnreachable, have_me, origin, W, H);
	const int D = ans.at(origin.x, origin.y);
	bool found = false;
	if (D != kUnreachable)
	{
		// Candidates within D: a reachable mask (~190 + 1.7 per tile reached) or a field
		// rooted at origin cut at D (16 * chunks + D * chunks), whichever is expected cheaper.
		const int chunks = static_cast<int>(md.chunked_width * md.chunked_height);
		const long area = std::min<long>(static_cast<long>(W) * H, static_cast<long>(2 * D + 1) * (2 * D + 1));
		Bitboard near;
		if (190 + area * 17 / 10 <= (16 + D) * chunks)
		{
			sdk_Bitboard_ReachableMask(walls.w, origin.x, origin.y, near.w, D);
			near &= cand;
			found = near.first(H, out);
		}
		else
		{
			const FieldAnswer a2 = field_query(walls, o, &cand, D, have_me, origin, W, H);
			Vec2 best{ W, H };
			cand.for_each_unordered(H, [&](int x, int y) {
				if (a2.at(x, y) <= D && (y < best.y || (y == best.y && x < best.x))) best = { x, y };
			});
			found = best.y < H;
			if (found) out = best;
		}
	}
#ifdef BOT_VERIFY
	{
		Bitboard v;
		std::uint16_t c = 0;
		sdk_DistanceField_ComputeToWithExpansionCount(walls.w, o.w, cand.w, v.w, verify_field, kUnreachable, &c);
		std::uint16_t bd = kUnreachable;
		Vec2 want{ -1, -1 };
		cand.for_each(H, [&](int x, int y) {
			if (verify_field[fidx(x, y)] < bd) bd = verify_field[fidx(x, y)], want = { x, y };
		});
		if (++verify_checks % 2000 == 0) std::printf("@@VERIFY checks=%ld fails=%ld\n", verify_checks, verify_fails);
		if (found != (want.x >= 0) || (found && !(out == want)))
		{
			++verify_fails;
			std::printf("@@VERIFY nearest mismatch got %d,%d (%d) want %d,%d D=%d\n", found ? out.x : -1, found ? out.y : -1, found, want.x, want.y, D);
		}
	}
#endif
	return found;
}

} // namespace cbs
