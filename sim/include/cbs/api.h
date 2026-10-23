// Bot-facing API: one method per engine host import (same arguments, records and error
// codes as sdk/cpp/imports.h), evaluated from one bot's perspective. Hidden information
// is enforced here: a policy only ever sees the game through an Api.
//
// Every call is charged through the PriceTable; when the turn budget is exhausted the
// runner suspends the bot (see runner.h).
#pragma once
#include <cstdint>
#include "cbs/coro.h"
#include "cbs/fuel.h"
#include "cbs/game.h"

namespace cbs
{
// ABI records (layouts mirror sdk/cpp/imports.h).
struct ChampionInfo
{
	std::int32_t team, type, x, y;
	float health, max_health, strength, focus;
	std::int32_t move_speed, attack_range;
	std::uint32_t state;
};
struct ChampionIdentity
{
	std::int32_t team, type;
};
struct CampRecord
{
	std::int32_t x, y;
	float health, max_health, strength, focus;
	std::int32_t cooldowns[2];
};
struct CampBuffRecord
{
	std::uint32_t type;
	float magnitude;
	std::int32_t timer;
};
struct BuffRecord
{
	std::uint32_t type;
	std::int32_t duration;
	float value;
};
struct WardResources
{
	std::uint32_t charges;
	std::int32_t cooldown;
};
struct WardRecord
{
	std::uint32_t team;
	std::int32_t x, y, timer;
	std::uint8_t disabled;
	std::uint32_t owner;
};
struct TeleportRecord
{
	std::uint32_t champion;
	std::int32_t type;
	std::uint32_t team;
	std::int32_t dx, dy, timer;
	std::uint32_t channel_type;
};
struct AltarLockRecord
{
	std::uint32_t kind, handle, team;
	std::int32_t x, y;
	std::uint32_t hits_remaining;
};
struct AbilityProps
{
	std::uint32_t kind;
	std::int32_t cooldown;
	std::uint32_t max_charges, targets, attributes;
	float range, radius, modifier;
	std::int32_t duration;
	std::uint32_t enhanced_attack;
};

class Api
{
public:
	// champ = -1 for a draft bot.
	Api(Game& g, int team, int champ, const PriceTable* prices = &PriceTable::placeholder());

	Game& game() { return g_; }
	int team() const { return team_; }
	int champ() const { return champ_; }

	// ---- fuel ----
	// `spent` counts fuel used this turn against `budget`. Under a runner (coroutine attached),
	// a charge that overruns the budget suspends the bot inside the call; it resumes at its
	// next turn with the overrun carried over, and only then does the call take effect.
	std::int64_t spent = 0;
	std::int64_t budget = 0;
	bool unlimited = true; // no runner: charges are only counted
	std::uint64_t suspensions = 0;
	void charge(Call c, std::int64_t n = 0)
	{
		PriceContext ctx{ g_.map().W, g_.map().H, n };
		spent += prices_->price(c, ctx);
		if (!unlimited && coro_)
			while (spent > budget)
			{
				const std::int64_t over = spent - budget;
				++suspensions;
				coro_->yield(); // runner refills `budget` and zeroes `spent` for the next turn
				spent += over;
			}
	}
	// Charge a policy's own computation (building blocks) explicitly.
	void compute(std::int64_t fuel) { charge(Call::compute, fuel); }
	// Yield the rest of this turn.
	void end_turn()
	{
		charge(Call::yield);
		if (coro_) coro_->yield();
	}
	void attach(Coroutine* c) { coro_ = c; }

	// ---- identity, roster, occupancy ----
	std::int32_t my_champion();
	std::int32_t my_team();
	Err champion_is_alive(std::uint32_t h, std::int32_t* out);
	Err num_allies(std::uint32_t* out);
	Err num_enemies(std::uint32_t* out);
	Err allies(std::uint32_t* out, std::uint32_t cap, std::uint32_t* count);
	Err enemies(std::uint32_t* out, std::uint32_t cap, std::uint32_t* count);
	Err champion_at(Vec2 p, std::uint32_t* out);
	Err camp_at(Vec2 p, std::uint32_t* out);
	Err has_champion(Vec2 p, std::int32_t* out);
	Err has_camp(Vec2 p, std::int32_t* out);
	Err is_visible(Vec2 p, std::int32_t* out);
	Err vision(Bitboard& out);
	Err ally_occupancy(Bitboard& out);
	Err enemy_occupancy(Bitboard& out);
	Err camp_occupancy(Bitboard& out, int which /*0 all, 1 awake, 2 asleep*/);

