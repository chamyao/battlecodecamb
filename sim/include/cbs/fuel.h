// Fuel accounting. Fuel is a game rule: every bot call is priced, the per-turn budget is
// enforced by the runner, and exhausting it suspends the bot until its next turn.
//
// Prices are measured against cambc 3.0.5 with oracle/bots/fuelprobe (see docs/FUEL.md). A price may
// depend on the map's 8x8 chunk count and on a call-specific size n via PriceContext.
#pragma once
#include <cstdint>
#include <functional>

namespace cbs
{
enum class Call : std::uint16_t
{
	// identity / roster
	my_champion, my_team, champion_is_alive, num_allies, num_enemies, allies, enemies,
	// champion queries
	champion, champion_identity, champion_design, champion_restrictions, champion_ability_props, champion_cooldown,
	champion_items, champion_consumables, champion_gems, champion_gold, champion_vision, hypothetical_vision,
	champion_wards, champion_ward_positions, champion_channel_time, champion_can_shop, champion_can_sell, champion_priority,
	champion_buff_data, ability_damage, ability_heal, ability_shield,
	// world queries
	vision, ward_vision, wards, teleports, altar_locks, occupancy, camp, camp_state, camp_buffs, camp_design, camp_group_state,
	camp_group_cooldown, is_visible, has_unit, unit_at, submitted_gems, round_number, item_info, consumable_info, game_settings,
	// static map
	metadata, map_mask, map_symmetry, spawn_region, map_camp_query,
	// actions
	move_to, attack, cast, buy_item, buy_consumable, sell, use_consumable, recall, cancel_channel, submit_gems, place_ward,
	set_priority, resign,
	// memory
	shared_memory_size, read_shared_memory, write_shared_memory, draft_memory_size, read_draft_memory, submit_draft_memory,
	// draft
	draft_num_rounds, draft_get, draft_champion,
	// geometry primitives (bitboards / distance fields)
	bitboard_op, bitboard_shadow_cast, bitboard_reachable, distance_field, draw_shape,
	// Api::nearest_by_walk (raw: one distance field; the deploy bot: field_memo.h + a reachable mask)
	nearest_by_walk,
	// misc
	fuel_remaining, debug_draw, yield,
	// a policy's own computation (building blocks) charged explicitly
	compute,
	count
};

struct PriceContext
{
	int map_w = 0, map_h = 0;
	std::int64_t n = 0;	 // call-specific size: units returned, BFS expansions, bytes copied...
	std::int64_t n2 = 0; // second size where a call has one (distance_field: destination tiles)
	std::int64_t n3 = 0; // third size (deploy bot's distance_field / nearest_by_walk: memo misses)
	// Bitboards are stored as one 64-bit word per 8x8 chunk; board-sized calls cost ~1 fuel per word.
	std::int64_t chunks() const { return static_cast<std::int64_t>((map_w + 7) / 8) * ((map_h + 7) / 8); }
};

// Maps a call (and its context) to fuel. Default: measured prices.
struct PriceTable
{
	// price = base + per_row * H + per_chunk * chunks
	//       + (per_n_milli * n + per_n_chunk_milli * n * chunks + per_n2_milli * n2
	//          + per_n3_milli * n3 + per_n3_chunk_milli * n3 * chunks) / 1000
	std::int64_t base[static_cast<int>(Call::count)];
	std::int64_t per_row[static_cast<int>(Call::count)];
	std::int64_t per_chunk[static_cast<int>(Call::count)];
	std::int64_t per_n_milli[static_cast<int>(Call::count)];
	std::int64_t per_n_chunk_milli[static_cast<int>(Call::count)];
	std::int64_t per_n2_milli[static_cast<int>(Call::count)];
	std::int64_t per_n3_milli[static_cast<int>(Call::count)];
	std::int64_t per_n3_chunk_milli[static_cast<int>(Call::count)];
	// The calls are made through the deploy bot's distance-field memo (cbs/field_memo.h): Api
	// runs the same memo to supply n (host search layers), n3 (misses) for those calls.
	bool bot_memo = false;
	// Optional override for prices that are not affine in n.
	std::function<std::int64_t(Call, const PriceContext&)> custom;

	PriceTable();
	std::int64_t price(Call c, const PriceContext& ctx) const
	{
		if (custom) return custom(c, ctx);
		const int i = static_cast<int>(c);
		const std::int64_t ch = ctx.chunks();
		return base[i] + per_row[i] * ctx.map_h + per_chunk[i] * ch +
			   (per_n_milli[i] * ctx.n + per_n_chunk_milli[i] * ctx.n * ch + per_n2_milli[i] * ctx.n2 + per_n3_milli[i] * ctx.n3 +
				per_n3_chunk_milli[i] * ctx.n3 * ch) /
				   1000;
	}
	// Raw engine imports as called directly by a C++ bot (measured against cambc; the default).
	static const PriceTable& measured();
	// The same calls as made by our deployable bot (bot/src/bot_api.cpp), whose wrappers add
	// board conversions etc. Calibrated from a profiling build of that bot (docs/FUEL.md).
	static const PriceTable& bot_wrapper();
	// Kept for callers of the old name; same as measured().
	static const PriceTable& placeholder() { return measured(); }
};

struct FuelBudget
{
	static constexpr std::int64_t kCpp = 100000;
	std::int64_t per_turn = kCpp;
	int draft_first_turn_multiplier = 10;
	int play_first_turn_multiplier = 2;
};
} // namespace cbs
