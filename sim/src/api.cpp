#include "cbs/api.h"
#include "cbs/coverage.h"
#include "cbs/field_memo.h"
#include <algorithm>
#include <bit>
#include <cstring>
#include <vector>

namespace cbs
{
Api::Api(Game& g, int team, int champ, const PriceTable* prices) : g_(g), team_(team), champ_(champ), prices_(prices) { fold_prices(); }

void Api::fold_prices()
{
	custom_price_ = static_cast<bool>(prices_->custom);
	if (custom_price_) return;
	const PriceContext ctx{ g_.map().W, g_.map().H };
	const std::int64_t ch = ctx.chunks();
	for (int i = 0; i < static_cast<int>(Call::count); ++i)
		folded_[i] = { prices_->base[i] + prices_->per_row[i] * ctx.map_h + prices_->per_chunk[i] * ch,
					   prices_->per_n_milli[i] + prices_->per_n_chunk_milli[i] * ch, prices_->per_n2_milli[i],
					   prices_->per_n3_milli[i] + prices_->per_n3_chunk_milli[i] * ch };
	const Folded& c = folded_[static_cast<int>(Call::compute)];
	compute_identity_ = c.fixed == 0 && c.kn == 1000 && c.kn2 == 0 && c.kn3 == 0;
}

const Bitboard& Api::vis()
{
	// Vision depends only on these fields (reveals are append-only within a round).
	std::uint64_t key = 0;
	if (playing())
	{
		const Champion& c = g_.champs[champ_];
		key = static_cast<std::uint64_t>(g_.round) << 40 | static_cast<std::uint64_t>(c.revealed_n) << 32 |
			  static_cast<std::uint64_t>(c.alive ? 1 + c.pos.x + 101 * c.pos.y : 0) << 16 |
			  static_cast<std::uint64_t>(c.ward_active ? 1 + c.ward_pos.x + 101 * c.ward_pos.y : 0);
	}
	if (key == vis_stamp_) return vis_;
	vis_stamp_ = key;
	vis_.clear();
	if (playing()) g_.champion_vision(champ_, vis_);
	return vis_;
}

bool Api::champion_visible(int h)
{
	if (h == champ_) return true;
	const Champion& c = g_.champs[h];
	return c.alive && sees(c.pos);
}

std::int32_t Api::my_champion()
{
	charge(Call::my_champion);
	return champ_;
}
std::int32_t Api::my_team()
{
	charge(Call::my_team);
	return team_;
}

Err Api::champion_is_alive(std::uint32_t h, std::int32_t* out)
{
	charge(Call::champion_is_alive);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	*out = g_.champs[h].alive;
	return Err::success;
}

Err Api::num_allies(std::uint32_t* out)
{
	charge(Call::num_allies);
	*out = 0;
	for (auto& c : g_.champs) *out += c.team == team_;
	return Err::success;
}
Err Api::num_enemies(std::uint32_t* out)
{
	charge(Call::num_enemies);
	*out = 0;
	for (auto& c : g_.champs) *out += c.team != team_;
	return Err::success;
}
Err Api::allies(std::uint32_t* out, std::uint32_t cap, std::uint32_t* count)
{
	*count = 0;
	for (auto& c : g_.champs)
		if (c.team == team_)
		{
			if (*count < cap) out[*count] = static_cast<std::uint32_t>(c.id);
			++*count;
		}
	charge(Call::allies, *count);
	return Err::success;
}
Err Api::enemies(std::uint32_t* out, std::uint32_t cap, std::uint32_t* count)
{
	*count = 0;
	for (auto& c : g_.champs)
		if (c.team != team_)
		{
			if (*count < cap) out[*count] = static_cast<std::uint32_t>(c.id);
			++*count;
		}
	charge(Call::enemies, *count);
	return Err::success;
}

Err Api::champion_at(Vec2 p, std::uint32_t* out)
{
	charge(Call::unit_at);
	if (!g_.map().in_bounds(p)) return Err::api_bad_position;
	if (!sees(p)) return Err::api_not_in_vision;
	const int c = g_.champion_at(p);
	if (c < 0) return Err::api_not_found;
	*out = static_cast<std::uint32_t>(c);
	return Err::success;
}
Err Api::camp_at(Vec2 p, std::uint32_t* out)
{
	charge(Call::unit_at);
	if (!g_.map().in_bounds(p)) return Err::api_bad_position;
	if (!sees(p)) return Err::api_not_in_vision;
	const int c = g_.camp_at(p);
	if (c < 0) return Err::api_not_found;
	*out = static_cast<std::uint32_t>(c);
	return Err::success;
}
Err Api::has_champion(Vec2 p, std::int32_t* out)
{
	charge(Call::has_unit);
	if (!g_.map().in_bounds(p)) return Err::api_bad_position;
	*out = sees(p) && g_.champion_at(p) >= 0;
	return Err::success;
}
Err Api::has_camp(Vec2 p, std::int32_t* out)
{
	charge(Call::has_unit);
	if (!g_.map().in_bounds(p)) return Err::api_bad_position;
	*out = sees(p) && g_.camp_at(p) >= 0;
	return Err::success;
}
Err Api::is_visible(Vec2 p, std::int32_t* out)
{
	charge(Call::is_visible);
	if (!g_.map().in_bounds(p)) return Err::api_bad_position;
	*out = sees(p);
	return Err::success;
}
Err Api::vision(Bitboard& out)
{
	charge(Call::vision);
	out = vis();
	return Err::success;
}
Err Api::ally_occupancy(Bitboard& out)
{
	charge(Call::occupancy);
	out.clear();
	const Bitboard& v = vis();
	for (auto& c : g_.champs)
		if (c.alive && c.team == team_ && v.test(c.pos)) out.set(c.pos);
	return Err::success;
}
Err Api::enemy_occupancy(Bitboard& out)
{
	charge(Call::occupancy);
	out.clear();
	const Bitboard& v = vis();
	for (auto& c : g_.champs)
		if (c.alive && c.team != team_ && v.test(c.pos)) out.set(c.pos);
	return Err::success;
}
Err Api::camp_occupancy(Bitboard& out, int which)
{
	charge(Call::occupancy);
	out.clear();
	const Bitboard& v = vis();
	for (auto& c : g_.camps)
		if (c.life != CampLife::dead && v.test(c.pos) &&
			(which == 0 || (which == 1 && c.life == CampLife::awake) || (which == 2 && c.life == CampLife::asleep)))
			out.set(c.pos);
	return Err::success;
}

// ---------------------------------------------------------------- champion queries

Err Api::champion(std::uint32_t h, ChampionInfo* out)
{
	charge(Call::champion);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	const Champion& c = g_.champs[h];
	const auto& d = champion_design(c.type);
	out->team = c.team;
	out->type = static_cast<std::int32_t>(c.type);
	out->x = c.alive ? c.pos.x : -1;
	out->y = c.alive ? c.pos.y : -1;
	out->health = c.hp;
	out->max_health = c.max_hp;
	out->strength = c.strength;
	out->focus = c.focus;
	out->move_speed = d.move_speed;
	out->attack_range = d.attack_range;
	out->state = g_.state_bits(static_cast<int>(h));
	return Err::success;
}

Err Api::champion_identity(std::uint32_t h, ChampionIdentity* out)
{
	charge(Call::champion_identity);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	out->team = g_.champs[h].team;
	out->type = static_cast<std::int32_t>(g_.champs[h].type);
	return Err::success;
}

Err Api::champion_restrictions(std::uint32_t h, std::uint8_t* out)
{
	charge(Call::champion_restrictions);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	*out = g_.restrictions(static_cast<int>(h));
	return Err::success;
}

Err Api::champion_ability_props(std::uint32_t h, std::uint32_t slot, AbilityProps* out)
{
	charge(Call::champion_ability_props);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (slot > 1) return Err::api_invalid_ability;
	const auto& a = champion_design(g_.champs[h].type).abilities[slot];
	*out = {};
	out->kind = static_cast<std::uint32_t>(a.kind);
	out->cooldown = a.cooldown;
	out->targets = a.targets;
	out->attributes = a.exclusive_with_movement ? 1u : 0u;
	out->range = a.range;
	out->radius = a.radius;
	out->modifier = a.modifier;
	out->duration = a.duration;
	out->enhanced_attack = a.enhanced_attack;
	return Err::success;
}

Err Api::champion_cooldown(std::uint32_t h, std::uint32_t slot, std::int32_t* out)
{
	charge(Call::champion_cooldown);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (slot > 1) return Err::api_invalid_ability;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	*out = g_.champs[h].cooldown[slot];
	return Err::success;
}

Err Api::champion_items(std::uint32_t h, std::uint32_t* out)
{
	charge(Call::champion_items);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	for (int i = 0; i < kNumItems; ++i) out[i] = static_cast<std::uint32_t>(g_.champs[h].items[i]);
	return Err::success;
}

Err Api::champion_consumables(std::uint32_t h, std::uint32_t* out)
{
	charge(Call::champion_consumables);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	for (int i = 0; i < kNumConsumables; ++i) out[i] = static_cast<std::uint32_t>(g_.champs[h].cons[i]);
	return Err::success;
}

Err Api::champion_gems(std::uint32_t h, std::uint32_t* out)
{
	charge(Call::champion_gems);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	*out = g_.champs[h].gems;
	return Err::success;
}

Err Api::champion_gold(std::uint32_t h, std::uint32_t* out)
{
	charge(Call::champion_gold);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (static_cast<int>(h) != champ_) return Err::api_not_owner;
	*out = g_.champs[h].gold_int();
	return Err::success;
}

Err Api::champion_buff_data(std::uint32_t h, BuffRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	charge(Call::champion_buff_data);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	const BuffList& b = g_.champs[h].buffs;
	*count = static_cast<std::uint32_t>(b.n);
	for (int i = 0; i < b.n && static_cast<std::uint32_t>(i) < cap; ++i)
		out[i] = { static_cast<std::uint32_t>(b.b[i].type), b.b[i].duration, b.b[i].value };
	return Err::success;
}

Err Api::champion_vision(std::uint32_t h, Bitboard& out)
{
	charge(Call::champion_vision);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (static_cast<int>(h) != champ_) return Err::api_not_owner;
	out = vis();
	return Err::success;
}

Err Api::hypothetical_vision(std::int32_t type, Vec2 p, Bitboard& out)
{
	charge(Call::hypothetical_vision);
	if (!playing()) return Err::api_not_initialized;
	if (type < 0 || type >= kNumChampionTypes) return Err::api_invalid_champion_type;
	if (!g_.map().in_bounds(p)) return Err::api_bad_position;
	out.clear();
	g_.map().add_window(g_.map().vision8(p), p, out);
	return Err::success;
}

Err Api::ward_vision(Vec2 p, Bitboard& out)
{
	charge(Call::ward_vision);
	if (!playing()) return Err::api_not_initialized;
	if (!g_.map().in_bounds(p)) return Err::api_bad_position;
	out.clear();
	g_.map().vision(p, static_cast<int>(settings().ward_vision_radius), out);
	return Err::success;
}

Err Api::champion_wards(std::uint32_t h, WardResources* out)
{
	charge(Call::champion_wards);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (static_cast<int>(h) != champ_) return Err::api_not_owner;
	out->charges = static_cast<std::uint32_t>(g_.champs[h].ward_charges);
	out->cooldown = g_.champs[h].ward_cooldown;
	return Err::success;
}

Err Api::champion_ward_positions(std::uint32_t h, Vec2* out, std::uint32_t cap, std::uint32_t* count)
{
	charge(Call::champion_ward_positions);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (static_cast<int>(h) != champ_) return Err::api_not_owner;
	const Champion& c = g_.champs[h];
	*count = c.ward_active ? 1 : 0;
	if (c.ward_active && cap > 0) out[0] = c.ward_pos;
	return Err::success;
}

Err Api::champion_channel_time(std::uint32_t h, std::int32_t* out)
{
	charge(Call::champion_channel_time);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	if (g_.champs[h].channel == Channel::none) return Err::cancel_not_channeling;
	*out = g_.champs[h].channel_timer;
	return Err::success;
}

Err Api::champion_can_shop(std::uint32_t h, bool consumables, std::int32_t* out)
{
	charge(Call::champion_can_shop);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (static_cast<int>(h) != champ_) return Err::api_not_owner;
	*out = g_.can_shop(static_cast<int>(h), consumables);
	return Err::success;
}

Err Api::champion_can_sell(std::uint32_t h, std::int32_t* out)
{
	charge(Call::champion_can_sell);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (static_cast<int>(h) != champ_) return Err::api_not_owner;
	*out = g_.can_sell(static_cast<int>(h));
	return Err::success;
}

Err Api::champion_priority(std::uint32_t h, bool next, std::int32_t* out)
{
	charge(Call::champion_priority);
	if (h >= g_.champs.size()) return Err::api_invalid_champion;
	if (!playing() || !champion_visible(static_cast<int>(h))) return Err::api_not_in_vision;
	*out = next ? g_.champs[h].next_priority : g_.champs[h].priority;
	return Err::success;
}

// ---------------------------------------------------------------- world

Err Api::camp(std::uint32_t h, CampRecord* out)
{
	charge(Call::camp);
	if (h >= g_.camps.size()) return Err::api_invalid_camp;
	const Camp& c = g_.camps[h];
	// A dead camp reads as out of vision even on a visible tile (cambc; 01starfish round 613).
	if (!playing() || !sees(c.pos) || c.life == CampLife::dead) return Err::api_not_in_vision;
	*out = { c.pos.x, c.pos.y, c.hp, c.max_hp, c.strength, c.focus, { c.cooldown[0], c.cooldown[1] } };
	return Err::success;
}

void Api::visible_camps(std::vector<std::uint32_t>& out)
{
	out.clear();
	// The deploy bot (bot_api.cpp) reads the camp occupancy and queries each occupied tile, so
	// it is priced on those tiles; otherwise one camp call per camp.
	const bool bot = prices_->bot_memo && count_charges;
	if (bot)
	{
		Bitboard occ;
		const bool counting = count_charges;
		count_charges = false;
		camp_occupancy(occ, 0);
		count_charges = counting;
		charge(Call::visible_camps, 0, occ.count(g_.map().H)); // n2: tiles (calibrated as dbits)
		count_charges = false;
	}
	// camp(c) succeeding with health > 0, on each camp (vision looked up once)
	if (playing())
	{
		const Bitboard& v = vis();
		const std::size_t n = std::min(g_.map().camps.size(), g_.camps.size());
		for (std::uint32_t c = 0; c < n; ++c)
		{
			const Camp& k = g_.camps[c];
			if (g_.map().in_bounds(k.pos) && v.test(k.pos) && k.life != CampLife::dead && k.hp > 0) out.push_back(c);
		}
	}
	if (bot) count_charges = true;
}

Err Api::camp_state(std::uint32_t h, std::uint32_t* out)
{
	charge(Call::camp_state);
	if (h >= g_.camps.size()) return Err::api_invalid_camp;
	const Camp& c = g_.camps[h];
	if (!playing() || !sees(c.pos)) return Err::api_not_in_vision;
	*out = static_cast<std::uint32_t>(c.life);
	return Err::success;
}

Err Api::camp_buffs(std::uint32_t h, CampBuffRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	charge(Call::camp_buffs);
	if (h >= g_.camps.size()) return Err::api_invalid_camp;
	const Camp& c = g_.camps[h];
	if (!playing() || !sees(c.pos)) return Err::api_not_in_vision;
	*count = static_cast<std::uint32_t>(c.buffs.n);
	for (int i = 0; i < c.buffs.n && static_cast<std::uint32_t>(i) < cap; ++i)
		out[i] = { static_cast<std::uint32_t>(c.buffs.b[i].type), c.buffs.b[i].value, c.buffs.b[i].duration };
	return Err::success;
}

Err Api::camp_group_state(std::uint32_t g, std::uint32_t* out)
{
	charge(Call::camp_group_state);
	if (g >= g_.groups.size()) return Err::api_invalid_camp_group;
	*out = 0;
	if (!playing()) return Err::success;
	// A champion keeps reporting a group it has seen respawning until it respawns; other states
	// need a visible group tile.
	if (g_.groups[g].state == GroupState::respawning)
	{
		g_.update_group_memory(champ_);
		if (g_.champs[champ_].seen_respawning[g] && g_.groups[g].respawn_timer > 0)
		{
			*out = static_cast<std::uint32_t>(GroupState::respawning);
			return Err::success;
		}
	}
	for (int h : g_.map().groups[g].camps)
		if (sees(g_.map().camps[h].pos))
		{
			*out = static_cast<std::uint32_t>(g_.groups[g].state);
			break;
		}
	return Err::success;
}

Err Api::camp_group_cooldown(std::uint32_t g, std::int32_t* out)
{
	charge(Call::camp_group_cooldown);
	if (g >= g_.groups.size()) return Err::api_invalid_camp_group;
	if (g_.groups[g].state != GroupState::respawning) return Err::api_group_not_respawning;
	*out = g_.groups[g].respawn_timer;
	return Err::success;
}

Err Api::wards(WardRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	*count = 0;
	if (playing())
	{
		const Bitboard& v = vis();
		for (auto& w : g_.wards)
			if (v.test(w.pos))
			{
				if (*count < cap) out[*count] = { static_cast<std::uint32_t>(w.team), w.pos.x, w.pos.y, -1, 0, static_cast<std::uint32_t>(w.owner) };
				++*count;
			}
	}
	charge(Call::wards, *count);
	return Err::success;
}

Err Api::teleports(TeleportRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	*count = 0;
	if (playing())
	{
		const Bitboard& v = vis();
		for (auto& c : g_.champs)
			if (c.alive && c.channel == Channel::teleport && (c.id == champ_ || v.test(c.channel_target)))
			{
				if (*count < cap)
					out[*count] = { static_cast<std::uint32_t>(c.id), static_cast<std::int32_t>(c.type), static_cast<std::uint32_t>(c.team),
									c.channel_target.x, c.channel_target.y, c.channel_timer, 4 };
				++*count;
			}
	}
	charge(Call::teleports, *count);
	return Err::success;
}

Err Api::altar_locks(AltarLockRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	*count = 0;
	if (playing())
	{
		const Bitboard& v = vis();
		for (auto& l : g_.locks)
			if (v.test(l.pos))
			{
				if (*count < cap)
					out[*count] = { static_cast<std::uint32_t>(EntityKind::altar_lock), static_cast<std::uint32_t>(l.handle), static_cast<std::uint32_t>(l.team),
									l.pos.x, l.pos.y, static_cast<std::uint32_t>(l.hits) };
				++*count;
			}
	}
	charge(Call::altar_locks, *count);
	return Err::success;
}

Err Api::submitted_gems(std::uint32_t team, std::uint32_t* out)
{
	charge(Call::submitted_gems);
	if (team > 1) return Err::api_invalid_team;
	*out = g_.teams[team].submitted;
	return Err::success;
}

Err Api::round_number(std::uint32_t* out)
{
	charge(Call::round_number);
	*out = static_cast<std::uint32_t>(g_.round);
	return Err::success;
}

// ---------------------------------------------------------------- memory

Err Api::read_shared_memory(std::int32_t off, std::uint8_t* out, std::uint32_t n)
{
	charge(Call::read_shared_memory, n);
	if (off < 0 || static_cast<std::uint32_t>(off) + n > kSharedMemory) return Err::memory_bad_range;
	std::memcpy(out, g_.teams[team_].shared + off, n);
	return Err::success;
}

Err Api::write_shared_memory(std::int32_t off, const std::uint8_t* in, std::uint32_t n)
{
	charge(Call::write_shared_memory, n);
	return g_.write_shared(team_, off, in, static_cast<int>(n));
}

Err Api::read_draft_memory(std::int32_t off, std::uint8_t* out, std::uint32_t n)
{
	charge(Call::read_draft_memory, n);
	if (off < 0 || static_cast<std::uint32_t>(off) + n > kDraftMemory) return Err::memory_bad_range;
	std::memcpy(out, g_.teams[team_].draft_mem + off, n);
	return Err::success;
}

Err Api::submit_draft_memory(const std::uint8_t* in, std::uint32_t n)
{
	charge(Call::submit_draft_memory, n);
	if (playing() || g_.draft.done) return Err::memory_draft_frozen;
	if (n > kDraftMemory) return Err::memory_bad_range;
	if (g_.teams[team_].draft_mem_size > 0) CBS_RULE_HIT("draft_memory_resubmit");
	std::memcpy(g_.teams[team_].draft_mem, in, n); // later submissions overwrite the prefix (confirmed by replay)
	g_.teams[team_].draft_mem_size = std::max(g_.teams[team_].draft_mem_size, n);
	return Err::success;
}

// ---------------------------------------------------------------- actions

#define REQUIRE_PLAYER() \
	if (!playing()) return Err::api_invalid_perspective

Err Api::move_to(Vec2 p, std::int32_t* ok)
{
	charge(Call::move_to);
	REQUIRE_PLAYER();
	bool b = false;
	const Err e = g_.move(champ_, p, b);
	*ok = b;
	return e;
}
Err Api::attack(std::uint32_t kind, std::uint32_t h)
{
	charge(Call::attack);
	REQUIRE_PLAYER();
	return g_.attack(champ_, static_cast<EntityKind>(kind), static_cast<int>(h));
}
Err Api::cast(std::uint32_t slot, std::uint32_t kind, std::uint32_t h, Vec2 p, std::int32_t* ok)
{
	charge(Call::cast);
	REQUIRE_PLAYER();
	bool b = false;
	const Err e = g_.cast(champ_, static_cast<int>(slot), static_cast<EntityKind>(kind), static_cast<int>(h), p, b);
	*ok = b;
	return e;
}
Err Api::buy_item(std::uint32_t item, std::uint32_t count)
{
	charge(Call::buy_item);
	REQUIRE_PLAYER();
	return g_.buy_item(champ_, static_cast<int>(item), static_cast<int>(count));
}
Err Api::buy_consumable(std::uint32_t type)
{
	charge(Call::buy_consumable);
	REQUIRE_PLAYER();
	return g_.buy_consumable(champ_, static_cast<int>(type));
}
Err Api::sell(std::uint32_t item)
{
	charge(Call::sell);
	REQUIRE_PLAYER();
	return g_.sell(champ_, static_cast<int>(item));
}
Err Api::use_consumable(std::int32_t type, Vec2 p, std::int32_t* ok)
{
	charge(Call::use_consumable);
	REQUIRE_PLAYER();
	bool b = false;
	const Err e = g_.use_consumable(champ_, type, p, b);
	*ok = b;
	return e;
}
Err Api::recall()
{
	charge(Call::recall);
	REQUIRE_PLAYER();
	return g_.recall(champ_);
}
Err Api::cancel_channel()
{
	charge(Call::cancel_channel);
	REQUIRE_PLAYER();
	return g_.cancel_channel(champ_);
}
Err Api::submit_gems(Vec2 altar)
{
	charge(Call::submit_gems);
	REQUIRE_PLAYER();
	return g_.submit_gems(champ_, altar);
}
Err Api::place_ward(Vec2 p, std::int32_t* ok)
{
	charge(Call::place_ward);
	REQUIRE_PLAYER();
	bool b = false;
	const Err e = g_.place_ward(champ_, p, b);
	*ok = b;
	return e;
}
Err Api::set_priority(std::int32_t p)
{
	charge(Call::set_priority);
	REQUIRE_PLAYER();
	return g_.set_priority(champ_, p);
}
Err Api::resign()
{
	charge(Call::resign);
	g_.resign(team_);
	return Err::success;
}

// ---------------------------------------------------------------- geometry

void Api::shadow_cast(const Bitboard& walls, Vec2 origin, int dist, Bitboard& out)
{
	// Price by the tiles the shadowcaster scans (the host's cost driver).
	std::int64_t scanned = 0;
	out.clear();
	const int W = g_.map().W, H = g_.map().H;
	cbs::shadowcast(
		W, H, origin, dist, [&](int x, int y) { return ++scanned, walls.test(x, y); }, [&](int x, int y) { out.set(x, y); });
	charge(Call::bitboard_shadow_cast, scanned);
}

void Api::reachable(const Bitboard& walls, Vec2 origin, int dist, Bitboard& out)
{
	// Price by BFS layers that grew: the largest distance reached.
	cbs::reachable(walls, g_.map().W, g_.map().H, origin, dist, out);
	int layers = 0;
	if (dist > 0 && out.count(g_.map().H) > 1)
	{
		Row128 seen[kMaxDim];
		Bitboard roots;
		roots.set(origin);
		bfs_layers(walls, roots, g_.map().W, g_.map().H, dist, seen, [&](auto, int, int d) { layers = d; }, [] { return false; });
	}
	charge(Call::bitboard_reachable, layers);
}

namespace
{
// A search the simulator has just run for the same request (Api::distance_field): when the memo
// misses on exactly that search, its field is copied instead of searched again. Set only around
// one memo query (no charge, so no suspension, can happen in between).
struct FieldHint
{
	const Bitboard *walls, *roots, *dests;
	int max_distance;
	const std::uint16_t* dist; // row-major
	const Bitboard* visited;
	int count;
};
thread_local const FieldHint* field_hint = nullptr;

// field_memo Ops over the simulator's BFS, with the host's ComputeTo semantics (all dests).
struct SimFieldOps
{
	using Board = Bitboard;
	int W, H, cw;
	int fidx(int x, int y) const { return ((y >> 3) * cw + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7); }
	int delta(const Board& a, const Board& b, Vec2* out, int cap) const
	{
		int n = 0;
		for (int y = 0; y < H; ++y)
			for (int k = 0; k < 2; ++k)
				for (std::uint64_t d = a.w[y][k] ^ b.w[y][k]; d; d &= d - 1)
				{
					if (n < cap) out[n] = { k * 64 + std::countr_zero(d), y };
					++n;
				}
		return n;
	}
	std::uint16_t compute(const Board& walls, const Board& roots, const Board* dests, std::uint16_t maxd, std::uint16_t* field,
						  Board& visited) const
	{
		std::fill(field, field + cw * ((H + 7) / 8) * 64, kUnreachable); // the map's chunks (fidx never reads beyond)
		// The hint's search is this one when walls, roots and the limit are the same and both stop at
		// the same single tile (first dest reached == all dests reached).
		if (const FieldHint* h = field_hint; h && &walls == h->walls && &roots == h->roots && h->max_distance == maxd && dests && h->dests &&
											   dests->count(H) == 1 && *dests == *h->dests)
		{
			visited = *h->visited;
			visited.for_each_unordered(H, [&](int x, int y) { field[fidx(x, y)] = h->dist[y * W + x]; });
			return static_cast<std::uint16_t>(h->count);
		}
		// distance_field(..., all_dests = true), written straight into the chunked layout.
		Row128 seen[kMaxDim];
		const Row128 full = W >= 128 ? ~Row128{ 0 } : (Row128{ 1 } << W) - 1;
		int left = 0;
		bool reached = false;
		if (dests)
			for (int y = 0; y < H; ++y) left += row_pop(row_of<Row128>(*dests, y) & full);
		const int n = bfs_layers(
			walls, roots, W, H, maxd, seen,
			[&](auto layer, int y, int d) {
				if (dests)
					if (const auto hit = layer & row_of<decltype(layer)>(*dests, y))
						if ((left -= row_pop(hit)) == 0) reached = true;
				std::uint16_t* row = field + ((y >> 3) * cw) * 64 + (y & 7) * 8;
				row_bits(layer, [&](int x) { row[(x >> 3) * 64 + (x & 7)] = static_cast<std::uint16_t>(d); });
			},
			[&] { return dests && reached; });
		for (int y = 0; y < kMaxDim; ++y)
		{
			visited.w[y][0] = y < H ? static_cast<std::uint64_t>(seen[y]) : 0;
			visited.w[y][1] = y < H ? static_cast<std::uint64_t>(seen[y] >> 64) : 0;
		}
		return static_cast<std::uint16_t>(n);
	}
};
using SimMemo = field_memo::Memo<SimFieldOps>;
} // namespace

Api::MemoCharge Api::memo_query(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, Vec2 me,
								bool have_me, int qr, bool compute)
{
	const int W = g_.map().W, H = g_.map().H;
	if (!field_memo_) field_memo_ = std::make_shared<SimMemo>(SimFieldOps{ W, H, (W + 7) / 8 });
	const auto ans = static_cast<SimMemo*>(field_memo_.get())->query(walls, roots, dests, max_distance, have_me, me, qr, W, H, compute);
	if (MemoStats& st = memo_stats(); st.enabled)
	{
		++st.calls;
		st.misses += ans.miss;
		st.layers += ans.layers;
	}
	return { ans.layers, ans.miss ? 1 : 0, ans.f != nullptr };
}

int Api::distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int max_distance, std::uint16_t* dist,
						Bitboard& visited)
{
	const int H = g_.map().H;
	const int n = cbs::distance_field(walls, roots, dests, g_.map().W, H, max_distance, dist, visited);
	const std::int64_t nd = dests ? dests->count(H) : 0;
	if (!prices_->bot_memo || !count_charges)
	{
		last_field = { n, nd };
		charge(Call::distance_field, n, nd);
		return n;
	}
	// As bot_api.cpp: the request as the memo sees it (reads within qr of the champion).
	const bool have_me = playing() && champion_visible(champ_);
	const Vec2 me = have_me ? g_.champs[champ_].pos : Vec2{};
	int qr = 1;
	if (dests && have_me) dests->for_each(H, [&](int x, int y) { qr = std::max(qr, field_memo::cheb(x, y, me)); });
	const FieldHint hint{ &walls, &roots, dests, max_distance, dist, &visited, n };
	field_hint = &hint;
	const MemoCharge mc = memo_query(walls, roots, dests, max_distance, me, have_me, std::min(qr, 3));
	field_hint = nullptr;
	last_field = { mc.layers, nd };
	charge(Call::distance_field, mc.layers, nd, mc.misses);
	return n;
}

