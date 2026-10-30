// Core types and engine constants for the cambc 2026a simulator.
// Numeric values (enums, error codes, constants) mirror the official engine; see
// docs/ENGINE_FINDINGS.md and oracle/fixtures/engine_constants.json.
#pragma once
#include <array>
#include <cstdint>
#include <cstdlib>

namespace cbs
{
constexpr int kMaxDim = 100;
constexpr int kMaxChampions = 12; // up to 6 bodies per team (Cassi & Issac count as one pick)
constexpr int kMaxCamps = 256;
constexpr int kMaxGroups = 256;
constexpr int kNumItems = 84; // engine 2.0.0: 14 families x (3 stats x shard / emblem)
constexpr int kNumConsumables = 4;
constexpr int kSharedMemory = 8;
constexpr int kDraftMemory = 1024;

struct Vec2
{
	int x = 0, y = 0;
	constexpr bool operator==(const Vec2&) const = default;
};
constexpr int chebyshev(Vec2 a, Vec2 b)
{
	const int dx = a.x > b.x ? a.x - b.x : b.x - a.x, dy = a.y > b.y ? a.y - b.y : b.y - a.y;
	return dx > dy ? dx : dy;
}

enum class Symmetry : std::uint8_t { horizontal, vertical, rotational180 };

enum class ChampionType : std::uint8_t
{
	ryth, vesper_vale, vendetta, cassi, issac, stellar, prism, marcella, willow, ren, varg, tavi, heart_of_ruin, count
};
constexpr int kNumChampionTypes = static_cast<int>(ChampionType::count);

// Draft choices; Cassi & Issac share index 3.
enum class DraftChoice : std::uint8_t
{
	ryth, vesper_vale, vendetta, cassi_and_issac, stellar, prism, marcella, willow, ren, varg, tavi, heart_of_ruin, count
};
constexpr int kNumDraftChoices = static_cast<int>(DraftChoice::count);

enum class CampType : std::uint8_t { wolf, elk, gem_cluster, gold_cluster, monolith, golem, count };

enum class AbilityKind : std::uint8_t { none, attack_reset, damage, aoe_damage, cc, heal, dash, shield };

enum class Passive : std::uint8_t
{
	none, bonus_gold, remote_shop, gem_focus, splash_attack, health_strength, reset_cooldowns_on_kill, retaliation,
	stun_immunity, omnivamp_retired, missing_health_damage
};

enum class ItemPassive : std::uint8_t { none, monster, durability, treasure, jungle, home, tribute, capture, prospector, hunter, skirmish, collectors };

namespace target
{
constexpr std::uint32_t camps = 1, enemies = 2, allies = 4, self = 8, ground = 16;
}

// Champion state bit flags (champion_info::state).
namespace state_bit
{
constexpr std::uint32_t alive = 1u << 0, recalling = 1u << 1, submitting = 1u << 2, can_move = 1u << 3, can_attack = 1u << 4,
						completed_turn = 1u << 5, recall_started = 1u << 6, submit_started = 1u << 7, recall_cancelled = 1u << 8,
						submit_cancelled = 1u << 9, can_cast = 1u << 11, teleporting = 1u << 12;
}

// Restriction bits (champion_restrictions).
namespace restrict_bit
{
constexpr std::uint8_t move = 1, attack = 2, cast = 4, shop = 8, consumable = 16, ward = 32;
}

// Entity kinds for action targets.
enum class EntityKind : std::uint32_t { none = 0, champion = 1, camp = 2, altar_lock = 6 };

// Consumable raw ids.
namespace consumable
{
constexpr int tp_crystal = 0, altar_lock = 2;
}

// Engine error codes (values mirror EngineC/Errors.h).
enum class Err : std::int32_t
{
	success = 0, invalid_handle = 1, invalid_argument = 5, invalid_draft = 12, draft_not_drafting = 13, draft_duplicate_champion = 14,
	draft_invalid_round = 15, draft_unavailable = 16, invalid_action = 18, memory_bad_range = 19, memory_draft_frozen = 20,
	move_cant_move = 21, move_bad_destination = 22, cast_invalid_source = 23, cast_invalid_slot = 24, cast_no_ability = 25,
	cast_cant_cast = 26, cast_already_cast = 27, cast_on_cooldown = 28, cast_no_charges = 29, cast_bad_target = 30,
	cast_out_of_range = 31, cast_bad_destination = 32, cant_act = 33, is_recalling = 34, is_submitting_gems = 35,
	move_already_moved = 36, move_out_of_range = 37, move_unreachable = 38, attack_invalid_source = 39, attack_cant_attack = 40,
	attack_already_attacked = 41, attack_bad_target = 42, attack_out_of_range = 43, recall_cant_channel = 44,
	submit_cant_channel = 45, submit_no_gems = 46, submit_bad_altar = 47, submit_out_of_range = 48, buy_not_on_spawn = 49,
	buy_invalid_item = 50, buy_invalid_count = 51, buy_not_enough_gold = 52, buy_inventory_full = 53, buy_stats_overflow = 54,
	buyc_not_on_spawn = 55, buyc_invalid_type = 56, buyc_invalid_count = 57, buyc_inventory_full = 58, buyc_not_enough_gold = 59,
	use_invalid_type = 60, use_not_owned = 61, ward_no_charges = 62, ward_cant_place = 63, ward_bad_destination = 64,
	ward_out_of_range = 65, teleport_bad_destination = 82, api_no_map = 87, bad_position = 88, bad_radius = 89, aliasing = 90,
	api_invalid_team = 93, api_invalid_perspective = 94, api_not_initialized = 95, api_bad_position = 96, api_not_in_vision = 97,
	api_not_found = 98, api_invalid_camp_group = 99, api_invalid_camp_info = 100, api_invalid_camp = 101, api_invalid_champion = 102,
	api_invalid_ward = 103, api_invalid_ability = 104, api_not_teammate = 105, api_group_not_respawning = 106, api_champion_alive = 107,
	api_invalid_champion_type = 108, api_invalid_camp_type = 109, api_value_out_of_range = 110, api_buffer_too_small = 111,
	api_not_owner = 112, recall_already_used = 113, submit_already_used = 114, cancel_not_channeling = 115, cancel_already_used = 116,
	ward_ally_ward_present = 117, lock_bad_altar = 118, lock_out_of_range = 119, lock_already_locked = 120, is_teleporting = 123,
	cancel_not_cancellable = 124, submit_altar_locked = 125, cast_already_moved = 126, move_exclusive_spell_cast = 127,
	sell_not_tavi = 128, sell_invalid_item = 129, sell_not_owned = 130, sell_already_sold = 131, sell_gold_overflow = 132,
	sell_not_on_spawn = 133, draft_already_picked = 134, draft_no_champion_selected = 135,
};

// ---- Design data (engine constants) ----

struct AbilityDesign
{
	AbilityKind kind = AbilityKind::none;
	int cooldown = 0;
	std::uint32_t targets = 0;
	bool exclusive_with_movement = false;
	float range = 0, radius = 0, modifier = 0;
	int duration = 0;
	bool enhanced_attack = false;
};

struct ChampionDesign
{
	Passive passive;
	bool ranged;
	int vision_radius, move_speed, attack_range;
	float base_health, health_growth, base_strength, strength_growth, base_focus, focus_growth, camp_damage_multiplier;
	AbilityDesign abilities[2];
};

struct CampDesign
{
	float vision_radius;
	int move_speed, attack_range;
	float base_health, base_strength, base_focus;
	int gold, gems, respawn;
	int ability_cooldown; // both (empty) ability slots report this cooldown
};

struct ItemDesign
{
	int cost;
	bool purchasable;
	int health_points, strength_points, focus_points;
	ItemPassive passive;
	float passive_magnitude;
	int combine_count, result, combine_cost;
};

struct Settings
{
	int capture_time = 5, camp_sleep_time = 2, respawn_time = 60, recall_time = 5;
	double submit_gem_duration_multiplier = 0.1;
	int submit_gem_base_duration = 0, submit_gem_minimum_duration = 1, submit_gems_range = 1;
	int max_rounds = 2000, winning_gems = 1000, kill_gold = 100, assist_gold = 0, passive_gold = 0;
	float spawn_healing = 1.0f;
	int active_wards = 1, ward_charges = 1, shared_memory_bytes = 8, draft_memory_bytes = 1024, tile_reveal_rounds = 1;
	int ward_cooldown = 10, ward_lifetime = -1;
	float ward_vision_radius = 6, ward_placement_radius = 2, control_ward_vision_radius = 6, control_ward_placement_radius = 2;
	int altar_lock_hits = 5, tp_scroll_time = 3, tp_crystal_time = 3;
};

const ChampionDesign& champion_design(ChampionType t);
const CampDesign& camp_design(CampType t);
const ItemDesign& item_design(int item);
struct ConsumableDesign
{
	int cost, carry_limit;
};
const ConsumableDesign& consumable_design(int c);
const Settings& settings();

} // namespace cbs
