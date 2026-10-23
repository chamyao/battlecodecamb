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
	std::shared_ptr<Map> m(new Map); // default-init: make_shared would zero all ~14 KB first (1 fuel/byte)
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
	// Map::camp_at is left empty: nothing in the bot reads it (filling 10k ints costs 40k fuel).
	// The whole static camp layout in one call (per group: id, gold, gems, max respawn, camp
	// count, then per camp: id, design, x, y); per-camp queries cost ~300 fuel each here.
	std::uint32_t nw = 0;
	sdk_map_camp_layout(nullptr, 0, &nw);
	std::vector<std::uint32_t> lay(nw);
	if (nw && sdk_map_camp_layout(lay.data(), nw, &nw) == 0)
	{
		std::uint32_t ng = 0, nc = 0;
		for (std::uint32_t i = 0; i + 5 <= lay.size(); i += 5 + 4 * lay[i + 4])
		{
			ng = std::max(ng, lay[i] + 1);
			for (std::uint32_t k = 0; k < lay[i + 4]; ++k) nc = std::max(nc, lay[i + 5 + 4 * k] + 1);
		}
		m->groups.resize(ng);
		m->camps.resize(nc);
		for (std::uint32_t i = 0; i + 5 <= lay.size(); i += 5 + 4 * lay[i + 4])
		{
			const std::uint32_t g = lay[i];
			for (std::uint32_t k = 0; k < lay[i + 4]; ++k)
			{
				const std::uint32_t* c = &lay[i + 5 + 4 * k];
				m->camps[c[0]] = { static_cast<CampType>(c[1]), { static_cast<int>(c[2]), static_cast<int>(c[3]) }, static_cast<int>(g) };
				m->groups[g].camps.push_back(static_cast<int>(c[0]));
			}
			auto& v = m->groups[g].camps;
			for (std::size_t a = 1; a < v.size(); ++a)
				for (std::size_t b = a; b > 0 && v[b - 1] > v[b]; --b) std::swap(v[b - 1], v[b]);
		}
	}
#ifdef BOT_VERIFY
	{
		std::uint32_t ng = 0;
		sdk_map_num_camp_groups(&ng);
		bool ok = ng == m->groups.size();
		std::vector<std::uint32_t> hs(512);
		for (std::uint32_t g = 0; g < ng && ok; ++g)
		{
			std::uint32_t n = 0;
			sdk_map_camp_group_camps(g, hs.data(), 512, &n);
			std::vector<int> want(hs.begin(), hs.begin() + n);
			std::sort(want.begin(), want.end());
			ok &= want == m->groups[g].camps;
			for (std::uint32_t i = 0; i < n && ok; ++i)
			{
				camp_info ci{};
				sdk_map_camp_info(hs[i], &ci);
				const auto& c = m->camps[hs[i]];
				ok &= c.pos.x == ci.x && c.pos.y == ci.y && static_cast<int>(c.type) == ci.type && c.group == static_cast<int>(g);
			}
		}
		std::printf("@@VERIFY camp layout %s (%zu groups, %zu camps)\n", ok ? "ok" : "MISMATCH", m->groups.size(), m->camps.size());
	}
