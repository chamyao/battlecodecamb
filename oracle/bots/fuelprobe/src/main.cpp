// Oracle bot: measures the fuel price of SDK calls. Every probe is bracketed by two
// fuel_remaining() reads; the "empty" probe measures the bracket itself. Prints
// "@@F <name> <n> <fuel>" where n is a size the price may depend on (units returned,
// tiles set, expansions...). Run in release builds (--release) with a large --fuel.
// Also prices our own C++ geometry (sim/src/bitboard.cpp compiled into the bot) on the same
// inputs, and the official SDK wrappers for a few common calls.
#include <cambc.h>
#include <cstdint>
#include <cstdio>
#include <vector>
#include "../src/bitboard.cpp" // resolved via -I<repo>/sim/include (oracle/run_fuelprobe.sh)

using namespace cambc;
using namespace cambc::detail;

static std::uint64_t rng_state = 0x2545F4914F6CDD1Dull;
static std::uint32_t rnd()
{
	rng_state ^= rng_state << 13;
	rng_state ^= rng_state >> 7;
	rng_state ^= rng_state << 17;
	return static_cast<std::uint32_t>(rng_state >> 11);
}

#define M(name, n, ...)                                                                                                          \
	do                                                                                                                           \
	{                                                                                                                            \
		const std::int64_t a_ = sdk_fuel_remaining();                                                                            \
		__VA_ARGS__;                                                                                                             \
		const std::int64_t b_ = sdk_fuel_remaining();                                                                            \
		std::printf("@@F %s %ld %lld\n", name, static_cast<long>(n), static_cast<long long>(a_ - b_));                         \
	} while (0)

static int W, H;

static cbs::Bitboard to_cbs(const bitboard& b)
{
	auto lin = b.export_linear_buffer();
	cbs::Bitboard o;
	cbs::from_linear(o, W, H, lin.data());
	return o;
}

static bitboard random_board(int pct)
{
	bitboard b;
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
			if (static_cast<int>(rnd() % 100) < pct) b.set({ x, y });
	return b;
}

