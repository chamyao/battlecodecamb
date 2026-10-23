// Game rules. Comments tagged "RULE?" mark behaviour inferred from the handbook that is not
// yet confirmed against the engine; confirmed behaviour is documented in docs/ENGINE_FINDINGS.md.
#include "cbs/game.h"
#include <algorithm>
#include <cmath>

namespace cbs
{
namespace
{
ChampionType bodies(int choice, int which)
{
	if (choice < 3) return static_cast<ChampionType>(choice);
	if (choice == 3) return which == 0 ? ChampionType::cassi : ChampionType::issac;
	return static_cast<ChampionType>(choice + 1);
}
} // namespace

Game::Game(std::shared_ptr<const Map> map) : map_(std::move(map))
{
	draft.rounds = 5;
	camps.resize(map_->camps.size());
	for (std::size_t i = 0; i < camps.size(); ++i)
	{
		const auto& s = map_->camps[i];
		const auto& d = camp_design(s.type);
		Camp& c = camps[i];
		c.type = s.type;
		c.group = s.group;
		c.pos = s.pos;
		c.hp = c.max_hp = d.base_health;
		c.strength = d.base_strength;
		c.focus = d.base_focus;
		c.life = CampLife::asleep;
	}
	groups.resize(map_->groups.size());
}

// ---------------------------------------------------------------- draft

Err Game::draft_pick(int team, int choice)
{
	if (draft.done) return Err::draft_not_drafting;
	if (choice < 0 || choice >= kNumDraftChoices) return Err::invalid_draft;
	if (draft.pending[team] >= 0) return Err::draft_already_picked;
	const TeamState& t = teams[team];
	for (int i = 0; i < t.npicks; ++i)
		if (t.picks[i] == choice) return Err::draft_duplicate_champion;
	draft.pending[team] = choice;
	return Err::success;
}

void Game::draft_end_round(std::uint64_t& rng)
{
	for (int team = 0; team < 2; ++team)
	{
		int choice = draft.pending[team];
		if (choice < 0)
		{
			// RULE?: the engine's own random fill cannot be reproduced; use our RNG.
			int avail[kNumDraftChoices], n = 0;
			for (int k = 0; k < kNumDraftChoices; ++k)
			{
				bool used = false;
				for (int i = 0; i < teams[team].npicks; ++i) used |= teams[team].picks[i] == k;
				if (!used) avail[n++] = k;
			}
			rng ^= rng << 13, rng ^= rng >> 7, rng ^= rng << 17;
			choice = avail[rng % n];
		}
		teams[team].picks[teams[team].npicks++] = choice;
		draft.pending[team] = -1;
	}
	if (++draft.round >= draft.rounds) draft.done = true;
}

void Game::start_play()
{
	champs.clear();
	for (int team = 0; team < 2; ++team)
	{
		int slot = 0;
		for (int i = 0; i < teams[team].npicks; ++i)
		{
			const int choice = teams[team].picks[i];
			const int nb = choice == 3 ? 2 : 1;
			for (int b = 0; b < nb; ++b)
			{
				Champion ch;
				ch.id = static_cast<int>(champs.size());
				ch.team = team;
				ch.type = bodies(choice, b);
				ch.pos = spawn_slot(team, slot);
				++slot;
				recompute_stats(ch);
				ch.hp = ch.max_hp;
				ch.ward_charges = settings().ward_charges;
				ch.seen_respawning.assign(groups.size(), 0);
				champs.push_back(ch);
			}
			if (nb == 2)
			{
				champs[champs.size() - 2].partner = static_cast<int>(champs.size()) - 1;
				champs.back().partner = static_cast<int>(champs.size()) - 2;
			}
		}
	}
	round = 0;
}

// ---------------------------------------------------------------- stats

void Game::recompute_stats(Champion& ch)
{
	const auto& d = champion_design(ch.type);
	ch.health_pts = ch.strength_pts = ch.focus_pts = 0;
	ch.passives = 0;
	for (int i = 0; i < kNumItems; ++i)
	{
		if (!ch.items[i]) continue;
		const auto& it = item_design(i);
		ch.health_pts += it.health_points * ch.items[i];
		ch.strength_pts += it.strength_points * ch.items[i];
		ch.focus_pts += it.focus_points * ch.items[i];
		if (it.passive != ItemPassive::none) ch.passives |= 1u << static_cast<int>(it.passive);
	}
	ch.max_hp = d.base_health + d.health_growth * static_cast<float>(ch.health_pts);
	ch.strength = d.base_strength + d.strength_growth * static_cast<float>(ch.strength_pts);
	ch.focus = d.base_focus + d.focus_growth * static_cast<float>(ch.focus_pts);
	if (d.passive == Passive::health_strength) ch.strength += (ch.max_hp - d.base_health) * 0.01f; // RULE? rounding order
	if (d.passive == Passive::gem_focus) ch.focus += 1.5f * static_cast<float>(ch.gems);
}

void Game::grant_gold(Champion& ch, std::uint32_t amount, bool earned)
{
	int pct = 0;
	if (champion_design(ch.type).passive == Passive::bonus_gold) pct += 33;
	if (ch.has_passive(ItemPassive::treasure)) pct += 20;
	// Bonus gold is kept exactly in hundredths: amount * (100 + pct) / 100.
	const std::int64_t total = static_cast<std::int64_t>(amount) * (100 + pct);
	ch.gold_cents += total;
	if (earned)
	{
		ch.earned_gold_cents += total;
		teams[ch.team].earned_gold_cents += total;
	}
}

// ---------------------------------------------------------------- queries

int Game::champion_at(Vec2 p) const
{
	for (const auto& c : champs)
		if (c.alive && c.pos == p) return c.id;
	return -1;
}

int Game::camp_at(Vec2 p) const
{
	if (!map_->in_bounds(p)) return -1;
	// Camps never move, so only the camp spawning on the tile can be there.
	const int h = map_->camp_at[map_->idx(p)];
	return h >= 0 && camps[h].life != CampLife::dead ? h : -1;
}

int Game::lock_at(Vec2 p, int team) const
{
	for (std::size_t i = 0; i < locks.size(); ++i)
		if (locks[i].pos == p && locks[i].team == team) return static_cast<int>(i);
	return -1;
}

bool Game::tile_reserved_by_teleport(Vec2 p) const
{
	for (const auto& c : champs)
		if (c.alive && c.channel == Channel::teleport && c.channel_target == p) return true;
	return false;
}

bool Game::is_stunned(int c) const { return champs[c].buffs.has(BuffType::stun); }

std::uint8_t Game::restrictions(int c) const
{
	return is_stunned(c) ? static_cast<std::uint8_t>(0x3f) : 0; // a stun sets every restriction bit
}

std::uint32_t Game::state_bits(int c) const
{
	const Champion& ch = champs[c];
	std::uint32_t s = 0;
	if (ch.alive) s |= state_bit::alive;
	if (ch.channel == Channel::recall) s |= state_bit::recalling;
	if (ch.channel == Channel::tribute) s |= state_bit::submitting;
	if (ch.channel == Channel::teleport) s |= state_bit::teleporting;
	const bool ranged = champion_design(ch.type).ranged;
	if (ch.alive && ch.channel == Channel::none && !ch.buffs.has(BuffType::stun))
	{
		if (!ch.moved && !(ranged && (ch.attacked || ch.attack_reset)) && !ch.cast_exclusive) s |= state_bit::can_move;
		if (!ch.attacked && !(ranged && ch.moved)) s |= state_bit::can_attack;
		if (!ch.cast) s |= state_bit::can_cast;
	}
	if (ch.completed_turn) s |= state_bit::completed_turn;
	if (ch.recall_started) s |= state_bit::recall_started;
	if (ch.submit_started) s |= state_bit::submit_started;
	if (ch.recall_cancelled) s |= state_bit::recall_cancelled;
	if (ch.submit_cancelled) s |= state_bit::submit_cancelled;
	return s;
}

bool Game::can_shop(int c, bool consumables) const
{
	const Champion& ch = champs[c];
	if (!ch.alive) return true;
	if (ch.channel != Channel::none) return false; // RULE? all channels block shopping
	if (ch.buffs.has(BuffType::stun)) return false;
	if (on_spawn(ch)) return true;
	return !consumables && champion_design(ch.type).passive == Passive::remote_shop;
}

bool Game::can_sell(int c) const
{
	const Champion& ch = champs[c];
	return champion_design(ch.type).passive == Passive::remote_shop && ch.alive && ch.channel == Channel::none && !ch.buffs.has(BuffType::stun) &&
		   on_spawn(ch);
}

void Game::champion_vision(int c, Bitboard& out) const
{
	const Champion& ch = champs[c];
	if (ch.alive) map_->add_window(map_->vision8(ch.pos), ch.pos, out);
	if (ch.ward_active) map_->add_window(map_->vision6(ch.ward_pos), ch.ward_pos, out); // ward_vision_radius == 6
	for (int i = 0; i < ch.revealed_n; ++i) out.set(ch.revealed[i]);
}

int Game::channel_time(int c) const { return champs[c].channel_timer; }

float Game::apply_outgoing(const Champion& src, float amount, bool vs_camp) const
{
	// Applied sequentially in float, as the engine does: (base * (1 + missing-health bonus)) * 1.1.
	if (champion_design(src.type).passive == Passive::missing_health_damage)
		amount *= 1.0f + 0.5f * (1.0f - src.hp / src.max_hp);
	if (vs_camp && src.has_passive(ItemPassive::monster)) amount *= 1.1f;
	return amount;
}

float Game::ability_damage(int c, int slot) const
{
	const Champion& ch = champs[c];
	const auto& a = champion_design(ch.type).abilities[slot];
	return apply_outgoing(ch, a.modifier * ch.focus, false);
}
float Game::ability_heal(int c, int slot) const
{
	const Champion& ch = champs[c];
	return champion_design(ch.type).abilities[slot].modifier * ch.focus;
}
float Game::ability_shield(int c, int slot) const { return ability_heal(c, slot); }

// ---------------------------------------------------------------- combat

void Game::wake_group(int g)
{
	for (int h : map_->groups[g].camps)
		if (camps[h].life == CampLife::asleep)
		{
			camps[h].life = CampLife::awake;
			camps[h].sleep_timer = settings().camp_sleep_time;
		}
}

void Game::interrupt_channel(Champion& ch, bool by_damage)
{
	if (ch.channel == Channel::none) return;
	if (by_damage && ch.channel != Channel::recall) return;
	ch.channel = Channel::none;
	ch.channel_timer = 0;
}

void Game::damage_champion(int target, const Hit& hit)
{
	Champion& t = champs[target];
	if (!t.alive) return;
	float amount = hit.amount;
	if (t.has_passive(ItemPassive::durability)) amount *= 0.9f;			   // RULE? order
	if (hit.src_camp >= 0 && t.has_passive(ItemPassive::jungle)) amount *= 0.7f; // RULE? order
	// Shields absorb first, earliest-expiring first.
	while (amount > 0)
	{
		int best = -1;
		for (int i = 0; i < t.buffs.n; ++i)
			if (t.buffs.b[i].type == BuffType::shield && (best < 0 || t.buffs.b[i].duration < t.buffs.b[best].duration)) best = i;
		if (best < 0) break;
		Buff& s = t.buffs.b[best];
		if (s.value > amount)
		{
			s.value -= amount;
			amount = 0;
		}
		else
		{
			amount -= s.value;
			t.buffs.remove(best);
		}
	}
	t.hp -= amount;
	interrupt_channel(t, true);
	// Ren retaliation (also as he dies).
	if (champion_design(t.type).passive == Passive::retaliation && !hit.splash && !hit.retaliation && hit.src_champ != target &&
		(hit.src_champ >= 0 || hit.src_camp >= 0))
	{
		Hit back;
		back.src_champ = target;
		back.retaliation = true;
		// Outgoing modifiers apply (Monster's x1.1 against camps).
		back.amount = apply_outgoing(t, 0.2f * t.focus, hit.src_camp >= 0);
		if (hit.src_champ >= 0) damage_champion(hit.src_champ, back);
		else damage_camp(hit.src_camp, back);
	}
	if (t.hp <= 0 && t.alive) kill_champion(target, hit.src_champ);
}

void Game::damage_camp(int k, const Hit& hit)
{
	Camp& c = camps[k];
	if (c.life == CampLife::dead) return;
	c.hp -= hit.amount;
	// Damage wakes every sleeping member of the group; awake camps keep their idle count.
	wake_group(c.group);
	if (c.hp <= 0) kill_camp(k, hit.src_champ);
}

void Game::kill_champion(int target, int killer)
{
	Champion& t = champs[target];
	if (!t.alive) return;
	std::uint32_t gems = 0;
	auto die = [&](Champion& v) {
		if (!v.alive) return;
		gems += v.gems;
		v.gems = 0;
		v.alive = false;
		v.hp = 0;
		v.channel = Channel::none;
		v.channel_timer = 0;
		v.buffs.n = 0;
		v.cooldown[0] = v.cooldown[1] = 0; // abilities reset on death
		v.respawn_timer = settings().respawn_time;
		v.deaths++;
		recompute_stats(v);
	};
	die(t);
	if (t.partner >= 0) die(champs[t.partner]);
	check_capture_regions();
	if (killer >= 0 && champs[killer].team != t.team)
	{
		Champion& k = champs[killer];
		k.gems += gems;
		k.kills++;
		teams[k.team].kills++;
		grant_gold(k, static_cast<std::uint32_t>(settings().kill_gold), true);
		recompute_stats(k);
		if (champion_design(k.type).passive == Passive::reset_cooldowns_on_kill) k.cooldown[0] = k.cooldown[1] = 0;
	}
}

void Game::kill_camp(int k, int killer)
{
	Camp& c = camps[k];
	c.life = CampLife::dead;
	c.hp = 0;
	c.buffs.n = 0;
	if (killer >= 0 && champion_design(champs[killer].type).passive == Passive::reset_cooldowns_on_kill)
		champs[killer].cooldown[0] = champs[killer].cooldown[1] = 0;
	bool all_dead = true;
	for (int h : map_->groups[c.group].camps) all_dead &= camps[h].life == CampLife::dead;
	if (all_dead)
	{
		Group& g = groups[c.group];
		g.state = GroupState::reward;
		g.capture_team = -1;
		g.capture_timer = 0;
	}
}

void Game::stun_champion(int target, int duration)
{
	Champion& t = champs[target];
	if (!t.alive || champion_design(t.type).passive == Passive::stun_immunity) return;
	const int i = t.buffs.find(BuffType::stun);
	if (i >= 0) t.buffs.b[i].duration = std::max(t.buffs.b[i].duration, duration); // RULE? refresh
	else t.buffs.add({ BuffType::stun, duration, 0 });
	interrupt_channel(t, false);
}

void Game::stun_camp(int k, int duration)
{
	Camp& c = camps[k];
	if (c.life == CampLife::dead) return;
	const int i = c.buffs.find(BuffType::stun);
	if (i >= 0) c.buffs.b[i].duration = std::max(c.buffs.b[i].duration, duration);
	else c.buffs.add({ BuffType::stun, duration, 0 });
}

// ---------------------------------------------------------------- round structure

void Game::process_respawns()
{
	for (std::size_t g = 0; g < groups.size(); ++g)
	{
		Group& G = groups[g];
		if (G.state != GroupState::respawning) continue;
		if (G.respawn_timer > 0) --G.respawn_timer; // RULE? decrement before check
		if (G.respawn_timer > 0) continue;
		bool blocked = false;
		// A champion on a spawn tile, or a teleport heading there, delays the whole group.
		for (int h : map_->groups[g].camps)
			blocked |= champion_at(map_->camps[h].pos) >= 0 || tile_reserved_by_teleport(map_->camps[h].pos);
		if (blocked) continue;
		for (int h : map_->groups[g].camps)
		{
			Camp& c = camps[h];
			c.hp = c.max_hp;
			c.life = CampLife::asleep;
			c.buffs.n = 0;
			c.sleep_timer = 0;
			c.cooldown[0] = c.cooldown[1] = 0;
		}
		G.state = GroupState::alive;
		for (auto& ch : champs) ch.seen_respawning[g] = 0;
	}
}

void Game::check_capture_regions()
{
	for (std::size_t g = 0; g < groups.size(); ++g)
	{
		Group& G = groups[g];
		if (G.state != GroupState::reward || G.capture_team < 0) continue;
		bool present[2] = {};
		for (int h : map_->groups[g].camps)
		{
			const int c = champion_at(map_->camps[h].pos);
			if (c >= 0) present[champs[c].team] = true;
		}
		if (present[0] == present[1] || !present[G.capture_team])
		{
			G.capture_team = -1;
			G.capture_timer = 0;
		}
	}
}

void Game::on_position_changed(int c)
{
	check_capture_regions();
	update_group_memory(c);
}

void Game::update_group_memory(int c)
{
	Champion& ch = champs[c];
	bool any = false;
	for (const auto& G : groups) any |= G.state == GroupState::respawning;
	if (!any) return;
	Bitboard vis;
	champion_vision(c, vis);
	for (std::size_t g = 0; g < groups.size(); ++g)
		if (groups[g].state == GroupState::respawning && !ch.seen_respawning[g])
			for (int h : map_->groups[g].camps)
				if (vis.test(map_->camps[h].pos))
				{
					ch.seen_respawning[g] = 1;
					break;
				}
}

void Game::process_captures()
{
	for (std::size_t g = 0; g < groups.size(); ++g)
	{
		Group& G = groups[g];
		if (G.state != GroupState::reward) continue;
		bool present[2] = {};
		for (int h : map_->groups[g].camps)
		{
			const int c = champion_at(map_->camps[h].pos);
			if (c >= 0) present[champs[c].team] = true;
		}
		if (present[0] == present[1])
		{
			G.capture_team = -1;
			G.capture_timer = 0;
			continue;
		}
		const int team = present[0] ? 0 : 1;
		if (G.capture_team != team)
		{
			G.capture_team = team;
			G.capture_timer = settings().capture_time;
		}
		else if (--G.capture_timer > 0)
			continue;
		if (G.capture_timer > 0) continue;
		// Reward: split among allies on the region; lowest id gets the remainder.
		int who[kMaxChampions], n = 0;
		for (int h : map_->groups[g].camps)
		{
			const int c = champion_at(map_->camps[h].pos);
			if (c >= 0) who[n++] = c;
		}
		std::sort(who, who + n);
		const auto& info = map_->groups[g];
		for (int i = 0; i < n; ++i)
		{
			Champion& ch = champs[who[i]];
			std::uint32_t gold = static_cast<std::uint32_t>(info.gold / n), gems = static_cast<std::uint32_t>(info.gems / n);
			if (i == 0)
			{
				gold += static_cast<std::uint32_t>(info.gold % n);
				gems += static_cast<std::uint32_t>(info.gems % n);
			}
			ch.gems += gems;
			grant_gold(ch, gold, true);
			recompute_stats(ch);
		}
		G.state = GroupState::respawning;
		G.respawn_timer = info.respawn;
		G.capture_team = -1;
		G.capture_timer = 0;
		for (auto& ch : champs) update_group_memory(ch.id); // champions watching the region see it start respawning
	}
}

void Game::camp_turn(int k)
{
	Camp& c = camps[k];
	if (c.life == CampLife::dead) return;
	// Turn start: expire zero-timer buffs.
	for (int i = c.buffs.n - 1; i >= 0; --i)
		if (c.buffs.b[i].duration <= 0) c.buffs.remove(i);
	if (c.life == CampLife::awake)
	{
		const auto& d = camp_design(c.type);
		auto nearest = [&]() {
			// Nearest champion by Chebyshev distance; ties go to the earliest in this round's turn order.
			int best = -1, bestd = 1 << 30;
			for (int id : round_order_)
			{
				const Champion& ch = champs[id];
				if (!ch.alive) continue;
				const int dist = chebyshev(ch.pos, c.pos);
				if (dist <= d.attack_range && dist < bestd)
				{
					best = ch.id;
					bestd = dist;
				}
			}
			return best;
		};
		// A champion in range resets the sleep timer even while stunned; a stunned camp just cannot attack.
		const bool stunned = c.buffs.has(BuffType::stun);
		const int target = nearest();
		if (target >= 0)
		{
			c.sleep_timer = settings().camp_sleep_time;
			if (c.strength > 0 && !stunned)
			{
				Hit h;
				h.src_camp = k;
				h.amount = c.strength;
				h.basic = true;
				damage_champion(target, h);
			}
		}
		else if (c.sleep_timer <= 0)
			c.life = CampLife::asleep; // RULE? health is kept
	}
	if (c.sleep_timer > 0) --c.sleep_timer;
	// Turn end: decrement cooldowns and buffs.
	for (int s = 0; s < 2; ++s)
		if (c.cooldown[s] > 0) --c.cooldown[s];
	for (int i = 0; i < c.buffs.n; ++i)
		if (c.buffs.b[i].duration > 0) --c.buffs.b[i].duration;
}

void Game::begin_round()
{
	++round;
	for (auto& ch : champs)
	{
		ch.priority = ch.next_priority;
		ch.revealed_n = 0;
		ch.completed_turn = false;
		// Per-turn allowances reset at round start (visible on allies before they act).
		ch.moved = ch.attacked = ch.cast = ch.cast_exclusive = false;
		ch.recall_started = ch.submit_started = ch.recall_cancelled = ch.submit_cancelled = ch.sold = false;
		ch.attack_reset = false;
	}
	turn_order(round_order_);
	process_respawns();
	process_captures();
	for (std::size_t k = 0; k < camps.size(); ++k) camp_turn(static_cast<int>(k));
}

void Game::turn_order(std::vector<int>& out) const
{
	out.clear();
	std::vector<int> t[2];
	for (const auto& ch : champs) t[ch.team].push_back(ch.id);
	for (auto& v : t)
		std::stable_sort(v.begin(), v.end(), [&](int a, int b) { return champs[a].priority > champs[b].priority; });
	const int first = (round % 2 == 1) ? 0 : 1;
	const std::size_t n = std::max(t[0].size(), t[1].size());
	for (std::size_t i = 0; i < n; ++i)
		for (int s = 0; s < 2; ++s)
		{
			const auto& v = t[s == 0 ? first : 1 - first];
			if (i < v.size()) out.push_back(v[i]);
		}
}

void Game::respawn_champion(int c)
{
	Champion& ch = champs[c];
	Vec2 p;
	if (!free_spawn_tile(ch.team, p)) return;
	ch.alive = true;
	ch.pos = p;
	recompute_stats(ch);
	ch.hp = ch.max_hp;
	ch.cooldown[0] = ch.cooldown[1] = 0;
	ch.buffs.n = 0;
}

Vec2 Game::spawn_slot(int team, int i) const
{
	// Team A's slots run row-major through its box; team B's are their mirror images.
	const Box& a = map_->spawn[0];
	const int w = a.max_x - a.min_x;
	const Vec2 pa{ a.min_x + i % w, a.min_y + i / w };
	return team == 0 ? pa : map_->mirror(pa);
}

bool Game::free_spawn_tile(int team, Vec2& out) const
{
	const Box& a = map_->spawn[0];
	const int n = (a.max_x - a.min_x) * (a.max_y - a.min_y);
	for (int i = 0; i < n; ++i)
	{
		const Vec2 p = spawn_slot(team, i);
		if (champion_at(p) < 0 && !tile_reserved_by_teleport(p))
		{
			out = p;
			return true;
		}
	}
	return false;
}

void Game::complete_channel(int c)
{
	Champion& ch = champs[c];
	const Channel kind = ch.channel;
	ch.channel = Channel::none;
	switch (kind)
	{
	case Channel::recall:
	{
		Vec2 p;
		if (free_spawn_tile(ch.team, p)) ch.pos = p;
		on_position_changed(c);
		break;
	}
	case Channel::tribute:
	{
		const std::uint32_t g = ch.gems;
		ch.gems = 0;
		teams[ch.team].submitted += g;
		if (champion_design(ch.type).passive == Passive::stun_immunity) grant_gold(ch, 2 * g, true);
		recompute_stats(ch);
		check_win(ch.team);
		break;
	}
	case Channel::teleport:
		if (champion_at(ch.channel_target) < 0 && camp_at(ch.channel_target) < 0) ch.pos = ch.channel_target; // RULE?
		on_position_changed(c);
		break;
	default: break;
	}
}

void Game::begin_turn(int c)
{
	Champion& ch = champs[c];
	update_group_memory(c);
	if (!ch.alive && ch.respawn_timer <= 0) respawn_champion(c);
	if (ch.ward_charges < settings().ward_charges && ch.ward_cooldown <= 0) ch.ward_charges++; // also while dead
	if (!ch.alive) return;
	for (int i = ch.buffs.n - 1; i >= 0; --i)
		if (ch.buffs.b[i].duration <= 0) ch.buffs.remove(i);
	if (ch.channel != Channel::none && ch.channel_timer <= 0) complete_channel(c);
}

void Game::end_turn(int c)
{
	update_group_memory(c);
	Champion& ch = champs[c];
	ch.completed_turn = true;
	ch.recall_started = ch.submit_started = ch.recall_cancelled = ch.submit_cancelled = false; // per-turn channel flags
	for (int s = 0; s < 2; ++s)
		if (ch.cooldown[s] > 0) --ch.cooldown[s];
	for (int i = 0; i < ch.buffs.n; ++i)
		if (ch.buffs.b[i].duration > 0) --ch.buffs.b[i].duration;
	if (ch.channel != Channel::none && ch.channel_timer > 0) --ch.channel_timer;
	if (ch.ward_cooldown > 0) --ch.ward_cooldown;
	if (!ch.alive)
	{
		if (ch.respawn_timer > 0) --ch.respawn_timer;
		return;
	}
	if (on_spawn(ch)) ch.hp = std::min(ch.max_hp, ch.hp + settings().spawn_healing * ch.max_hp);
}

void Game::check_win(int team)
{
	if (!over && teams[team].submitted >= static_cast<std::uint32_t>(settings().winning_gems))
	{
		over = true;
		result.winner = team;
		result.reason = 1;
		result.rounds = round;
	}
}

void Game::end_round()
{
	if (over || round < settings().max_rounds) return;
	over = true;
	result.reason = 2;
	result.rounds = round;
	const TeamState &a = teams[0], &b = teams[1];
	if (a.submitted != b.submitted) result.winner = a.submitted > b.submitted ? 0 : 1;
	else if (a.earned_gold_cents != b.earned_gold_cents) result.winner = a.earned_gold_cents > b.earned_gold_cents ? 0 : 1;
	else if (a.kills != b.kills) result.winner = a.kills > b.kills ? 0 : 1;
	else result.winner = 1;
}

void Game::resign(int team)
{
	if (over) return;
	over = true;
	result.winner = 1 - team;
	result.reason = 3;
	result.rounds = round;
}

// ---------------------------------------------------------------- actions

Err Game::common_action_checks(const Champion& ch) const
{
	if (!ch.alive) return Err::cant_act; // RULE?
	if (ch.channel == Channel::recall) return Err::is_recalling;
	if (ch.channel == Channel::tribute) return Err::is_submitting_gems;
	if (ch.channel == Channel::teleport) return Err::is_teleporting;
	return Err::success;
}

bool Game::landing_ok(const Champion& ch, Vec2 to, bool& hidden_block, bool known_only) const
{
	hidden_block = false;
	if (!map_->in_bounds(to)) return false;
	if (map_->walls.test(to) || map_->holes.test(to) || map_->altars.test(to)) return false;
	if (map_->spawn[1 - ch.team].contains(to)) return false;
	if (to == ch.pos) return false;
	const bool occupied = champion_at(to) >= 0 || camp_at(to) >= 0 || tile_reserved_by_teleport(to);
	if (!occupied) return true;
	Bitboard vis;
	champion_vision(ch.id, vis);
	if (vis.test(to)) return false;
	hidden_block = true;
	return true;
}

Err Game::move(int c, Vec2 to, bool& ok)
{
	ok = false;
	Champion& ch = champs[c];
	if (is_stunned(c)) return Err::move_cant_move; // RULE?
	if (Err e = common_action_checks(ch); e != Err::success) return e;
	if (ch.moved) return Err::move_already_moved;
	if (ch.cast_exclusive) return Err::move_exclusive_spell_cast;
	const bool ranged = champion_design(ch.type).ranged;
	if (ranged && (ch.attacked || ch.attack_reset)) return Err::move_cant_move; // a reset restores the attack, not the walk
	bool hidden = false;
	if (!landing_ok(ch, to, hidden, true)) return Err::move_bad_destination;
	if (chebyshev(ch.pos, to) > champion_design(ch.type).move_speed) return Err::move_unreachable;
	if (hidden)
	{
		if (ch.revealed_n < 8) ch.revealed[ch.revealed_n++] = to;
		return Err::success;
	}
	ch.pos = to;
	ch.moved = true;
	ok = true;
	on_position_changed(c);
	return Err::success;
}

void Game::apply_basic_attack(int c, EntityKind kind, int handle)
{
	Champion& ch = champs[c];
	const auto& d = champion_design(ch.type);
	const bool enhanced = ch.buffs.has(BuffType::enhanced_attack);
	if (enhanced) ch.buffs.remove(ch.buffs.find(BuffType::enhanced_attack));
	auto hit_unit = [&](EntityKind k, int h, float base, bool splash) {
		Hit hit;
		hit.src_champ = c;
		hit.basic = true;
		hit.splash = splash;
		if (k == EntityKind::champion)
		{
			hit.amount = apply_outgoing(ch, base, false);
			damage_champion(h, hit);
			if (enhanced) stun_champion(h, 1);
		}
		else
		{
			hit.amount = apply_outgoing(ch, base, true) * d.camp_damage_multiplier;
			damage_camp(h, hit);
			if (enhanced) stun_camp(h, 1);
		}
	};
	const Vec2 tp = kind == EntityKind::champion ? champs[handle].pos : camps[handle].pos;
	hit_unit(kind, handle, ch.strength, false);
	if (d.passive == Passive::splash_attack)
	{
		for (auto& o : champs)
			if (o.alive && o.team != ch.team && !(kind == EntityKind::champion && o.id == handle) && chebyshev(o.pos, tp) <= 1)
				hit_unit(EntityKind::champion, o.id, ch.strength, true);
		for (int dy = -1; dy <= 1; ++dy)
			for (int dx = -1; dx <= 1; ++dx)
			{
				const int k = camp_at({ tp.x + dx, tp.y + dy });
				if (k >= 0 && !(kind == EntityKind::camp && k == handle)) hit_unit(EntityKind::camp, k, ch.strength, true);
			}
	}
}

Err Game::attack(int c, EntityKind kind, int handle)
{
	Champion& ch = champs[c];
	if (is_stunned(c)) return Err::attack_cant_attack;
	if (Err e = common_action_checks(ch); e != Err::success) return e;
	const bool ranged = champion_design(ch.type).ranged;
	Bitboard vis;
	champion_vision(c, vis);
	// Order: target validity (42), allowance (41/40), range (43).
	Vec2 tp;
	int li = -1;
	if (kind == EntityKind::champion)
	{
		if (handle < 0 || handle >= static_cast<int>(champs.size())) return Err::attack_bad_target;
		const Champion& t = champs[handle];
		if (!t.alive || t.team == ch.team || !vis.test(t.pos)) return Err::attack_bad_target;
		tp = t.pos;
	}
	else if (kind == EntityKind::camp)
	{
		if (handle < 0 || handle >= static_cast<int>(camps.size())) return Err::attack_bad_target;
		const Camp& t = camps[handle];
		if (t.life == CampLife::dead || !vis.test(t.pos)) return Err::attack_bad_target;
		tp = t.pos;
	}
	else if (kind == EntityKind::altar_lock)
	{
		for (std::size_t i = 0; i < locks.size(); ++i)
			if (locks[i].handle == handle) li = static_cast<int>(i);
		if (li < 0 || locks[li].team == ch.team || !vis.test(locks[li].pos)) return Err::attack_bad_target;
		tp = locks[li].pos;
	}
	else
		return Err::attack_bad_target;
	if (ch.attacked) return Err::attack_already_attacked;
	if (ranged && ch.moved) return Err::attack_cant_attack;
	if (chebyshev(ch.pos, tp) > champion_design(ch.type).attack_range) return Err::attack_out_of_range;
	ch.attacked = true;
	ch.attack_reset = false;
	if (li >= 0)
	{
		if (--locks[li].hits <= 0) locks.erase(locks.begin() + li);
		return Err::success;
	}
	apply_basic_attack(c, kind, handle);
	return Err::success;
}

Err Game::cast(int c, int slot, EntityKind kind, int handle, Vec2 dest, bool& ok)
{
	ok = false;
	Champion& ch = champs[c];
	if (is_stunned(c)) return Err::cast_cant_cast;
	if (Err e = common_action_checks(ch); e != Err::success) return e;
	if (slot < 0 || slot > 1) return Err::cast_invalid_slot;
	const auto& d = champion_design(ch.type);
	const AbilityDesign& a = d.abilities[slot];
	if (a.kind == AbilityKind::none) return Err::cast_no_ability;
	if (ch.cast) return Err::cast_already_cast;
	if (ch.cooldown[slot] > 0) return Err::cast_on_cooldown;
	// An attack reset needs a spent basic attack to restore.
	if (a.kind == AbilityKind::attack_reset && !ch.attacked) return Err::cast_cant_cast;
	if (a.exclusive_with_movement && ch.moved) return Err::cast_already_moved;
	Bitboard vis;
	champion_vision(c, vis);
	// Unit-targeted casts of ground abilities land on the target's tile.
	if ((a.kind == AbilityKind::aoe_damage || a.kind == AbilityKind::dash) && kind != EntityKind::none)
	{
		if (kind == EntityKind::champion && handle >= 0 && handle < static_cast<int>(champs.size()) && champs[handle].alive && vis.test(champs[handle].pos))
			dest = champs[handle].pos;
		else if (kind == EntityKind::camp && handle >= 0 && handle < static_cast<int>(camps.size()) && camps[handle].life != CampLife::dead &&
				 vis.test(camps[handle].pos))
			dest = camps[handle].pos;
		else
			return Err::cast_bad_target;
	}
	auto finish = [&]() {
		ch.cast = true;
		ch.cooldown[slot] = a.cooldown;
		if (a.exclusive_with_movement) ch.cast_exclusive = true;
		ok = true;
		return Err::success;
	};
	auto in_range = [&](Vec2 p) { return chebyshev(ch.pos, p) <= a.range; };
	switch (a.kind)
	{
	case AbilityKind::attack_reset:
		ch.attacked = false;
		ch.attack_reset = true;
		if (a.enhanced_attack)
		{
			const int i = ch.buffs.find(BuffType::enhanced_attack);
			if (i >= 0) ch.buffs.remove(i);
			ch.buffs.add({ BuffType::enhanced_attack, 1, 0 }); // RULE? duration
		}
		return finish();
	case AbilityKind::shield:
		ch.buffs.add({ BuffType::shield, a.duration, a.modifier * ch.focus });
		return finish();
	case AbilityKind::damage:
	case AbilityKind::cc:
	case AbilityKind::heal:
	{
		if (kind == EntityKind::champion)
		{
			if (handle < 0 || handle >= static_cast<int>(champs.size())) return Err::cast_bad_target;
			const Champion& t = champs[handle];
			const bool ally = t.team == ch.team;
			if (!t.alive || !vis.test(t.pos)) return Err::cast_bad_target;
			if (t.id == c && !(a.targets & target::self)) return Err::cast_bad_target;
			if (t.id != c && ally && !(a.targets & target::allies)) return Err::cast_bad_target;
			if (!ally && !(a.targets & target::enemies)) return Err::cast_bad_target;
			if (!in_range(t.pos)) return Err::cast_out_of_range;
			if (a.kind == AbilityKind::heal)
				champs[handle].hp = std::min(champs[handle].max_hp, champs[handle].hp + a.modifier * ch.focus);
			else
			{
				// Even a zero-damage hit (Cassi's stun) counts as damage, e.g. for Ren's retaliation.
				Hit h;
				h.src_champ = c;
				h.amount = apply_outgoing(ch, a.modifier * ch.focus, false);
				damage_champion(handle, h);
				if (a.kind == AbilityKind::cc) stun_champion(handle, a.duration);
			}
			return finish();
		}
		if (kind == EntityKind::camp)
		{
			if (!(a.targets & target::camps)) return Err::cast_bad_target;
			if (handle < 0 || handle >= static_cast<int>(camps.size())) return Err::cast_bad_target;
			const Camp& t = camps[handle];
			if (t.life == CampLife::dead || !vis.test(t.pos)) return Err::cast_bad_target;
			if (!in_range(t.pos)) return Err::cast_out_of_range;
			{
				Hit h;
				h.src_champ = c;
				h.amount = apply_outgoing(ch, a.modifier * ch.focus, true);
				damage_camp(handle, h);
			}
			if (a.kind == AbilityKind::cc) stun_camp(handle, a.duration);
			return finish();
		}
		return Err::cast_bad_target;
	}
	case AbilityKind::aoe_damage:
	{
		if (!map_->in_bounds(dest)) return Err::cast_bad_destination;
		if (!in_range(dest)) return Err::cast_out_of_range;
		const int r = static_cast<int>(a.radius);
		const float dmg_c = apply_outgoing(ch, a.modifier * ch.focus, false);
		const float dmg_k = apply_outgoing(ch, a.modifier * ch.focus, true);
		for (auto& o : champs)
			if (o.alive && o.team != ch.team && chebyshev(o.pos, dest) <= r)
			{
				Hit h;
				h.src_champ = c;
				h.amount = dmg_c;
				damage_champion(o.id, h);
				if (a.duration > 0) stun_champion(o.id, a.duration);
			}
		for (int dy = -r; dy <= r; ++dy)
			for (int dx = -r; dx <= r; ++dx)
			{
				const int k = camp_at({ dest.x + dx, dest.y + dy });
				if (k < 0) continue;
				Hit h;
				h.src_champ = c;
				h.amount = dmg_k;
				damage_camp(k, h);
				if (a.duration > 0) stun_camp(k, a.duration);
			}
		return finish();
	}
	case AbilityKind::dash:
	{
		if (!map_->in_bounds(dest)) return Err::cast_bad_destination;
		if (chebyshev(ch.pos, dest) > a.range) return Err::cast_out_of_range;
		bool hidden = false;
		if (!landing_ok(ch, dest, hidden, true)) return Err::cast_bad_destination;
		// Legal dash path: one intermediate king step that is not a wall and holds no camp or
		// enemy champion the caster can see (holes may be crossed, allies and unseen enemies passed
		// through). RULE? unseen camps, altars
		bool path = chebyshev(ch.pos, dest) <= 1;
		Bitboard vis;
		if (!path) champion_vision(c, vis);
		for (int dy = -1; dy <= 1 && !path; ++dy)
			for (int dx = -1; dx <= 1 && !path; ++dx)
			{
				const Vec2 mid{ ch.pos.x + dx, ch.pos.y + dy };
				const int occ = champion_at(mid);
				if (map_->in_bounds(mid) && !map_->walls.test(mid) && chebyshev(mid, dest) <= 1 &&
					(occ < 0 || champs[occ].team == ch.team || !vis.test(mid)) && camp_at(mid) < 0)
					path = true;
			}
		if (!path) return Err::cast_bad_destination;
		if (hidden)
		{
			if (ch.revealed_n < 8) ch.revealed[ch.revealed_n++] = dest;
			return Err::success;
		}
		ch.pos = dest;
		on_position_changed(c);
		if (a.modifier > 0 || a.duration > 0)
		{
			const int r = static_cast<int>(a.radius);
			for (auto& o : champs)
				if (o.alive && o.team != ch.team && chebyshev(o.pos, dest) <= r)
				{
					if (a.modifier > 0)
					{
						Hit h;
						h.src_champ = c;
						h.amount = apply_outgoing(ch, a.modifier * ch.focus, false);
						damage_champion(o.id, h);
					}
					if (a.duration > 0) stun_champion(o.id, a.duration);
				}
			for (int dy = -r; dy <= r; ++dy)
				for (int dx = -r; dx <= r; ++dx)
				{
					const int k = camp_at({ dest.x + dx, dest.y + dy });
					if (k < 0) continue;
					if (a.modifier > 0)
					{
						Hit h;
						h.src_champ = c;
						h.amount = apply_outgoing(ch, a.modifier * ch.focus, true);
						damage_camp(k, h);
					}
					if (a.duration > 0) stun_camp(k, a.duration);
				}
		}
		return finish();
	}
	default: return Err::cast_no_ability;
	}
}

Err Game::buy_item(int c, int item, int count)
{
	Champion& ch = champs[c];
	if (ch.alive && is_stunned(c)) return Err::cant_act;
	if (ch.alive && ch.channel != Channel::none) return common_action_checks(ch);
	if (!can_shop(c, false)) return Err::buy_not_on_spawn;
	if (item < 0 || item >= kNumItems || !item_design(item).purchasable) return Err::buy_invalid_item;
	if (count <= 0) return Err::buy_invalid_count;
	const auto& it = item_design(item);
	const std::uint64_t cost = static_cast<std::uint64_t>(it.cost) * static_cast<std::uint64_t>(count);
	if (static_cast<std::int64_t>(cost) * 100 > ch.gold_cents) return Err::buy_not_enough_gold;
	ch.gold_cents -= static_cast<std::int64_t>(cost) * 100;
	ch.spent_gold += cost;
	const float old_max = ch.max_hp;
	ch.items[item] += count;
	while (it.combine_count > 0 && ch.items[item] >= it.combine_count)
	{
		ch.items[item] -= it.combine_count;
		ch.items[it.result] += 1;
	}
	recompute_stats(ch);
	if (ch.alive && on_spawn(ch) && ch.max_hp > old_max) ch.hp = std::min(ch.max_hp, ch.hp + (ch.max_hp - old_max));
	return Err::success;
}

Err Game::buy_consumable(int c, int type)
{
	Champion& ch = champs[c];
	if (type < 0 || type >= kNumConsumables || consumable_design(type).carry_limit == 0) return Err::buyc_invalid_type;
	if (ch.alive && is_stunned(c)) return Err::cant_act; // RULE? order vs invalid type
	if (ch.alive && ch.channel != Channel::none) return common_action_checks(ch);
	if (!can_shop(c, true)) return Err::buyc_not_on_spawn;
	if (ch.cons[type] >= consumable_design(type).carry_limit) return Err::buyc_inventory_full;
	if (ch.gold_cents < static_cast<std::int64_t>(consumable_design(type).cost) * 100) return Err::buyc_not_enough_gold;
	ch.gold_cents -= static_cast<std::int64_t>(consumable_design(type).cost) * 100;
	ch.spent_gold += static_cast<std::uint64_t>(consumable_design(type).cost);
	ch.cons[type]++;
	return Err::success;
}

Err Game::sell(int c, int item)
{
	Champion& ch = champs[c];
	if (champion_design(ch.type).passive != Passive::remote_shop) return Err::sell_not_tavi;
	if (ch.alive && ch.channel != Channel::none) return common_action_checks(ch);
	if (is_stunned(c)) return Err::cant_act; // RULE? order vs the Tavi/channel checks
	if (item < 0 || item >= kNumItems) return Err::sell_invalid_item;
	if (ch.items[item] <= 0) return Err::sell_not_owned;
	if (!can_sell(c)) return Err::sell_not_on_spawn;
	if (ch.sold) return Err::sell_already_sold;
	ch.items[item]--;
	ch.gold_cents += static_cast<std::int64_t>(item_design(item).cost) * 100;
	ch.sold = true;
	recompute_stats(ch);
	ch.hp = std::min(ch.hp, ch.max_hp);
	return Err::success;
}

Err Game::use_consumable(int c, int type, Vec2 dest, bool& ok)
{
	ok = false;
	Champion& ch = champs[c];
	if (type < 0 || type >= kNumConsumables || consumable_design(type).carry_limit == 0) return Err::use_invalid_type;
	if (is_stunned(c)) return Err::cant_act;
	if (Err e = common_action_checks(ch); e != Err::success) return e;
	if (ch.cons[type] <= 0) return Err::use_not_owned;
	if (type == consumable::altar_lock)
	{
		if (!map_->in_bounds(dest) || !map_->altars.test(dest)) return Err::lock_bad_altar;
		if (chebyshev(ch.pos, dest) > 2) return Err::lock_out_of_range;
		if (lock_at(dest, ch.team) >= 0) return Err::lock_already_locked; // each team may hold one lock per altar
		locks.push_back({ next_lock_handle++, ch.team, dest, settings().altar_lock_hits });
		for (auto& o : champs) // cancels every tribute at the altar, allies' included
			if (o.channel == Channel::tribute && o.channel_target == dest)
			{
				o.channel = Channel::none;
				o.channel_timer = 0;
			}
		ch.cons[type]--;
		ok = true;
		return Err::success;
	}
	// Teleport crystal: validated like a move (codes 22 / 37).
	bool hidden = false;
	if (!landing_ok(ch, dest, hidden, true)) return Err::move_bad_destination;
	if (chebyshev(ch.pos, dest) > 3) return Err::move_out_of_range; // RULE? code
	if (hidden)
	{
		if (ch.revealed_n < 8) ch.revealed[ch.revealed_n++] = dest;
		return Err::success;
	}
	ch.cons[type]--;
	ch.channel = Channel::teleport;
	ch.channel_timer = settings().tp_crystal_time;
	ch.channel_target = dest;
	ok = true;
	return Err::success;
}

Err Game::recall(int c)
{
	Champion& ch = champs[c];
	if (ch.recall_started) return Err::recall_already_used;
	if (is_stunned(c)) return Err::recall_cant_channel; // RULE?
	if (Err e = common_action_checks(ch); e != Err::success) return e == Err::is_recalling ? Err::recall_cant_channel : e;
	ch.channel = Channel::recall;
	const int t = settings().recall_time;
	ch.channel_timer = ch.has_passive(ItemPassive::home) ? (t + 1) / 2 : t;
	ch.channel_target = ch.pos;
	ch.recall_started = true;
	return Err::success;
}

Err Game::cancel_channel(int c)
{
	Champion& ch = champs[c];
	if (ch.channel == Channel::none) return Err::cancel_not_channeling;
	if (ch.channel == Channel::teleport) return Err::cancel_not_cancellable;
	if (ch.recall_cancelled || ch.submit_cancelled) return Err::cancel_already_used;
	if (ch.channel == Channel::recall) ch.recall_cancelled = true;
	else ch.submit_cancelled = true;
	ch.channel = Channel::none;
	ch.channel_timer = 0;
	return Err::success;
}

Err Game::submit_gems(int c, Vec2 altar)
{
	Champion& ch = champs[c];
	if (ch.submit_started) return Err::submit_already_used;
	if (Err e = common_action_checks(ch); e != Err::success) return e;
	if (!map_->in_bounds(altar) || !map_->altars.test(altar)) return Err::submit_bad_altar;
	if (chebyshev(ch.pos, altar) > settings().submit_gems_range) return Err::submit_out_of_range;
	if (ch.gems == 0) return Err::submit_no_gems;
	const int li = lock_at(altar, 1 - ch.team);
	if (li >= 0)
	{
		// A tribute against an enemy lock becomes a basic attack on the lock when one is possible.
		return attack(c, EntityKind::altar_lock, locks[li].handle) == Err::success ? Err::success : Err::submit_altar_locked;
	}
	if (is_stunned(c)) return Err::submit_cant_channel;
	ch.channel = Channel::tribute;
	const double raw = std::ceil(settings().submit_gem_duration_multiplier * ch.gems) + settings().submit_gem_base_duration;
	ch.channel_timer = std::max(settings().submit_gem_minimum_duration, static_cast<int>(raw));
	ch.channel_target = altar;
	ch.submit_started = true;
	return Err::success;
}

Err Game::place_ward(int c, Vec2 dest, bool& ok)
{
	ok = false;
	Champion& ch = champs[c];
	if (is_stunned(c)) return Err::ward_cant_place;
	if (Err e = common_action_checks(ch); e != Err::success) return e;
	if (ch.ward_charges <= 0) return Err::ward_no_charges;
	if (!map_->in_bounds(dest) || map_->walls.test(dest) || map_->holes.test(dest) || map_->altars.test(dest) ||
		map_->spawn_mask[1 - ch.team].test(dest))
		return Err::ward_bad_destination;
	if (chebyshev(ch.pos, dest) > settings().ward_placement_radius) return Err::ward_out_of_range;
	for (const auto& w : wards)
		if (w.team == ch.team && w.pos == dest)
		{
			// An allied ward the champion cannot see behaves like a hidden occupant: success, nothing
			// placed, the tile is revealed.
			Bitboard vis;
			champion_vision(c, vis);
			if (vis.test(dest)) return Err::ward_ally_ward_present;
			if (ch.revealed_n < 8) ch.revealed[ch.revealed_n++] = dest;
			return Err::success;
		}
	bool replaced = false;
	for (auto& w : wards)
		if (w.owner == c)
		{
			w.pos = dest; // a re-placed ward keeps its slot in the ward list
			replaced = true;
		}
	if (!replaced) wards.push_back({ c, ch.team, dest });
	ch.ward_active = true;
	ch.ward_pos = dest;
	ch.ward_charges--;
	ch.ward_cooldown = settings().ward_cooldown;
	ok = true;
	return Err::success;
}

Err Game::set_priority(int c, int p)
{
	champs[c].next_priority = p;
	return Err::success;
}

Err Game::write_shared(int team, int offset, const std::uint8_t* data, int n)
{
	if (offset < 0 || n < 0 || offset + n > kSharedMemory) return Err::memory_bad_range;
	std::memcpy(teams[team].shared + offset, data, static_cast<std::size_t>(n));
	return Err::success;
}
} // namespace cbs
