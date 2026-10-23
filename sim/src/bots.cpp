#include "cbs/bots.h"
#include <algorithm>
#include <stdexcept>
#include <vector>

namespace cbs
{
namespace
{
struct Rng
{
	std::uint64_t s;
	std::uint32_t next(std::uint32_t n)
	{
		s ^= s << 13, s ^= s >> 7, s ^= s << 17;
		return static_cast<std::uint32_t>((s >> 11) % n);
	}
};

// One starter bot instance (state persists across its turns).
struct Starter
{
	Api& api;
	Rng rng;
	int chosen_stat = -1;
	std::vector<std::uint16_t> field;

	const Map& m() const { return api.map(); }

	void blocked_tiles(Bitboard& blocked, Vec2 me)
	{
		blocked = m().walls;
		blocked |= m().holes;
		blocked |= m().altars;
		blocked |= m().spawn_mask[1 - api.team()];
		Bitboard occ;
		api.ally_occupancy(occ);
		blocked |= occ;
		api.enemy_occupancy(occ);
		blocked |= occ;
		api.camp_occupancy(occ, 0);
		blocked |= occ;
		blocked.reset(me);
	}

	bool move_towards(Bitboard goals, Vec2 me)
	{
		Bitboard blocked, camps;
		blocked_tiles(blocked, me);
		api.camp_occupancy(camps, 0);
		if (goals.test(me)) return false;
		// Only free goals or occupied camp tiles can seed the field.
		Bitboard free_goals;
		for (int y = 0; y < m().H; ++y)
			for (int x = 0; x < m().W; ++x)
				if (goals.test(x, y) && (!blocked.test(x, y) || camps.test(x, y))) free_goals.set(x, y);
		if (!free_goals.any(m().H)) return false;
		Bitboard walls = blocked, dest, visited;
		for (int y = 0; y < m().H; ++y)
			for (int x = 0; x < m().W; ++x)
				if (free_goals.test(x, y)) walls.reset(x, y);
		dest.set(me);
		field.resize(static_cast<std::size_t>(m().W) * m().H);
		api.distance_field(walls, free_goals, &dest, kUnreachable, field.data(), visited);
		Vec2 best = me;
		std::uint16_t bd = field[m().idx(me)];
		for (int dy = -1; dy <= 1; ++dy)
			for (int dx = -1; dx <= 1; ++dx)
			{
				const Vec2 p{ me.x + dx, me.y + dy };
				if (!m().in_bounds(p) || blocked.test(p)) continue;
				if (field[m().idx(p)] < bd)
				{
					bd = field[m().idx(p)];
					best = p;
				}
			}
		if (best == me) return false;
		std::int32_t ok = 0;
		return api.move_to(best, &ok) == Err::success && ok;
	}

	bool attack_first_in_range(bool enemies, const ChampionInfo& me)
	{
		if (!(me.state & state_bit::can_attack)) return false;
		const Vec2 mp{ me.x, me.y };
		if (enemies)
		{
			std::uint32_t ids[16], n = 0;
			api.enemies(ids, 16, &n);
			for (std::uint32_t i = 0; i < n; ++i)
			{
				ChampionInfo ci{};
				if (api.champion(ids[i], &ci) != Err::success || !(ci.state & state_bit::alive)) continue;
				if (chebyshev(mp, { ci.x, ci.y }) <= me.attack_range && ci.health > 0)
					return api.attack(static_cast<std::uint32_t>(EntityKind::champion), ids[i]) == Err::success;
			}
			return false;
		}
		for (std::uint32_t c = 0; c < m().camps.size(); ++c)
		{
			const Vec2 p = m().camps[c].pos;
			if (chebyshev(mp, p) > me.attack_range) continue;
			CampRecord cr{};
			if (api.camp(c, &cr) != Err::success || cr.health <= 0) continue;
			return api.attack(static_cast<std::uint32_t>(EntityKind::camp), c) == Err::success;
		}
		return false;
	}

	void draft()
	{
		std::int32_t pick = 0;
		std::vector<int> avail;
		for (int i = 0; i < 11; ++i)
		{
			bool used = false;
			for (std::uint32_t r = 0; r < 6; ++r)
				if (api.draft_get(api.team(), r, &pick) == Err::success && pick == i) used = true;
			if (!used) avail.push_back(i);
		}
		const char msg[] = "hello world";
		api.submit_draft_memory(reinterpret_cast<const std::uint8_t*>(msg), 11);
		api.draft_champion(avail[rng.next(static_cast<std::uint32_t>(avail.size()))]);
	}

