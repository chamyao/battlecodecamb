// Bot-facing API: one method per engine host import (same arguments, records and error
// codes as sdk/cpp/imports.h), evaluated from one bot's perspective. Hidden information
// is enforced here: a policy only ever sees the game through an Api.
//
// Every call is charged through the PriceTable; when the turn budget is exhausted the
// runner suspends the bot (see runner.h).
#pragma once
#include <cstdint>
#include <memory>
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

// Thrown by a charge that overruns the budget when no coroutine is attached (inline players).
struct FuelExhausted
{
	const char* what() const noexcept { return "fuel exhausted"; }
};

// Totals of the bot distance-field memo as run by the simulator. Diagnostics: collected only
// while `enabled` is set (interp/tools/fuel_turns does), single-threaded use only.
struct MemoStats
{
	bool enabled = false;
	long long calls = 0, misses = 0, layers = 0;
	long long call_n[static_cast<int>(Call::count)] = {}, call_fuel[static_cast<int>(Call::count)] = {}; // by Call, all charges
};
inline MemoStats& memo_stats()
{
	static MemoStats s;
	return s;
}

class Api
{
public:
	// champ = -1 for a draft bot.
	Api(Game& g, int team, int champ, const PriceTable* prices = &PriceTable::measured());

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
	bool count_charges = true; // false in the real bot, where the engine meters fuel itself
	std::uint64_t suspensions = 0;
	std::uint64_t api_calls = 0; // charged engine calls (not compute / yield), for per-call overheads
	// Sizes of the last distance_field / nearest_by_walk call as priced (simulator only): BFS
	// layers searched (bot memo: on a miss only) and tiles queried (nearest_by_walk under the bot
	// memo: 1 + the reachable mask's tiles). The interpreter charges its blocks on these.
	struct FieldWork
	{
		std::int64_t layers = 0, dests = 0;
	} last_field;
	void charge(Call c, std::int64_t n = 0, std::int64_t n2 = 0, std::int64_t n3 = 0)
	{
		if (!count_charges) return;
		const std::int64_t p = price(c, n, n2, n3);
		spent += p;
		if (c != Call::compute && c != Call::yield) ++api_calls;
		if (memo_stats().enabled || (!unlimited && spent > budget)) [[unlikely]]
			charge_rest(c, p);
	}
	// The rest of charge(), rarely needed: diagnostics, then the overrun (throw or suspend).
	[[gnu::noinline]] void charge_rest(Call c, std::int64_t p)
	{
		if (memo_stats().enabled && prices_->bot_memo)
		{
			MemoStats& ms = memo_stats();
			++ms.call_n[static_cast<int>(c)];
			ms.call_fuel[static_cast<int>(c)] += p;
		}
		if (!unlimited && !coro_ && spent > budget) throw FuelExhausted{};
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
	// Handles of the visible living camps (camp() succeeds with health > 0), ascending. Priced
	// as camp() on every camp handle; a real bot may find them any cheaper exact way.
	void visible_camps(std::vector<std::uint32_t>& out);
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
	// Nearest tile of `cand` from `origin` by walking distance over non-`walls` tiles (ties: first
	// in row-major order); false if none is reachable. Priced as the distance field it runs
	// (origin-rooted, stopping at the first layer touching `cand`; its expansion count goes to
	// *expansions); a real bot may compute it any cheaper exact way.
	bool nearest_by_walk(const Bitboard& walls, Vec2 origin, const Bitboard& cand, Vec2& out, int* expansions = nullptr);

	// ---- draft ----
	Err draft_num_rounds(std::uint8_t* out);
	Err draft_get(std::int32_t team, std::uint32_t round, std::int32_t* out);
	Err draft_champion(std::int32_t choice);

	// Fuel left this turn: the simulator's meter (2^40 when unlimited); the deploy bot asks the
	// engine (bot_api.cpp). Defined out of line so the bot cannot fall back to the simulator's.
	std::int64_t fuel_remaining();

private:
	Game& g_;
	int team_, champ_;
	const PriceTable* prices_;
	Coroutine* coro_ = nullptr;
	// prices_ folded with this map's size (set_prices): price = fixed + (kn n + kn2 n2 + kn3 n3) / 1000,
	// the same integers as PriceTable::price. Unused (custom) when the table has a custom function.
	struct Folded
	{
		std::int64_t fixed, kn, kn2, kn3;
	};
	Folded folded_[static_cast<int>(Call::count)];
	bool custom_price_ = true;
	void fold_prices();
	std::int64_t price(Call c, std::int64_t n, std::int64_t n2, std::int64_t n3) const
	{
		if (custom_price_)
		{
			PriceContext ctx{ g_.map().W, g_.map().H, n, n2, n3 };
			return prices_->price(c, ctx);
		}
		const Folded& f = folded_[static_cast<int>(c)];
		return f.fixed + (f.kn * n + f.kn2 * n2 + f.kn3 * n3) / 1000;
	}

	bool playing() const { return champ_ >= 0; }
	const Bitboard& vis();	  // cached vision for the current game state
	bool sees(Vec2 p) { return g_.map().in_bounds(p) && vis().test(p); }
	bool champion_visible(int h);
	Bitboard vis_;
	std::uint64_t vis_stamp_ = ~0ull;
	// Simulator only: the deploy bot's distance-field memo (cbs/field_memo.h), run to price
	// distance_field / nearest_by_walk when prices_->bot_memo. Opaque here (api.cpp).
	std::shared_ptr<void> field_memo_;
	struct MemoCharge
	{
		std::int64_t layers, misses;
		bool answered; // false: a miss with compute off (no search ran)
	};
	MemoCharge memo_query(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, Vec2 me, bool have_me, int qr,
						  bool compute = true);
	// The deploy bot's nearest_by_walk history (bot_api.cpp), mirrored for pricing.
	std::shared_ptr<void> nbw_hist_;
};
} // namespace cbs