#endif
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
// Visible camps are exactly the camp-occupied tiles in vision: look their handles up there
// (~10 fuel per visible camp) instead of querying every camp on the map.
void Api::visible_camps(std::vector<std::uint32_t>& out)
{
	out.clear();
#ifdef BOT_REFERENCE
	for (std::uint32_t c = 0; c < g_.map().camps.size(); ++c)
	{
		cambc::detail::camp_state cs{};
		if (sdk_camp(c, &cs) == 0 && cs.health > 0) out.push_back(c);
	}
	return;
#endif
	Bitboard occ;
	if (sdk_camp_occupancy(occ.w) == 0)
		occ.for_each_unordered(g_.map().H, [&](int x, int y) {
			std::uint32_t h = 0;
			cambc::detail::camp_state cs{};
			if (sdk_camp_at(x, y, &h) == 0 && sdk_camp(h, &cs) == 0 && cs.health > 0) out.push_back(h);
		});
	for (std::size_t i = 1; i < out.size(); ++i)
		for (std::size_t j = i; j > 0 && out[j - 1] > out[j]; --j) std::swap(out[j - 1], out[j]);
#ifdef BOT_VERIFY
	std::vector<std::uint32_t> want;
	for (std::uint32_t c = 0; c < g_.map().camps.size(); ++c)
	{
		cambc::detail::camp_state cs{};
		if (sdk_camp(c, &cs) == 0 && cs.health > 0) want.push_back(c);
	}
	if (want != out) std::printf("@@VERIFY visible_camps mismatch got %zu want %zu\n", out.size(), want.size());
#endif
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

#ifdef BOT_PROF2
} // namespace cbs
long long bot_prof[8];
namespace cbs
{
#define PROF_T sdk_fuel_remaining()
#endif
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
constexpr int kSlots = 4;
FieldSlot* slots = nullptr;
std::uint64_t slot_clock = 0;
alignas(16) std::uint64_t delta_w[hostbb::kWords];
constexpr std::uint32_t kMaxDelta = 24;
hostbb::Pos delta_pos[kMaxDim * kMaxDim];
#ifdef BOT_VERIFY
alignas(16) std::uint16_t verify_field[kFieldWords];
long verify_checks = 0, verify_fails = 0;
#endif

inline int fidx(int x, int y) { return ((y >> 3) * static_cast<int>(md.chunked_width) + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7); }
inline int cheb(int x, int y, Vec2 p) { return std::max(std::abs(x - p.x), std::abs(y - p.y)); }

// Can the walls of `sl` be replaced by `walls` for a request that stops at layer S <= L (its
// nearest dest) and is read only on Q, the open tiles within Chebyshev `qr` of `me` (all its
// dests are in Q)? Every q in Q must keep its cached distance D_q if D_q <= S, and stay
// farther than S otherwise. (Tiles that are walls in the request read as unreachable, which
// is exact: see FieldAnswer.) Let A be the tiles that became walls and R those that opened.
//  - An old shortest path to q passes through a in A only if d(a) + cheb(a, q) <= D_q. If no
//    a qualifies, an old shortest path survives, so q gets no farther. (Walls only removed
//    paths, so tiles farther than S stay so.)
//  - A new path that uses R enters its first r in R from a neighbour n reached without R, so
//    it is at least lb(r) + cheb(r, q) long, lb(r) = min_n d(n) + 1 over old-open n. If that
//    is at least D_q (or S + 1 for tiles farther than S), q gets no closer.
// Unknown distances (beyond L) are taken as L + 1: a lower bound, so the test stays sound.
bool box_unaffected_(const FieldSlot& sl, const Bitboard& walls, const Bitboard& roots, Vec2 me, int S, int qr, int W, int H);
#ifdef BOT_DF_PROFILE
std::uint32_t dbg_n = 0;
#endif
bool box_unaffected(const FieldSlot& sl, const Bitboard& walls, const Bitboard& roots, Vec2 me, int S, int qr, int W, int H)
{
#ifdef BOT_DF_PROFILE
	const long long f0 = sdk_fuel_remaining();
	dbg_n = 0;
	const bool r = box_unaffected_(sl, walls, roots, me, S, qr, W, H);
	std::printf("@@BOX n=%u ok=%d fuel=%lld S=%d L=%d qr=%d\n", dbg_n, r, f0 - (long long)sdk_fuel_remaining(), S, sl.depth, qr);
	return r;
#else
	return box_unaffected_(sl, walls, roots, me, S, qr, W, H);
#endif
}
bool box_unaffected_(const FieldSlot& sl, const Bitboard& walls, const Bitboard& roots, Vec2 me, int S, int qr, int W, int H)
{
#ifdef BOT_PROF2
	struct BT { long long f0 = PROF_T; ~BT() { bot_prof[7] += f0 - PROF_T; } } bt_;
#endif
	sdk_Bitboard_Xor(sl.walls.w, walls.w, delta_w);
	std::uint32_t n = 0;
	// Give up on many changed tiles (each removed one costs ~300 fuel to examine).
	// (GetSetBits reports how many it wrote, capped at the capacity, so ask for all of them.)
	sdk_Bitboard_GetSetBits(delta_w, delta_pos, kMaxDim * kMaxDim, &n);
#ifdef BOT_DF_PROFILE
	dbg_n = n;
#endif
	if (n > kMaxDelta) return false;
	const int L = sl.depth;
	auto d = [&](int x, int y) {
		const int v = sl.field[fidx(x, y)];
		return v <= L ? v : L + 1;
	};
	// Conservative per-tile tests against the whole of Q at once (cheb(t, q) >= cheb(t, me) -
	// qr, and every target is at most S, or S + 1 for tiles beyond S): cheap, and a rejection
	// only costs a fresh search.
	for (std::uint32_t i = 0; i < n; ++i)
	{
		const int x = delta_pos[i].x, y = delta_pos[i].y;
		if (roots.test(x, y)) return false;
		const int c = cheb(x, y, me);
		if (walls.test(x, y))
		{
			// a is excluded from Q (walls read as unreachable), so cheb(a, q) >= 1 for q in Q.
			if (d(x, y) + std::max(1, c - qr) <= S) return false;
		}
		else
		{
			if (c - qr >= S) continue; // lb >= 1
			int lb = 0x10000;
			for (int yy = std::max(0, y - 1); yy <= std::min(H - 1, y + 1); ++yy)
				for (int xx = std::max(0, x - 1); xx <= std::min(W - 1, x + 1); ++xx)
					if ((xx != x || yy != y) && !sl.walls.test(xx, yy)) lb = std::min(lb, d(xx, yy) + 1);
			if (lb + std::max(0, c - qr) < S + 1) return false;
		}
	}
	return true;
}

struct FieldAnswer
{
	const std::uint16_t* f;
	const Bitboard* walls; // the request's: never reached by a fresh search
	int limit;			   // values above this read as unreachable (-1: none)
	int count;			   // the stopping layer (expansion count of an equivalent fresh search)
	std::uint16_t at(int x, int y) const
	{
		const std::uint16_t v = f[fidx(x, y)];
		return (limit >= 0 && v > limit) || walls->test(x, y) ? kUnreachable : v;
	}
};

// `me` is the champion's tile (have_me false for the draft bot). The caller reads the answer
// only at dests and at open tiles within Chebyshev `qr` of `me` (qr > 2: no walls-changed reuse).
FieldAnswer field_query(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, bool have_me, Vec2 me,
						int qr, int W, int H)
{
#ifdef BOT_PROF2
	struct FT { long long f0 = PROF_T; ~FT() { bot_prof[0] += f0 - PROF_T; } } ft_;
#endif
	if (!slots) slots = new FieldSlot[kSlots];
#ifdef BOT_DF_PROFILE
	const auto pf0 = sdk_fuel_remaining();
	int pf_hit = 0;
	struct PfTail
	{
		decltype(pf0) f0;
		int& hit;
		const Bitboard* d;
		int H;
		const Bitboard* r;
		int qr;
		Vec2 me;
		~PfTail()
		{
			Vec2 rt{ -1, -1 };
			r->first(H, rt);
			std::printf("@@DF %lld %d nd=%d roots=%d r0=%d,%d qr=%d me=%d,%d\n", static_cast<long long>(f0 - sdk_fuel_remaining()), hit, d ? d->count(H) : -1,
						r->count(H), rt.x, rt.y, qr, me.x, me.y);
		}
	} pf_tail{ pf0, pf_hit, dests, H, &roots, qr, me };
#endif
	const auto maxd = static_cast<std::uint16_t>(std::clamp(max_distance, 0, 0xFFFF));
	// Nearest dest in a cached field (0x10000 if none within its depth); -1 if need_box and
	// some dest lies outside the box around the champion.
	auto nearest = [&](const FieldSlot& sl, bool need_box) {
		int best = 0x10000;
		const int L = sl.depth;
		dests->for_each_unordered(H, [&](int x, int y) {
			if (best < 0) return;
			if (need_box && cheb(x, y, me) > qr)
			{
				best = -1;
				return;
			}
			const int v = sl.field[fidx(x, y)];
			if (v <= L && v < best && !walls.test(x, y)) best = v; // a wall dest is never reached
		});
		return best;
	};
	FieldAnswer ans{ nullptr, &walls, -1, 0 };
	FieldSlot *use = nullptr, *same_roots = nullptr;
#ifdef BOT_PROF2
	const long long p0 = PROF_T;
#endif
	for (int i = 0; i < kSlots && !use; ++i)
	{
		FieldSlot& sl = slots[i];
#ifdef BOT_REFERENCE
		continue; // reference build: always a fresh search
#endif
		if (sl.depth < 0 || sl.maxd != maxd || !(sl.roots == roots)) continue;
		same_roots = &sl;
#ifdef BOT_DF_PROFILE
		pf_hit = 3;
#endif
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
		else if (dests && have_me && qr <= 2)
		{
			const int best = nearest(sl, true);
			if (best >= 0 && best <= sl.depth && box_unaffected(sl, walls, roots, me, best, qr, W, H)) use = &sl, ans.limit = best;
		}
	}
#ifdef BOT_PROF2
	bot_prof[5] += p0 - PROF_T;
#endif
#ifdef BOT_VERIFY
	int vpath = use ? (use->walls == walls ? 1 : 2) : 0;
	int vdepth = use ? use->depth : -1, vcomplete = use ? use->complete : -1;
#endif
	if (use)
	{
		ans.count = ans.limit >= 0 ? ans.limit : use->depth;
#ifdef BOT_DF_PROFILE
		pf_hit = use->walls == walls ? 1 : 2;
#endif
	}
	else
	{
		// Replace the stale field with the same roots, else the least recently used one.
		use = same_roots;
		if (!use)
		{
			use = &slots[0];
			for (int i = 1; i < kSlots; ++i)
				if (slots[i].used < use->used) use = &slots[i];
		}
		// Scratch boards (never zeroed: the host writes all of `visited`; me_only is kept empty
		// between calls).
		static Bitboard visited, me_only;
		const Bitboard* sd = dests;
#ifdef BOT_REFERENCE
		const bool to_me = false;
#else
		const bool to_me = dests && have_me && dests->test(me);
#endif
		if (to_me)
		{
			me_only.set(me);
			sd = &me_only;
		}
		std::uint16_t count = 0;
#ifdef BOT_PROF2
		const long long h0 = PROF_T;
		struct HT { long long h0; ~HT() { bot_prof[1] += h0 - PROF_T; } } ht_{ h0 };
#endif
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
		if (to_me)
		{
			reached = visited.test(me);
			me_only.reset(me);
		}
		else if (sd)
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
			for (int y = std::max(0, me.y - std::min(qr, 2)); y <= std::min(H - 1, me.y + std::min(qr, 2)); ++y)
				for (int x = std::max(0, me.x - std::min(qr, 2)); x <= std::min(W - 1, me.x + std::min(qr, 2)); ++x) check(x, y);
		if (dests) dests->for_each_unordered(H, check);
		if (++verify_checks % 2000 == 0) std::printf("@@VERIFY checks=%ld fails=%ld\n", verify_checks, verify_fails);
		if (bad)
		{
			++verify_fails;
			std::printf("@@VERIFY field mismatch tiles=%d limit=%d count=%d stop=%d path=%d depth=%d complete=%d qr=%d me=%d,%d nroots=%d\n", bad, ans.limit, ans.count, stop, vpath, vdepth, vcomplete, qr, me.x, me.y, roots.count(H));
		}
	}
#endif
	return ans;
}
} // namespace

