// Fuel accounting. Fuel is a game rule: every bot call is priced, the per-turn budget is
// enforced by the runner, and exhausting it suspends the bot until its next turn.
//
// Prices are placeholders until measured against cambc (see docs/FUEL.md). A price may
// depend on the call's inputs (map size, unit count, search size...) via PriceContext.
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
	// misc
	fuel_remaining, debug_draw, yield,
	// a policy's own computation (building blocks) charged explicitly
	compute,
	count
};

struct PriceContext
{
	int map_w = 0, map_h = 0;
	std::int64_t n = 0; // call-specific size: units returned, tiles expanded, bytes copied...
};

// Maps a call (and its context) to fuel. Default: placeholder constants.
struct PriceTable
{
	std::int64_t base[static_cast<int>(Call::count)];
	std::int64_t per_n[static_cast<int>(Call::count)];
	// Optional override for prices that are not affine in n.
	std::function<std::int64_t(Call, const PriceContext&)> custom;

	PriceTable();
	std::int64_t price(Call c, const PriceContext& ctx) const
	{
		if (custom) return custom(c, ctx);
		const int i = static_cast<int>(c);
		return base[i] + per_n[i] * ctx.n;
	}
	static const PriceTable& placeholder();
};

struct FuelBudget
{
	static constexpr std::int64_t kCpp = 100000;
	std::int64_t per_turn = kCpp;
	int draft_first_turn_multiplier = 10;
	int play_first_turn_multiplier = 2;
};
} // namespace cbs