std::int64_t Api::fuel_remaining()
{
	charge(Call::fuel_remaining);
	return unlimited ? (std::int64_t{ 1 } << 40) : budget - spent;
}

bool Api::nearest_by_walk(const Bitboard& walls, Vec2 origin, const Bitboard& cand, Vec2& out, int* expansions)
{
	const int W = g_.map().W, H = g_.map().H;
	// A dead champion reads (-1,-1): nothing is reachable from off the map. As bot_api.cpp, which
	// returns before any host call, so nothing is charged.
	if (origin.x < 0 || origin.y < 0 || origin.x >= W || origin.y >= H)
	{
		if (expansions) *expansions = 0;
		return false;
	}
	// cbs::distance_field from origin to cand without the field: the search stops at the first layer
	// that reaches cand, so the answer is that layer's first cand tile in row-major order.
	Row128 seen[kMaxDim];
	Bitboard roots;
	roots.set(origin);
	std::uint16_t bd = kUnreachable;
	bool found = false;
	const int n = bfs_layers(
		walls, roots, W, H, kUnreachable, seen,
		[&](auto layer, int y, int d) {
			if (found) return;
			if (const auto hit = layer & row_of<decltype(layer)>(cand, y))
			{
				out = { row_first(hit), y };
				bd = static_cast<std::uint16_t>(d);
				found = true;
			}
		},
		[&] { return found; });
	if (expansions) *expansions = n;
	if (!prices_->bot_memo || !count_charges)
	{
		last_field = { n, cand.count(H) };
		charge(Call::nearest_by_walk, n, last_field.dests);
	}
	else
	{
		// As bot_api.cpp (pricing only; the answer above is the simulator's own): per candidate
		// set (keyed by its first tile and size) the last D and what the reachable mask cost. After a
		// memo miss, when the last mask was dear, one origin-rooted search capped at the last D
		// + 2 per turn since answers instead; past the cap it falls back to the memo query.
		// Otherwise: the memo query read at origin, then a reachable mask out to D.
		struct Hist
		{
			Vec2 root0{ -1, -1 };
			int n = 0; // candidate count
			int D = 0;
			std::uint32_t round = 0;
			long long mask = 0;
			std::uint64_t used = 0;
		};
		struct Hists
		{
			Hist h[4];
			std::uint64_t clock = 0;
		};
		if (!nbw_hist_) nbw_hist_ = std::make_shared<Hists>();
		Hists& hs = *static_cast<Hists*>(nbw_hist_.get());
		const bool have_me = playing() && champion_visible(champ_) && g_.champs[champ_].pos == origin;
		Vec2 root0{ -1, -1 };
		cand.first(H, root0);
		const int ncand = cand.count(H);
		Hist* h = nullptr;
		for (Hist& e : hs.h)
			if (e.root0 == root0 && e.n == ncand) h = &e;
		const int chunks = ((W + 7) / 8) * ((H + 7) / 8);
		const auto round = static_cast<std::uint32_t>(g_.round);
		const int cap = h ? h->D + 2 + 2 * static_cast<int>(std::min<std::uint32_t>(round - h->round, 8)) : 0;
		const bool origin_on_miss = have_me && h && h->mask > static_cast<long long>(cap - h->D) * chunks + 2500;
		Bitboard o;
		o.set(origin);
		std::int64_t layers = 0, misses = 0, tiles = 1;
		MemoCharge mc = memo_query(walls, cand, &o, kUnreachable, origin, have_me, 0, !origin_on_miss);
		layers += mc.layers;
		misses += mc.misses;
		bool fast = false;
		if (!mc.answered)
		{
			// cbs::distance_field(walls, o, nullptr, cap) and the least value on cand: the first layer
			// that reaches cand (the search itself runs on to cap).
			Row128 v[kMaxDim];
			int bd = cap + 1;
			layers += bfs_layers(
				walls, o, W, H, cap, v,
				[&](auto layer, int y, int d) {
					if (d < bd && (layer & row_of<decltype(layer)>(cand, y))) bd = d;
				},
				[] { return false; });
			h->used = ++hs.clock;
			if (bd <= cap)
			{
				h->D = bd;
				h->round = round;
				fast = true;
			}
			else
			{
				mc = memo_query(walls, cand, &o, kUnreachable, origin, have_me, 0);
				layers += mc.layers;
				misses += mc.misses;
			}
		}
		if (!fast && found)
		{
			std::int64_t reach = 0; // tiles within D of origin: the mask
			for (int y = 0; y < H; ++y)
				reach += std::popcount(static_cast<std::uint64_t>(seen[y])) + std::popcount(static_cast<std::uint64_t>(seen[y] >> 64));
			tiles += reach;
			if (have_me)
			{
				if (!h)
				{
					h = &hs.h[0];
					for (Hist& e : hs.h)
						if (e.used < h->used) h = &e;
					h->root0 = root0;
					h->n = ncand;
				}
				h->D = bd;
				h->round = round;
				// The bot measures it. Estimate: ReachableMask works layer by layer on the chunks of
				// the box within k of origin (clipped to the map), so 97 + 1.54 per such chunk summed
				// over the D layers + 0.29 per tile reached (33k masks on 10 maps, tune-2 vs tune-1:
				// mae 93 fuel; large masks median 0.995).
				long long box_chunks = 0;
				for (int k = 1; k <= bd; ++k)
					box_chunks += static_cast<long long>(std::min(W - 1, origin.x + k) / 8 - std::max(0, origin.x - k) / 8 + 1) *
								  (std::min(H - 1, origin.y + k) / 8 - std::max(0, origin.y - k) / 8 + 1);
				h->mask = 97 + box_chunks * 154 / 100 + reach * 29 / 100;
				h->used = ++hs.clock;
			}
		}
		last_field = { layers, tiles };
		charge(Call::nearest_by_walk, layers, tiles, misses);
	}
	return found;
}

// ---------------------------------------------------------------- draft

Err Api::draft_num_rounds(std::uint8_t* out)
{
	charge(Call::draft_num_rounds);
	*out = static_cast<std::uint8_t>(g_.draft.rounds);
	return Err::success;
}

Err Api::draft_get(std::int32_t team, std::uint32_t round, std::int32_t* out)
{
	charge(Call::draft_get);
	if (team < 0 || team > 1) return Err::api_invalid_team;
	if (round >= static_cast<std::uint32_t>(g_.teams[team].npicks)) return Err::draft_unavailable;
	*out = g_.teams[team].picks[round];
	return Err::success;
}

Err Api::draft_champion(std::int32_t choice)
{
	charge(Call::draft_champion);
	if (playing()) return Err::draft_not_drafting;
	return g_.draft_pick(team_, choice);
}
} // namespace cbs