int Api::distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, std::uint16_t* dist,
						Bitboard& visited)
{
#ifdef BOT_PROF2
	struct DT { long long f0 = PROF_T; ~DT() { bot_prof[4] += f0 - PROF_T; } } dt_;
#endif
	const int W = g_.map().W, H = g_.map().H;
	champion_info ci{};
	const bool have_me = champ_ >= 0 && sdk_champion(static_cast<std::uint32_t>(champ_), &ci) == 0;
	const Vec2 me{ ci.x, ci.y };
	// The interpreter reads the dests and, around the champion, its 3x3 (move_towards) or, when
	// the dests reach that far, its 5x5 box (dash_towards); every other entry is unspecified,
	// and `visited` is not maintained (no caller reads it).
	static hostbb::Pos dpos[kMaxDim * kMaxDim];
	std::uint32_t nd = 0;
	int qr = 1;
	if (dests)
	{
		sdk_Bitboard_GetSetBits(dests->w, dpos, kMaxDim * kMaxDim, &nd);
		if (have_me)
			for (std::uint32_t i = 0; i < nd; ++i) qr = std::max(qr, cheb(dpos[i].x, dpos[i].y, me));
	}
	const FieldAnswer ans = field_query(walls, roots, dests, max_distance, have_me, me, std::min(qr, 3), W, H);
#ifdef BOT_PROF2
	struct QT { long long q0 = PROF_T; ~QT() { bot_prof[6] += q0 - PROF_T; } } qt_;
#endif
	const int r = std::min(qr, 2);
	if (have_me)
		for (int y = std::max(0, me.y - r); y <= std::min(H - 1, me.y + r); ++y)
			for (int x = std::max(0, me.x - r); x <= std::min(W - 1, me.x + r); ++x) dist[y * W + x] = ans.at(x, y);
	for (std::uint32_t i = 0; i < nd; ++i)
		if (!have_me || cheb(dpos[i].x, dpos[i].y, me) > r) dist[dpos[i].y * W + dpos[i].x] = ans.at(dpos[i].x, dpos[i].y);
	return ans.count;
}

