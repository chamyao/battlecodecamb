// Bot-side implementation of cbs::Api: the same class the simulator uses, backed by the
// engine's raw host imports (sdk/cpp/imports.h) instead of a simulated Game. This lets the
// policy interpreter (interp/src/policy.cpp) run unchanged in the real bot.
//
// Notes:
// - Bitboards are converted between the engine's chunked layout (one word per 8x8 chunk,
//   word = (y/8)*stride + x/8, bit = (y%8)*8 + x%8) and cbs row words with an 8x8 byte
//   transpose per 8 chunks.
// - distance_field() uses the host primitive (30-200x cheaper than cbs code compiled to
//   wasm, docs/FUEL.md) and, to stay cheap, only materialises distances on tiles within
//   Chebyshev 2 of this champion and on the `dests` tiles; every other entry reads as
//   unreachable and `visited` is left empty. That covers every read the interpreter makes.
// - Charges are not enforced here: the engine meters real fuel.
#include <cambc.h>
#include <algorithm>
#include <cstring>
#include <cstdio>
#include "cbs/api.h"
#include "bot_api.h"
#ifdef __wasm_simd128__
#include <wasm_simd128.h>
#endif

namespace cbs
{
namespace
{
using namespace cambc::detail;

metadata md{};
constexpr int kRawWords = 256;		  // >= 13 * 14 chunk words (100x100 maps)
constexpr int kFieldWords = 13 * 13 * 64; // u16 entries
alignas(16) std::uint64_t raw_a[kRawWords], raw_b[kRawWords], raw_c[kRawWords], raw_v[kRawWords];
alignas(16) std::uint16_t raw_field[kFieldWords];

#ifdef __wasm_simd128__
// 8x8 byte transpose with shuffles: a[j] byte k <-> a[k] byte j.
inline void transpose8(std::uint64_t a[8])
{
	const v128_t v0 = wasm_v128_load(a), v1 = wasm_v128_load(a + 2), v2 = wasm_v128_load(a + 4), v3 = wasm_v128_load(a + 6);
	// t0: bytes k = 0..3 of a0..a3 as [a0k a1k a2k a3k]; t1: k = 4..7; t2/t3: same for a4..a7.
	const v128_t t0 = wasm_i8x16_shuffle(v0, v1, 0, 8, 16, 24, 1, 9, 17, 25, 2, 10, 18, 26, 3, 11, 19, 27);
	const v128_t t1 = wasm_i8x16_shuffle(v0, v1, 4, 12, 20, 28, 5, 13, 21, 29, 6, 14, 22, 30, 7, 15, 23, 31);
	const v128_t t2 = wasm_i8x16_shuffle(v2, v3, 0, 8, 16, 24, 1, 9, 17, 25, 2, 10, 18, 26, 3, 11, 19, 27);
	const v128_t t3 = wasm_i8x16_shuffle(v2, v3, 4, 12, 20, 28, 5, 13, 21, 29, 6, 14, 22, 30, 7, 15, 23, 31);
	wasm_v128_store(a, wasm_i8x16_shuffle(t0, t2, 0, 1, 2, 3, 16, 17, 18, 19, 4, 5, 6, 7, 20, 21, 22, 23));
	wasm_v128_store(a + 2, wasm_i8x16_shuffle(t0, t2, 8, 9, 10, 11, 24, 25, 26, 27, 12, 13, 14, 15, 28, 29, 30, 31));
	wasm_v128_store(a + 4, wasm_i8x16_shuffle(t1, t3, 0, 1, 2, 3, 16, 17, 18, 19, 4, 5, 6, 7, 20, 21, 22, 23));
	wasm_v128_store(a + 6, wasm_i8x16_shuffle(t1, t3, 8, 9, 10, 11, 24, 25, 26, 27, 12, 13, 14, 15, 28, 29, 30, 31));
}
#else
inline void transpose8(std::uint64_t a[8])
{
	// a[j] byte k <-> a[k] byte j (an involution).
	constexpr std::uint64_t m4 = 0x00000000FFFFFFFFull, m2 = 0x0000FFFF0000FFFFull, m1 = 0x00FF00FF00FF00FFull;
	for (int i = 0; i < 4; ++i)
	{
		const std::uint64_t t = ((a[i] >> 32) ^ a[i + 4]) & m4;
		a[i + 4] ^= t;
		a[i] ^= t << 32;
	}
	for (int i : { 0, 1, 4, 5 })
	{
		const std::uint64_t t = ((a[i] >> 16) ^ a[i + 2]) & m2;
		a[i + 2] ^= t;
		a[i] ^= t << 16;
	}
	for (int i : { 0, 2, 4, 6 })
	{
		const std::uint64_t t = ((a[i] >> 8) ^ a[i + 1]) & m1;
		a[i + 1] ^= t;
		a[i] ^= t << 8;
	}
}
#endif

void raw_to_bb(const std::uint64_t* raw, Bitboard& b)
{
	std::memset(b.w, 0, sizeof b.w[0] * static_cast<std::size_t>(md.height)); // rows >= H are always zero
	const int cw = static_cast<int>(md.chunked_width), ch = static_cast<int>(md.chunked_height), st = static_cast<int>(md.chunk_stride);
	for (int cy = 0; cy < ch; ++cy)
		for (int g = 0; g * 8 < cw; ++g)
		{
			std::uint64_t a[8];
			for (int j = 0; j < 8; ++j) a[j] = g * 8 + j < cw ? raw[cy * st + g * 8 + j] : 0;
			transpose8(a);
			for (int k = 0; k < 8 && cy * 8 + k < md.height; ++k) b.w[cy * 8 + k][g] = a[k];
		}
}

void bb_to_raw(const Bitboard& b, std::uint64_t* raw)
{
	const int cw = static_cast<int>(md.chunked_width), ch = static_cast<int>(md.chunked_height), st = static_cast<int>(md.chunk_stride);
	std::memset(raw, 0, md.board_bytes); // padding chunks must be zero
	for (int cy = 0; cy < ch; ++cy)
		for (int g = 0; g * 8 < cw; ++g)
		{
			std::uint64_t a[8];
			for (int k = 0; k < 8; ++k) a[k] = cy * 8 + k < md.height ? b.w[cy * 8 + k][g] : 0;
			transpose8(a);
			for (int j = 0; j < 8 && g * 8 + j < cw; ++j) raw[cy * st + g * 8 + j] = a[j];
		}
}

inline std::uint16_t field_at(int x, int y)
{
	return raw_field[((y >> 3) * static_cast<int>(md.chunked_width) + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7)];
}

Err E(std::int32_t rc) { return static_cast<Err>(rc); }
} // namespace

// ---- static map ------------------------------------------------------------

std::shared_ptr<const Map> build_map_from_engine()
{
	sdk_bc_metadata(&md);
	auto m = std::make_shared<Map>();
	m->W = md.width;
	m->H = md.height;
	Bitboard* masks[4] = { &m->walls, &m->bushes, &m->holes, &m->altars };
	for (int k = 0; k < 4; ++k)
		if (sdk_bc_map_mask(k, raw_a) == 0) raw_to_bb(raw_a, *masks[k]);
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
	const Err e = E(sdk_ally_occupancy(raw_a));
	if (e == Err::success) raw_to_bb(raw_a, out);
	else out.clear();
	return e;
}
Err Api::enemy_occupancy(Bitboard& out)
{
	const Err e = E(sdk_enemy_occupancy(raw_a));
	if (e == Err::success) raw_to_bb(raw_a, out);
	else out.clear();
	return e;
}
Err Api::camp_occupancy(Bitboard& out, int which)
{
	const std::int32_t rc = which == 1 ? sdk_awake_camp_occupancy(raw_a) : which == 2 ? sdk_asleep_camp_occupancy(raw_a) : sdk_camp_occupancy(raw_a);
	if (rc == 0) raw_to_bb(raw_a, out);
	else out.clear();
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

int Api::distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, std::uint16_t* dist,
						Bitboard& visited)
{
	bb_to_raw(walls, raw_a);
	bb_to_raw(roots, raw_b);
	std::uint16_t count = 0;
	const auto maxd = static_cast<std::uint16_t>(std::clamp(max_distance, 0, 0xFFFF));
	if (dests)
	{
		bb_to_raw(*dests, raw_c);
		sdk_DistanceField_ComputeToWithExpansionCount(raw_a, raw_b, raw_c, raw_v, raw_field, maxd, &count);
	}
	else
		sdk_DistanceField_ComputeWithExpansionCount(raw_a, raw_b, raw_v, raw_field, maxd, &count);
	const int W = g_.map().W, H = g_.map().H;
	// The caller's array is the interpreter's reusable field: it starts out (and is kept)
	// all-unreachable except where we wrote last time, so only those entries are reset
	// (a full fill costs 2 fuel per tile in wasm).
	static std::vector<int> written;
	static const std::uint16_t* last = nullptr;
	if (last != dist)
	{
		std::fill(dist, dist + static_cast<std::size_t>(W) * H, kUnreachable);
		last = dist;
	}
	else
		for (int i : written) dist[i] = kUnreachable;
	written.clear();
	auto put = [&](int x, int y) {
		dist[y * W + x] = field_at(x, y);
		written.push_back(y * W + x);
	};
	std::memset(visited.w, 0, sizeof visited.w[0] * static_cast<std::size_t>(H)); // not materialised (see top)
	champion_info ci{};
	if (champ_ >= 0 && sdk_champion(static_cast<std::uint32_t>(champ_), &ci) == 0)
		for (int y = std::max(0, ci.y - 2); y <= std::min(H - 1, ci.y + 2); ++y)
			for (int x = std::max(0, ci.x - 2); x <= std::min(W - 1, ci.x + 2); ++x) put(x, y);
	if (dests) dests->for_each(H, put);
	return count;
}
} // namespace cbs
