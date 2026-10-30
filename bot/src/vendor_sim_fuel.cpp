#include "cbs/fuel.h"

namespace cbs
{
// Measured with oracle/bots/fuelprobe on cambc 3.0.5 (release builds), maps from 30x30 to
// 100x100; see docs/FUEL.md. Each price is what a C++ bot pays for one raw import call,
// including its own call-site instructions (argument setup), with the measuring bracket
// subtracted. Successful actions were mostly measured on their failing paths (RULE? success
// paths may cost a few fuel more).
PriceTable::PriceTable()
{
	for (int i = 0; i < static_cast<int>(Call::count); ++i)
	{
		base[i] = 8; // unmeasured calls: a typical small host call
		per_row[i] = per_chunk[i] = per_n_milli[i] = per_n_chunk_milli[i] = per_n2_milli[i] = per_n3_milli[i] = per_n3_chunk_milli[i] = 0;
	}
	auto set = [&](Call c, std::int64_t b, std::int64_t chunk = 0, std::int64_t n_milli = 0) {
		base[static_cast<int>(c)] = b;
		per_chunk[static_cast<int>(c)] = chunk;
		per_n_milli[static_cast<int>(c)] = n_milli;
	};
	// identity / roster
	set(Call::my_champion, 1);
	set(Call::my_team, 1);
	set(Call::champion_is_alive, 5);
	set(Call::num_allies, 4);
	set(Call::num_enemies, 4);
	set(Call::allies, 11);
	set(Call::enemies, 11);
	// champion queries
	set(Call::champion, 6);
	set(Call::champion_identity, 5);
	set(Call::champion_design, 5);
	set(Call::champion_restrictions, 5);
	set(Call::champion_ability_props, 6);
	set(Call::champion_cooldown, 6);
	set(Call::champion_items, 5);
	set(Call::champion_consumables, 5);
	set(Call::champion_gems, 5);
	set(Call::champion_gold, 5);
	set(Call::champion_vision, 5, 1);
	set(Call::hypothetical_vision, 9, 2);
	set(Call::champion_wards, 7);
	set(Call::champion_ward_positions, 11);
	set(Call::champion_channel_time, 7);
	set(Call::champion_can_shop, 8);
	set(Call::champion_can_sell, 7);
	set(Call::champion_priority, 8);
	set(Call::champion_buff_data, 9);
	set(Call::ability_damage, 6);
	set(Call::ability_heal, 6);
	set(Call::ability_shield, 6);
	// world queries
	set(Call::vision, 4, 1);
	set(Call::ward_vision, 8, 2);
	set(Call::wards, 10);
	set(Call::teleports, 10);
	set(Call::altar_locks, 10);
	set(Call::occupancy, 4, 1);
	set(Call::camp, 8);
	set(Call::camp_state, 7);
	set(Call::camp_buffs, 11);
	set(Call::camp_design, 7);
	set(Call::camp_group_state, 7);
	set(Call::camp_group_cooldown, 7);
	set(Call::camp_group_capture_state, 7); // engine 2.0.0, measured (fuel probe, 108 calls)
	set(Call::is_visible, 10);
	set(Call::has_unit, 10);
	set(Call::unit_at, 10);
	set(Call::submitted_gems, 7);
	set(Call::round_number, 6);
	set(Call::item_info, 5);
	set(Call::consumable_info, 5);
	set(Call::game_settings, 6);
	// static map
	set(Call::metadata, 6);
	set(Call::map_mask, 5, 1);
	set(Call::map_symmetry, 6);
	set(Call::spawn_region, 5);
	set(Call::map_camp_query, 7);
	// actions
	set(Call::move_to, 28);
	set(Call::attack, 5);
	set(Call::cast, 11);
	set(Call::buy_item, 5);
	set(Call::buy_consumable, 4);
	set(Call::sell, 4);
	set(Call::use_consumable, 8);
	set(Call::recall, 5);
	set(Call::cancel_channel, 3);
	set(Call::submit_gems, 5);
	set(Call::place_ward, 8);
	set(Call::set_priority, 29);
	set(Call::resign, 5);
	// memory (n = bytes)
	set(Call::shared_memory_size, 5);
	set(Call::read_shared_memory, 9);
	set(Call::write_shared_memory, 9);
	set(Call::draft_memory_size, 5);
	set(Call::read_draft_memory, 8, 0, 125);
	set(Call::submit_draft_memory, 5, 0, 125);
	// draft
	set(Call::draft_num_rounds, 4);
	set(Call::draft_get, 6);
	set(Call::draft_champion, 6);
	// host geometry
	set(Call::bitboard_op, 4, 1);				// not/union/zero/shift/reflect/count...: one word per chunk
	set(Call::bitboard_shadow_cast, 5, 2, 560);	// n = tiles scanned by the shadowcaster (fit, +-~100)
	set(Call::bitboard_reachable, 0, 1, 11000); // n = BFS layers that grew (fit, +-~90)
	set(Call::distance_field, 9, 16);			// + expansions x chunks (exact); n = expansions
	per_n_chunk_milli[static_cast<int>(Call::distance_field)] = 1000;
	set(Call::nearest_by_walk, 9, 16); // the same field, rooted at the origin
	per_n_chunk_milli[static_cast<int>(Call::nearest_by_walk)] = 1000;
	set(Call::visible_camps, 0); // raw: charged as one camp call per camp instead
	set(Call::draw_shape, 16, 0, 1000);			// n = chunks covered by the shape's bounding box (+-~2)
	// misc
	set(Call::fuel_remaining, 1);
	set(Call::debug_draw, 8);
	set(Call::yield, 0);
	set(Call::compute, 0, 0, 1000); // explicit charges are passed through as n
}

const PriceTable& PriceTable::measured()
{
	static const PriceTable t;
	return t;
}

const PriceTable& PriceTable::bot_wrapper()
{
	static const PriceTable t = [] {
		PriceTable p;
#include "fuel_bot_gen.inc"
		p.bot_memo = true;
		return p;
	}();
	return t;
}
} // namespace cbs