// Same answer as the simulator's (origin-rooted search, nearest candidate, ties row-major),
// computed as: D = distance to the nearest candidate from a search rooted at the candidates
// with `origin` as its only dest (distances are symmetric; rooted at a fixed set, so the
// memo usually answers it on later turns), then the candidates within D of `origin`, which
// are all exactly D away, and the first of them in row-major order.
bool Api::nearest_by_walk(const Bitboard& walls, Vec2 origin, const Bitboard& cand, Vec2& out, int* expansions)
{
#ifdef BOT_PROF2
	struct NT { long long f0 = PROF_T; ~NT() { bot_prof[2] += f0 - PROF_T; } } nt_;
#endif
	if (expansions) *expansions = 0; // only the simulator prices it
	const int W = g_.map().W, H = g_.map().H;
#ifdef BOT_REFERENCE
	{
		// The simulator's algorithm, on a fresh host search.
		static std::uint16_t f[kFieldWords];
		Bitboard o, v;
		o.set(origin);
		std::uint16_t c = 0;
		sdk_DistanceField_ComputeToWithExpansionCount(walls.w, o.w, cand.w, v.w, f, kUnreachable, &c);
		std::uint16_t bd = kUnreachable;
		bool found = false;
		cand.for_each(H, [&](int x, int y) {
			if (f[fidx(x, y)] < bd) bd = f[fidx(x, y)], out = { x, y }, found = true;
		});
		return found;
	}
#endif
	champion_info ci{};
	const bool have_me = champ_ >= 0 && sdk_champion(static_cast<std::uint32_t>(champ_), &ci) == 0 && ci.x == origin.x && ci.y == origin.y;
	Bitboard o;
	o.set(origin);
	const FieldAnswer ans = field_query(walls, cand, &o, kUnreachable, have_me, origin, 0, W, H); // reads only origin
	const int D = ans.at(origin.x, origin.y);
	bool found = false;
	if (D != kUnreachable)
	{
		// Candidates within D of origin: a reachable mask (measured ~4k at D ~ 46 on 100x100,
		// against ~18k for an origin-rooted field cut at D; it costs per tile reached, at most
		// ~16k for a whole 100x100 map).
#ifdef BOT_PROF2
		struct IT { long long f0 = PROF_T; ~IT() { bot_prof[3] += f0 - PROF_T; } } it_;
#endif
		Bitboard near;
		sdk_Bitboard_ReachableMask(walls.w, origin.x, origin.y, near.w, D);
		near &= cand;
		found = near.first(H, out);
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
