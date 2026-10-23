// Oracle bot: does a champion's bot instance (its memory) survive death and respawn?
// Prints "@@START" when main() begins and "@@T <turn counter> alive=<a>" whenever alive changes.
// Champions walk into the enemy spawn area to get killed.
#include <cambc.h>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
using namespace cambc;
using namespace cambc::detail;

static int turns = 0; // survives only if the instance does

int main()
{
	if (is_draft())
	{
		for (int i = 0;; ++i)
		{
			try { draft::pick(static_cast<champion_draft>((i + sdk_my_team() * 3) % 11)); } catch (...) {}
			end_turn();
		}
	}
	const int me = sdk_my_champion();
	std::uint32_t round{};
	sdk_bc_round_number(&round);
	std::printf("@@START champ=%d round=%u turns=%d\n", me, round, turns);
	int last_alive = -1;
	aabb enemy{};
	sdk_spawn_region(1 - sdk_my_team(), &enemy);
	for (;;)
	{
		++turns;
		champion_info ci{};
		sdk_champion(static_cast<std::uint32_t>(me), &ci);
		const int alive = ci.state & 1;
		if (alive != last_alive)
		{
			sdk_bc_round_number(&round);
			std::printf("@@T champ=%d round=%u turns=%d alive=%d\n", me, round, turns, alive);
			last_alive = alive;
		}
		if (turns % 50 == 0) std::printf("@@D champ=%d turns=%d pos=%d,%d hp=%g\n", me, turns, ci.x, ci.y, ci.health);
		if (alive)
		{
			std::uint32_t ids[16], n{};
			sdk_enemies(ids, 16, &n);
			for (std::uint32_t i = 0; i < n && i < 16; ++i)
			{
				champion_info e{};
				if (sdk_champion(ids[i], &e) == 0 && (e.state & 1) && std::max(std::abs(e.x - ci.x), std::abs(e.y - ci.y)) <= ci.attack_range)
				{
					sdk_attack(1, ids[i]);
					break;
				}
			}
			vec2 goal{ map::width() / 2, map::height() / 2 };
			for (std::uint32_t i = 0; i < n && i < 16; ++i)
			{
				champion_info e{};
				if (sdk_champion(ids[i], &e) == 0 && (e.state & 1)) { goal = { e.x, e.y }; break; }
			}
			const int sx = (goal.x > ci.x) - (goal.x < ci.x), sy = (goal.y > ci.y) - (goal.y < ci.y);
			const int cand[5][2] = { { sx, sy }, { sx, 0 }, { 0, sy }, { sx, -sy }, { -sx, sy } };
			for (auto& c : cand)
			{
				std::int32_t ok{};
				if ((c[0] || c[1]) && sdk_move_to(ci.x + c[0], ci.y + c[1], &ok) == 0 && ok) break;
			}
		}
		end_turn();
	}
}