	// ---- champion queries ----
	Err champion(std::uint32_t h, ChampionInfo* out);
	Err champion_identity(std::uint32_t h, ChampionIdentity* out);
	Err champion_restrictions(std::uint32_t h, std::uint8_t* out);
	Err champion_ability_props(std::uint32_t h, std::uint32_t slot, AbilityProps* out);
	Err champion_cooldown(std::uint32_t h, std::uint32_t slot, std::int32_t* out);
	Err champion_items(std::uint32_t h, std::uint32_t* out /*42*/);
	Err champion_consumables(std::uint32_t h, std::uint32_t* out /*4*/);
	Err champion_gems(std::uint32_t h, std::uint32_t* out);
	Err champion_gold(std::uint32_t h, std::uint32_t* out);
	Err champion_buff_data(std::uint32_t h, BuffRecord* out, std::uint32_t cap, std::uint32_t* count);
	Err champion_vision(std::uint32_t h, Bitboard& out);
	Err hypothetical_vision(std::int32_t type, Vec2 p, Bitboard& out);
	Err ward_vision(Vec2 p, Bitboard& out);
	Err champion_wards(std::uint32_t h, WardResources* out);
	Err champion_ward_positions(std::uint32_t h, Vec2* out, std::uint32_t cap, std::uint32_t* count);
	Err champion_channel_time(std::uint32_t h, std::int32_t* out);
	Err champion_can_shop(std::uint32_t h, bool consumables, std::int32_t* out);
	Err champion_can_sell(std::uint32_t h, std::int32_t* out);
	Err champion_priority(std::uint32_t h, bool next, std::int32_t* out);

	// ---- world ----
	Err camp(std::uint32_t h, CampRecord* out);
	Err camp_state(std::uint32_t h, std::uint32_t* out);
	Err camp_buffs(std::uint32_t h, CampBuffRecord* out, std::uint32_t cap, std::uint32_t* count);
	Err camp_group_state(std::uint32_t g, std::uint32_t* out);
	Err camp_group_cooldown(std::uint32_t g, std::int32_t* out);
	Err wards(WardRecord* out, std::uint32_t cap, std::uint32_t* count);
	Err teleports(TeleportRecord* out, std::uint32_t cap, std::uint32_t* count);
	Err altar_locks(AltarLockRecord* out, std::uint32_t cap, std::uint32_t* count);
	Err submitted_gems(std::uint32_t team, std::uint32_t* out);
	Err round_number(std::uint32_t* out);

	// ---- memory ----
	Err read_shared_memory(std::int32_t off, std::uint8_t* out, std::uint32_t n);
	Err write_shared_memory(std::int32_t off, const std::uint8_t* in, std::uint32_t n);
	Err read_draft_memory(std::int32_t off, std::uint8_t* out, std::uint32_t n);
	Err submit_draft_memory(const std::uint8_t* in, std::uint32_t n);

	// ---- actions ----
	Err move_to(Vec2 p, std::int32_t* ok);
	Err attack(std::uint32_t kind, std::uint32_t h);
	Err cast(std::uint32_t slot, std::uint32_t kind, std::uint32_t h, Vec2 p, std::int32_t* ok);
	Err buy_item(std::uint32_t item, std::uint32_t count);
	Err buy_consumable(std::uint32_t type);
	Err sell(std::uint32_t item);
	Err use_consumable(std::int32_t type, Vec2 p, std::int32_t* ok);
	Err recall();
	Err cancel_channel();
	Err submit_gems(Vec2 altar);
	Err place_ward(Vec2 p, std::int32_t* ok);
	Err set_priority(std::int32_t p);
	Err resign();

	// ---- static map (cached by real bots at startup) and priced geometry primitives ----
	const Map& map() const { return g_.map(); }
	void shadow_cast(const Bitboard& walls, Vec2 origin, int dist, Bitboard& out);
	void reachable(const Bitboard& walls, Vec2 origin, int dist, Bitboard& out);
	int distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, std::uint16_t* dist,
					   Bitboard& visited);

	// ---- draft ----
	Err draft_num_rounds(std::uint8_t* out);
	Err draft_get(std::int32_t team, std::uint32_t round, std::int32_t* out);
	Err draft_champion(std::int32_t choice);

	std::int64_t fuel_remaining()
	{
		charge(Call::fuel_remaining);
		return unlimited ? (std::int64_t{ 1 } << 40) : budget - spent;
	}

private:
	Game& g_;
	int team_, champ_;
	const PriceTable* prices_;
	Coroutine* coro_ = nullptr;

	bool playing() const { return champ_ >= 0; }
	const Bitboard& vis();	  // cached vision for the current game state
	bool sees(Vec2 p) { return g_.map().in_bounds(p) && vis().test(p); }
	bool champion_visible(int h);
	Bitboard vis_;
	std::uint64_t vis_stamp_ = ~0ull;
};
} // namespace cbs