static void geometry()
{
	bitboard a = random_board(30), b = random_board(50), out, visited, walls_map;
	sdk_bc_map_mask(0, walls_map.ptr());
	std::int32_t iv{};
	std::uint32_t uv{};
	M("empty", 0, );
	M("empty", 0, );
	M("bb_zero", 0, sdk_Bitboard_Zero(out.ptr()));
	M("bb_one", 0, sdk_Bitboard_One(out.ptr()));
	M("bb_not", 0, sdk_Bitboard_Not(a.ptr(), out.ptr()));
	M("bb_union", 0, sdk_Bitboard_Union(a.ptr(), b.ptr(), out.ptr()));
	M("bb_intersect", 0, sdk_Bitboard_Intersect(a.ptr(), b.ptr(), out.ptr()));
	M("bb_xor", 0, sdk_Bitboard_Xor(a.ptr(), b.ptr(), out.ptr()));
	M("bb_is_equal", 0, sdk_Bitboard_IsEqual(a.ptr(), b.ptr(), &iv));
	M("bb_is_zero", 0, sdk_Bitboard_IsZero(a.ptr(), &iv));
	M("bb_test", 0, sdk_Bitboard_Test(a.ptr(), 1, 1, &iv));
	M("bb_set", 0, sdk_Bitboard_Set(out.ptr(), 1, 1, 1));
	M("bb_shift_right", 1, sdk_Bitboard_ShiftRight(a.ptr(), out.ptr(), 1));
	M("bb_shift_right", 7, sdk_Bitboard_ShiftRight(a.ptr(), out.ptr(), 7));
	M("bb_shift_up", 1, sdk_Bitboard_ShiftUp(a.ptr(), out.ptr(), 1));
	M("bb_reflect", 0, sdk_Bitboard_Reflect(a.ptr(), out.ptr(), 1));
	for (int pct : { 0, 1, 5, 20, 50, 100 })
	{
		bitboard c = random_board(pct);
		std::uint32_t n{};
		sdk_Bitboard_NumSetBits(c.ptr(), &n);
		M("bb_num_set_bits", n, sdk_Bitboard_NumSetBits(c.ptr(), &uv));
		std::vector<position> pos(static_cast<std::size_t>(W * H) + 1);
		M("bb_get_set_bits", n, sdk_Bitboard_GetSetBits(c.ptr(), pos.data(), pos.size(), &uv));
		auto lin = c.export_linear_buffer();
		M("bb_export_linear", 0, sdk_Bitboard_ExportLinearBuffer(c.ptr(), lin.data(), lin.size()));
		M("bb_import_linear", 0, sdk_Bitboard_ImportLinearBuffer(out.ptr(), lin.data(), lin.size()));
	}
	for (int r : { 0, 1, 2, 4, 8, 16, 40 })
	{
		M("bb_draw_circle", r, sdk_Bitboard_DrawCircle(out.ptr(), W / 2, H / 2, static_cast<float>(r)));
		M("bb_draw_chebyshev", r, sdk_Bitboard_DrawChebyshev(out.ptr(), W / 2, H / 2, static_cast<float>(r)));
		cbs::Bitboard co;
		M("cbs_draw_chebyshev", r, cbs::draw_chebyshev(co, W, H, { W / 2, H / 2 }, static_cast<float>(r)));
		M("cbs_draw_circle", r, cbs::draw_circle(co, W, H, { W / 2, H / 2 }, static_cast<float>(r)));
	}
	// Shadowcast / reachable: price vs result size, host vs our C++.
	for (int t = 0; t < 60; ++t)
	{
		const int pct = static_cast<int>(rnd() % 40);
		bitboard walls = (t % 3 == 0) ? walls_map : random_board(pct);
		const cbs::Bitboard cw = to_cbs(walls);
		const int x = static_cast<int>(rnd() % W), y = static_cast<int>(rnd() % H);
		const int d = static_cast<int>(rnd() % 13);
		sdk_Bitboard_ShadowCast(walls.ptr(), x, y, out.ptr(), static_cast<std::uint16_t>(d));
		std::uint32_t n{};
		sdk_Bitboard_NumSetBits(out.ptr(), &n);
		M("bb_shadow_cast", n, sdk_Bitboard_ShadowCast(walls.ptr(), x, y, out.ptr(), static_cast<std::uint16_t>(d)));
		cbs::Bitboard co;
		M("cbs_shadow_cast", n, cbs::shadow_cast(cw, W, H, { x, y }, d, co));
		long scanned = 0, marked = 0;
		cbs::shadowcast(W, H, { x, y }, d, [&](int bx, int by) { ++scanned; return cw.test(bx, by); }, [&](int, int) { ++marked; });
		std::printf("@@G shadow d=%d n=%u scanned=%ld marked=%ld\n", d, n, scanned, marked);
		sdk_Bitboard_ReachableMask(walls.ptr(), x, y, out.ptr(), static_cast<std::uint16_t>(d));
		sdk_Bitboard_NumSetBits(out.ptr(), &n);
		M("bb_reachable", n, sdk_Bitboard_ReachableMask(walls.ptr(), x, y, out.ptr(), static_cast<std::uint16_t>(d)));
		M("cbs_reachable", n, cbs::reachable(cw, W, H, { x, y }, d, co));
		int layers = 0;
		{
			cbs::Bitboard prev, cur;
			cbs::reachable(cw, W, H, { x, y }, 0, prev);
			for (int k = 1; k <= d; ++k)
			{
				cbs::reachable(cw, W, H, { x, y }, k, cur);
				if (cur == prev) break;
				layers = k;
				prev = cur;
			}
		}
		std::printf("@@G reach d=%d n=%u layers=%d\n", d, n, layers);
	}
	// Distance fields: price vs visited tiles / expansions.
	std::vector<std::uint16_t> cd(static_cast<std::size_t>(W * H));
	for (int t = 0; t < 60; ++t)
	{
		bitboard walls = (t % 3 == 0) ? walls_map : random_board(static_cast<int>(rnd() % 40));
		bitboard roots, dests;
		const int nroots = 1 + static_cast<int>(rnd() % 4);
		for (int i = 0; i < nroots; ++i) roots.set({ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) });
		dests.set({ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) });
		const std::uint16_t maxd = (t % 4 == 0) ? static_cast<std::uint16_t>(rnd() % 20) : distance_field::unreachable;
		const cbs::Bitboard cw = to_cbs(walls), cr = to_cbs(roots), cdst = to_cbs(dests);
		distance_field f;
		std::uint16_t count{};
		sdk_DistanceField_ComputeWithExpansionCount(walls.ptr(), roots.ptr(), visited.ptr(), f.ptr(), maxd, &count);
		std::uint32_t n{};
		sdk_Bitboard_NumSetBits(visited.ptr(), &n);
		M("df_compute", n, sdk_DistanceField_ComputeWithExpansionCount(walls.ptr(), roots.ptr(), visited.ptr(), f.ptr(), maxd, &count));
		cbs::Bitboard cv;
		M("cbs_distance_field", n, cbs::distance_field(cw, cr, nullptr, W, H, maxd, cd.data(), cv));
		std::printf("@@G df n=%u exp=%u\n", n, count);
		sdk_DistanceField_ComputeToWithExpansionCount(walls.ptr(), roots.ptr(), dests.ptr(), visited.ptr(), f.ptr(), maxd, &count);
		sdk_Bitboard_NumSetBits(visited.ptr(), &n);
		M("df_compute_to", n, sdk_DistanceField_ComputeToWithExpansionCount(walls.ptr(), roots.ptr(), dests.ptr(), visited.ptr(), f.ptr(), maxd, &count));
		std::printf("@@G dfto n=%u exp=%u\n", n, count);
		M("cbs_distance_field_to", n, cbs::distance_field(cw, cr, &cdst, W, H, maxd, cd.data(), cv));
		std::uint16_t v{};
		M("df_get", 0, sdk_DistanceField_Get(f.ptr(), 1, 1, &v));
		M("df_set", 0, sdk_DistanceField_Set(f.ptr(), 1, 1, 3));
		distance_field g;
		M("df_copy", 0, sdk_DistanceField_Copy(f.ptr(), g.ptr()));
	}
	// Static / design queries.
	metadata md{};
	M("bc_metadata", 0, sdk_bc_metadata(&md));
	M("bc_map_mask", 0, sdk_bc_map_mask(0, out.ptr()));
	M("bc_map_symmetry", 0, sdk_bc_map_symmetry(&iv));
	M("map_num_camp_groups", 0, sdk_map_num_camp_groups(&uv));
	camp_info ci{};
	M("map_camp_info", 0, sdk_map_camp_info(0, &ci));
	std::vector<std::uint32_t> layout(4096);
	M("map_camp_layout", 0, sdk_map_camp_layout(layout.data(), layout.size(), &uv));
	M("map_camp_at", 0, sdk_map_camp_at(1, 1, &uv));
	detail::item_info ii{};
	M("item_info", 0, sdk_item_info(3, &ii));
	detail::consumable_info cci{};
	M("consumable_info", 0, sdk_consumable_info(0, &cci));
	champion_design cdz{};
	M("champion_design", 0, sdk_champion_design(2, &cdz));
	aabb box{};
	M("spawn_region", 0, sdk_spawn_region(0, &box));
	std::uint8_t mem[1024] = {};
	std::uint8_t nr{};
	M("draft_num_rounds", 0, sdk_draft_num_rounds(&nr));
	M("draft_get", 0, sdk_draft_get(0, 0, &iv));
	M("submit_draft_memory", 16, sdk_bc_submit_draft_memory(mem, 16));
	M("submit_draft_memory", 1024, sdk_bc_submit_draft_memory(mem, 1024));
	M("my_team", 0, sdk_my_team());
	M("fuel_remaining", 0, sdk_fuel_remaining());
	// Plain guest computation for scale: a 1000-iteration xorshift loop.
	std::uint32_t acc = 0;
	M("guest_loop_1000", 1000, for (int i = 0; i < 1000; ++i) acc += rnd());
	std::printf("@@acc %u\n", acc);
	// SDK wrappers (allocate / throw-check) for comparison.
	M("wrap_bitboard_ctor", 0, bitboard tmp; (void)tmp);
	M("wrap_bitboard_or", 0, bitboard tmp = a | b; (void)tmp);
	M("wrap_map_walls", 0, auto tmp = map::walls(); (void)tmp);
	M("wrap_distance_field_ctor", 0, distance_field tmp; (void)tmp);
}

