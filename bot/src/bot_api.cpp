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
#include "cbs/field_memo.h"

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
	// The group rewards are kept too (group_gems / group_gold read them).
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
			m->groups[g].gold = static_cast<int>(lay[i + 1]);
			m->groups[g].gems = static_cast<int>(lay[i + 2]);
			m->groups[g].respawn = static_cast<int>(lay[i + 3]);
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
	// The payload is tagged by kind (same numbering as cbs::AbilityKind); the sim fills these too.
	switch (static_cast<AbilityKind>(ap.kind))
	{
	case AbilityKind::attack_reset: out->enhanced_attack = ap.payload.enhanced_attack; break;
	case AbilityKind::damage:
	case AbilityKind::heal:
		out->range = ap.payload.damage.range;
		out->modifier = ap.payload.damage.modifier;
		break;
	case AbilityKind::aoe_damage:
		out->range = ap.payload.aoe_damage.range;
		out->radius = ap.payload.aoe_damage.radius;
		out->modifier = ap.payload.aoe_damage.modifier;
		out->duration = ap.payload.aoe_damage.duration;
		break;
	case AbilityKind::cc:
	case AbilityKind::shield:
		out->range = ap.payload.cc.range;
		out->modifier = ap.payload.cc.modifier;
		out->duration = ap.payload.cc.duration;
		break;
	case AbilityKind::dash:
		out->range = ap.payload.dash.range;
		out->radius = ap.payload.dash.radius;
		out->modifier = ap.payload.dash.modifier;
		out->duration = ap.payload.dash.duration;
		break;
	default: break;
	}
	return E(rc);
}
Err Api::champion_buff_data(std::uint32_t h, BuffRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	buff_data raw[8];
	std::uint32_t n = 0;
	const std::int32_t rc = sdk_champion_buff_data(h, raw, 8, &n);
	*count = n;
	for (std::uint32_t i = 0; i < n && i < cap && i < 8; ++i)
		out[i] = { raw[i].type, raw[i].data.shield.duration, raw[i].type == 0 ? raw[i].data.shield.value : 0.0f };
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
Err Api::camp_state(std::uint32_t h, std::uint32_t* out) { return E(sdk_camp_state(h, out)); }
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

// This champion's current vision (own, wards, reveals): one host call, ~6 + chunks fuel.
Err Api::vision(Bitboard& out)
{
	const Err e = E(sdk_vision(out.w));
	if (e != Err::success) out.clear();
	return e;
}
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
std::int64_t Api::fuel_remaining() { return static_cast<std::int64_t>(sdk_fuel_remaining()); }
Err Api::set_priority(std::int32_t p) { return E(sdk_set_priority(p)); }
Err Api::champion_priority(std::uint32_t h, bool next, std::int32_t* out) { return E(sdk_bc_champion_priority(h, next ? 1 : 0, out)); }

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
// Answered through the memo in cbs/field_memo.h (shared with the simulator, which runs the same
// decisions to price these calls); HostOps backs it with the host imports.
//
// BOT_VERIFY checks every answer against a fresh host search (debug only). BOT_REFERENCE turns
// the memo off (always a fresh search, no narrowing).
namespace
{
alignas(16) std::uint64_t delta_w[hostbb::kWords];
hostbb::Pos delta_pos[kMaxDim * kMaxDim];
#ifdef BOT_VERIFY
alignas(16) std::uint16_t verify_field[kFieldWords];
long verify_checks = 0, verify_fails = 0;
#endif

inline int fidx(int x, int y) { return ((y >> 3) * static_cast<int>(md.chunked_width) + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7); }
inline int cheb(int x, int y, Vec2 p) { return std::max(std::abs(x - p.x), std::abs(y - p.y)); }

struct HostOps
{
	using Board = Bitboard;
	int fidx(int x, int y) const { return ::cbs::fidx(x, y); }
	int delta(const Board& a, const Board& b, Vec2* out, int cap) const
	{
#ifdef BOT_PROF2
		struct BT { long long f0 = PROF_T; ~BT() { bot_prof[7] += f0 - PROF_T; } } bt_;
#endif
		sdk_Bitboard_Xor(a.w, b.w, delta_w);
		// GetSetBits reports how many it wrote, capped at the capacity, so ask for all of them.
		std::uint32_t n = 0;
		sdk_Bitboard_GetSetBits(delta_w, delta_pos, kMaxDim * kMaxDim, &n);
		for (std::uint32_t i = 0; i < n && i < static_cast<std::uint32_t>(cap); ++i) out[i] = { delta_pos[i].x, delta_pos[i].y };
		return static_cast<int>(n);
	}
	std::uint16_t compute(const Board& walls, const Board& roots, const Board* dests, std::uint16_t maxd, std::uint16_t* field,
						  Board& visited) const
	{
		std::uint16_t count = 0;
#ifdef BOT_PROF2
		struct HT { long long f0 = PROF_T; ~HT() { bot_prof[1] += f0 - PROF_T; } } ht_;
#endif
		if (dests)
			sdk_DistanceField_ComputeToWithExpansionCount(walls.w, roots.w, dests->w, visited.w, field, maxd, &count);
		else
			sdk_DistanceField_ComputeWithExpansionCount(walls.w, roots.w, visited.w, field, maxd, &count);
		return count;
	}
};
using FieldAnswer = field_memo::Answer<HostOps>;
field_memo::Memo<HostOps>* memo = nullptr;

// `me` is the champion's tile (have_me false for the draft bot). The caller reads the answer
// only at dests and at open tiles within Chebyshev `qr` of `me` (qr > 2: no walls-changed reuse).
FieldAnswer field_query(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, bool have_me, Vec2 me,
						int qr, int W, int H, bool compute = true)
{
#ifdef BOT_PROF2
	struct FT { long long f0 = PROF_T; ~FT() { bot_prof[0] += f0 - PROF_T; } } ft_;
#endif
	if (!memo)
	{
		memo = new field_memo::Memo<HostOps>(HostOps{});
#ifdef BOT_REFERENCE
		memo->reference = true;
#endif
	}
#ifdef BOT_QTRACE
	const long long qt0 = sdk_fuel_remaining();
#endif
	const FieldAnswer ans = memo->query(walls, roots, dests, max_distance, have_me, me, qr, W, H, compute);
#ifdef BOT_QTRACE
	std::printf("@@Q path=%d miss=%d layers=%d qr=%d nroots=%d ndests=%d fuel=%lld\n", ans.path, ans.miss, ans.layers, qr, roots.count(H), dests ? dests->count(H) : -1, qt0 - (long long)sdk_fuel_remaining());
#endif
#ifdef BOT_VERIFY
	if (ans.f)
	{
		const auto maxd = static_cast<std::uint16_t>(std::clamp(max_distance, 0, 0xFFFF));
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
			std::printf("@@VERIFY field mismatch tiles=%d limit=%d count=%d stop=%d path=%d depth=%d complete=%d qr=%d me=%d,%d nroots=%d\n", bad, ans.limit, ans.count, stop, ans.path, ans.depth, ans.complete, qr, me.x, me.y, roots.count(H));
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
	// ans.at, inlined (it costs ~100 fuel a tile through the generic accessors).
	const std::uint16_t* f = ans.f;
	const int lim = ans.limit < 0 ? 0xFFFF : ans.limit, cw = static_cast<int>(md.chunked_width), st = hostbb::stride;
	auto at = [&](int x, int y) -> std::uint16_t {
		const int b = (y & 7) * 8 + (x & 7);
		const std::uint16_t v = f[((y >> 3) * cw + (x >> 3)) * 64 + b];
		return v > lim || ((walls.w[(y >> 3) * st + (x >> 3)] >> b) & 1) ? kUnreachable : v;
	};
	if (have_me)
		for (int y = std::max(0, me.y - r); y <= std::min(H - 1, me.y + r); ++y)
			for (int x = std::max(0, me.x - r); x <= std::min(W - 1, me.x + r); ++x) dist[y * W + x] = at(x, y);
	for (std::uint32_t i = 0; i < nd; ++i)
		if (!have_me || cheb(dpos[i].x, dpos[i].y, me) > r) dist[dpos[i].y * W + dpos[i].x] = at(dpos[i].x, dpos[i].y);
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
	// A dead champion reads (-1,-1): nothing is reachable from off the map (and setting that bit
	// would write outside the board; the memo must never see it).
	if (origin.x < 0 || origin.y < 0 || origin.x >= W || origin.y >= H) return false;
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
	bool found = false;
	// Per candidate set (keyed by its first tile and size): the last D and what the reachable mask cost.
	// The mask's cost depends on the map (a few k in a compact region, ~a search for long walks
	// across an open map), so after a memo miss, when the last mask was dear, the simulator's
	// own algorithm runs instead on one search rooted at origin, capped at the last D + 2 per turn since: the
	// nearest candidate and the row-major tie-break come straight from it, with no
	// candidate-rooted search and no mask. Past the cap (the walls changed) it falls back.
	struct Hist
	{
		Vec2 root0{ -1, -1 };
		int n = 0; // candidate count: sets sharing a first tile are told apart
		int D = 0;
		std::uint32_t round = 0;
		long long mask = 0;
		std::uint64_t used = 0;
	};
	static Hist hist[4];
	static std::uint64_t hist_clock = 0;
	Vec2 root0{ -1, -1 };
	cand.first(H, root0);
	const int ncand = cand.count(H);
	Hist* h = nullptr;
	for (Hist& e : hist)
		if (e.root0 == root0 && e.n == ncand) h = &e;
	const int chunks = static_cast<int>(md.chunked_width * md.chunked_height);
	std::uint32_t round = 0;
	sdk_bc_round_number(&round);
	// D changes by at most 2 per turn (a dash) unless the walls change.
	const int cap = h ? h->D + 2 + 2 * static_cast<int>(std::min<std::uint32_t>(round - h->round, 8)) : 0;
	const bool origin_on_miss = have_me && h && h->mask > (cap - h->D) * chunks + 2500; // the extra layers + the candidate scan
	Bitboard o;
	o.set(origin);
	FieldAnswer ans = field_query(walls, cand, &o, kUnreachable, have_me, origin, 0, W, H, !origin_on_miss); // reads only origin
	if (!ans.f)
	{
		static std::uint16_t f[kFieldWords];
		Bitboard v;
		std::uint16_t c = 0;
		sdk_DistanceField_ComputeWithExpansionCount(walls.w, o.w, v.w, f, static_cast<std::uint16_t>(cap), &c);
		int bd = cap + 1;
		Vec2 best{};
		v &= cand; // the candidates the search reached (it writes every reached tile into v)
		v.for_each_unordered(H, [&](int x, int y) {
			const int d = f[fidx(x, y)];
			if (d < bd || (d == bd && (y < best.y || (y == best.y && x < best.x)))) bd = d, best = { x, y };
		});
		h->used = ++hist_clock;
		if (bd <= cap)
		{
			h->D = bd;
			h->round = round;
			out = best;
			found = true;
		}
		else
			ans = field_query(walls, cand, &o, kUnreachable, have_me, origin, 0, W, H);
	}
	if (!found)
	{
		const int D = ans.at(origin.x, origin.y);
		if (D != kUnreachable)
		{
			// Candidates within D of origin: a reachable mask (~1 chunk per layer, like a search).
#ifdef BOT_PROF2
			struct IT { long long f0 = PROF_T; ~IT() { bot_prof[3] += f0 - PROF_T; } } it_;
#endif
			Bitboard near;
			const long long m0 = sdk_fuel_remaining();
			sdk_Bitboard_ReachableMask(walls.w, origin.x, origin.y, near.w, D);
			if (have_me)
			{
				if (!h)
				{
					h = &hist[0];
					for (Hist& e : hist)
						if (e.used < h->used) h = &e;
					h->root0 = root0;
					h->n = ncand;
				}
				h->D = D;
				h->round = round;
				h->mask = m0 - static_cast<long long>(sdk_fuel_remaining());
				h->used = ++hist_clock;
			}
			near &= cand;
			found = near.first(H, out);
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
			std::printf("@@VERIFY nearest mismatch got %d,%d (%d) want %d,%d d=%d\n", found ? out.x : -1, found ? out.y : -1, found, want.x, want.y, bd);
		}
	}
#endif
	return found;
}

} // namespace cbs