	void turn()
	{
		if (chosen_stat < 0) chosen_stat = static_cast<int>(rng.next(3));
		std::uint8_t mem[4];
		api.read_shared_memory(0, mem, 4);
		std::uint32_t round = 0;
		api.round_number(&round);
		api.write_shared_memory(0, reinterpret_cast<const std::uint8_t*>(&round), 4);

		const std::uint32_t self = static_cast<std::uint32_t>(api.my_champion());
		ChampionInfo me{};
		api.champion(self, &me);
		const std::uint32_t st = me.state;
		if (!(st & state_bit::alive) || (st & (state_bit::recalling | state_bit::submitting | state_bit::teleporting)) ||
			(!(st & state_bit::can_move) && !(st & state_bit::can_attack)))
			return;
		const Vec2 pos{ me.x, me.y };
		const bool at_spawn = m().spawn[api.team()].contains(pos);
		if (at_spawn)
		{
			const int item = 6 + 2 * chosen_stat; // power shard of strength / focus / health
			std::uint32_t gold = 0;
			api.champion_gold(self, &gold);
			const std::uint32_t n = gold / 30;
			if (n) api.buy_item(static_cast<std::uint32_t>(item), n);
		}
		if (!at_spawn && me.health < me.max_health * 0.35f)
		{
			api.recall();
			return;
		}
		if (attack_first_in_range(true, me)) return;
		std::uint32_t gems = 0;
		api.champion_gems(self, &gems);
		AltarLockRecord locks[16];
		std::uint32_t nl = 0;
		api.altar_locks(locks, 16, &nl);
		auto locked = [&](Vec2 a) {
			for (std::uint32_t i = 0; i < nl && i < 16; ++i)
				if (locks[i].x == a.x && locks[i].y == a.y) return true;
			return false;
		};
		if (gems > 0)
		{
			Bitboard goals;
			for (Vec2 a : m().altar_list)
			{
				if (locked(a)) continue;
				if (chebyshev(pos, a) <= settings().submit_gems_range)
				{
					api.submit_gems(a);
					return;
				}
				draw_chebyshev(goals, m().W, m().H, a, static_cast<float>(settings().submit_gems_range));
			}
			move_towards(goals, pos);
			return;
		}
		if (attack_first_in_range(false, me)) return;
		Bitboard goals;
		for (std::size_t g = 0; g < m().groups.size(); ++g)
		{
			std::uint32_t gs = 0;
			api.camp_group_state(static_cast<std::uint32_t>(g), &gs);
			if (gs == static_cast<std::uint32_t>(GroupState::respawning)) continue;
			for (int c : m().groups[g].camps) goals.set(m().camps[c].pos);
		}
		if (move_towards(goals, pos))
		{
			api.champion(self, &me);
			attack_first_in_range(false, me);
		}
		api.set_priority(1 + static_cast<std::int32_t>(rng.next(100)));
	}
};

class StarterPlayer : public Player
{
public:
	explicit StarterPlayer(std::uint64_t seed) : seed_(seed) {}
	BotBody make_bot(int team, int champ) override
	{
		const std::uint64_t s = (seed_ * 0x9E3779B97F4A7C15ull) ^ (static_cast<std::uint64_t>(team) << 32) ^ static_cast<std::uint64_t>(champ + 7) * 0xBF58476D1CE4E5B9ull;
		return [s](Api& api) {
			Starter bot{ api, Rng{ s | 1 }, -1, {} };
			for (;;)
			{
				if (bot.api.champ() < 0) bot.draft();
				else bot.turn();
				api.end_turn();
			}
		};
	}

private:
	std::uint64_t seed_;
};

class IdlePlayer : public Player
{
public:
	BotBody make_bot(int, int) override
	{
		return [](Api& api) {
			for (;;) api.end_turn();
		};
	}
};
} // namespace

std::unique_ptr<Player> make_starter_player(std::uint64_t seed) { return std::make_unique<StarterPlayer>(seed); }
std::unique_ptr<Player> make_idle_player() { return std::make_unique<IdlePlayer>(); }
std::unique_ptr<Player> make_player(const std::string& name, std::uint64_t seed)
{
	if (name == "starter") return make_starter_player(seed);
	if (name == "idle") return make_idle_player();
	throw std::invalid_argument("unknown player: " + name);
}
} // namespace cbs