static void play()
{
	const std::uint32_t me = static_cast<std::uint32_t>(sdk_my_champion());
	std::int32_t iv{};
	std::uint32_t uv{};
	std::uint32_t ids[16];
	M("empty", 0, );
	M("my_champion", 0, sdk_my_champion());
	M("champion_is_alive", 0, sdk_champion_is_alive(me, &iv));
	M("num_allies", 0, sdk_num_allies(&uv));
	M("num_enemies", 0, sdk_num_enemies(&uv));
	std::uint32_t na{}, ne{};
	sdk_allies(ids, 16, &na);
	M("allies", na, sdk_allies(ids, 16, &uv));
	sdk_enemies(ids, 16, &ne);
	M("enemies", ne, sdk_enemies(ids, 16, &uv));
	champion_info ci{};
	M("champion_self", 0, sdk_champion(me, &ci));
	for (std::uint32_t h = 0; h < 12; ++h)
	{
		std::int32_t rc{};
		M(h == me ? "champion_self" : "champion_other", 0, rc = sdk_champion(h, &ci));
		std::printf("@@G champion rc=%d\n", rc);
	}
	champion_identity cid{};
	M("champion_identity", 0, sdk_champion_identity(me, &cid));
	std::uint8_t restr{};
	M("champion_restrictions", 0, sdk_champion_restrictions(me, &restr));
	ability_props ap{};
	M("champion_ability_props", 0, sdk_champion_ability_props(me, 0, &ap));
	M("champion_cooldown", 0, sdk_champion_cooldown(me, 0, &iv));
	std::uint32_t items[42];
	M("champion_items", 0, sdk_champion_items(me, items));
	std::uint32_t cons[4];
	M("champion_consumables", 0, sdk_champion_consumables(me, cons));
	M("champion_gems", 0, sdk_champion_gems(me, &uv));
	M("champion_gold", 0, sdk_champion_gold(me, &uv));
	buff_data bd[16];
	std::uint32_t nb{};
	sdk_champion_buff_data(me, bd, 16, &nb);
	M("champion_buff_data", nb, sdk_champion_buff_data(me, bd, 16, &uv));
	float fv{};
	M("champion_ability_damage", 0, sdk_champion_ability_damage(me, 0, &fv));
	bitboard vis, out;
	M("bc_champion_vision", 0, sdk_bc_champion_vision(me, vis.ptr()));
	M("board_vision", 0, sdk_vision(vis.ptr()));
	std::uint32_t nvis{};
	sdk_Bitboard_NumSetBits(vis.ptr(), &nvis);
	M("hypothetical_vision", 0, sdk_hypothetical_vision(0, ci.x, ci.y, out.ptr()));
	M("ward_vision", 0, sdk_ward_vision(ci.x, ci.y, out.ptr()));
	ward_resources wr{};
	M("champion_wards", 0, sdk_champion_wards(me, &wr));
	position wp[4];
	M("champion_ward_positions", 0, sdk_champion_ward_positions(me, wp, 4, &uv));
	M("champion_channel_time", 0, sdk_champion_channel_time(me, &iv));
	M("champion_can_shop", 0, sdk_champion_can_shop(me, 0, &iv));
	M("champion_can_sell", 0, sdk_champion_can_sell(me, &iv));
	M("champion_priority", 0, sdk_bc_champion_priority(me, 0, &iv));
	ward_info wi[32];
	std::uint32_t nw{};
	sdk_wards(wi, 32, &nw);
	M("wards", nw, sdk_wards(wi, 32, &uv));
	teleport_info ti[16];
	std::uint32_t nt{};
	sdk_teleports(ti, 16, &nt);
	M("teleports", nt, sdk_teleports(ti, 16, &uv));
	altar_lock_info li[16];
	std::uint32_t nl{};
	sdk_altar_locks(li, 16, &nl);
	M("altar_locks", nl, sdk_altar_locks(li, 16, &uv));
	M("ally_occupancy", 0, sdk_ally_occupancy(out.ptr()));
	M("enemy_occupancy", 0, sdk_enemy_occupancy(out.ptr()));
	M("camp_occupancy", 0, sdk_camp_occupancy(out.ptr()));
	M("awake_camp_occupancy", 0, sdk_awake_camp_occupancy(out.ptr()));
	M("ally_ward_occupancy", 0, sdk_ally_ward_occupancy(out.ptr()));
	M("teleport_occupancy", 0, sdk_teleport_occupancy(out.ptr()));
	M("ward_at", 0, sdk_ward_at(ci.x, ci.y, &uv));
	M("champion_at", 0, sdk_champion_at(ci.x, ci.y, &uv));
	M("camp_at", 0, sdk_camp_at(ci.x, ci.y, &uv));
	M("is_visible", 0, sdk_is_visible(ci.x, ci.y, &iv));
	M("has_champion", 0, sdk_has_champion(ci.x, ci.y, &iv));
	M("has_camp", 0, sdk_has_camp(ci.x, ci.y, &iv));
	detail::camp_state cs{};
	for (std::uint32_t k = 0; k < 6; ++k)
	{
		std::int32_t rc{};
		M("camp", 0, rc = sdk_camp(k, &cs));
		std::printf("@@G camp rc=%d\n", rc);
		M("camp_state", 0, sdk_camp_state(k, &uv));
	}
	camp_buff_data cb[8];
	M("camp_buffs", 0, sdk_camp_buffs(0, cb, 8, &uv));
	M("camp_group_state", 0, sdk_camp_group_state(0, &uv));
	M("camp_group_cooldown", 0, sdk_camp_group_cooldown(0, &iv));
	detail::camp_group_capture_state cgs{};
	for (std::uint32_t g = 0; g < 3; ++g) M("camp_group_capture_state", 0, sdk_camp_group_capture_state(g, &cgs)); // engine 2.0.0
	camp_design cdes{};
	M("camp_design", 0, sdk_camp_design(0, &cdes));
	M("bc_round_number", 0, sdk_bc_round_number(&uv));
	M("bc_submitted_gems", 0, sdk_bc_submitted_gems(0, &uv));
	std::uint8_t mem[8] = {};
	M("read_shared_memory", 8, sdk_read_shared_memory(0, mem, 8));
	M("write_shared_memory", 1, sdk_write_shared_memory(0, mem, 1));
	M("write_shared_memory", 8, sdk_write_shared_memory(0, mem, 8));
	std::uint8_t dm[1024];
	M("read_draft_memory", 1024, sdk_read_draft_memory(0, dm, 1024));
	M("set_priority", 0, sdk_set_priority(static_cast<std::int32_t>(rnd() % 5)));
	M("attack_invalid", 0, sdk_attack(9, 0));
	M("buy_item_invalid", 0, sdk_buy_item(99, 1));
	M("buy_consumable", 0, sdk_buy_consumable(0));
	M("sell_invalid", 0, sdk_sell(99));
	M("cancel_channel", 0, sdk_cancel_channel());
	M("cast_invalid", 0, sdk_cast(5, 0, 0, -1, -1, &iv));
	M("place_ward_invalid", 0, sdk_place_ward(-5, -5, &iv));
	M("submit_gems_invalid", 0, sdk_submit_gems(-5, -5));
	M("debug_dot", 0, sdk_debug_dot(ci.x, ci.y, 0xff0000));
	M("fuel_remaining", 0, sdk_fuel_remaining());
	// wrappers
	M("wrap_self_position", 0, auto p = self().position(); (void)p);
	M("wrap_vision_champion_tiles", 0, auto b = vision::champion_tiles(); (void)b);
	std::printf("@@G turn nvis=%u na=%u ne=%u\n", nvis, na, ne);
	// Random walk so visibility varies.
	const int dx = static_cast<int>(rnd() % 3) - 1, dy = static_cast<int>(rnd() % 3) - 1;
	std::int32_t ok{};
	M("move_to", 0, sdk_move_to(ci.x + dx, ci.y + dy, &ok));
	std::printf("@@G move ok=%d\n", ok);
}

int main()
{
	metadata md{};
	sdk_bc_metadata(&md);
	W = md.width, H = md.height;
	std::printf("@@dims %d %d board=%u field=%u\n", W, H, md.board_bytes, md.field_bytes);
	if (is_draft())
	{
		if (sdk_my_team() == 0) geometry();
		std::uint32_t picks = 0;
		for (;;)
		{
			try { draft::pick(static_cast<champion_draft>((sdk_my_team() * 5 + picks++) % 11)); } catch (...) {}
			end_turn();
		}
	}
	for (int turn = 0;; ++turn)
	{
		if (turn % 5 == 0) play();
		else
		{
			champion_info ci{};
			sdk_champion(static_cast<std::uint32_t>(sdk_my_champion()), &ci);
			std::int32_t ok{};
			sdk_move_to(ci.x + static_cast<int>(rnd() % 3) - 1, ci.y + static_cast<int>(rnd() % 3) - 1, &ok);
		}
		end_turn();
	}
}
