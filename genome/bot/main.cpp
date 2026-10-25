// cambc bot running a compiled genome (genome/bot/sync.sh): the genome runtime's fixed loop over the
// same bot-side cbs::Api the policy bot uses (bot_api.cpp, engine imports; the engine meters fuel).
#include <cambc.h>
#include <cstdio>
#include <exception>
#include <algorithm>
#include <vector>
#include "bot_api.h"
#include "cbs/api.h"
#include "cbs/coro.h"
#include "genome_rt.h"

extern "C" genome::GenesBase* genome_make(genome::Ctx& X);

int main()
{
	using namespace cambc::detail;
#ifdef GENOME_PROF
	genome::t1_mark(sdk_fuel_remaining()); // main start
#endif
	const int team = sdk_my_team();
	const int champ = cambc::is_draft() ? -1 : sdk_my_champion();
	auto mp = cbs::build_map_from_engine();
	{
		// The policy bot's map build fills each camp group's camps but not its gold / gems / respawn (bot_api.cpp);
		// genomes read gold and gems (group_gold, group_gems). Filled as the simulator does (sim/src/map.cpp).
		auto* mm = const_cast<cbs::Map*>(mp.get());
		for (auto& grp : mm->groups)
		{
			grp.gold = grp.gems = grp.respawn = 0;
			for (int c : grp.camps)
			{
				const auto& d = cbs::camp_design(mm->camps[c].type);
				grp.gold += d.gold, grp.gems += d.gems, grp.respawn = std::max(grp.respawn, d.respawn);
			}
		}
#ifdef GENOME_VERIFY_GROUPS
		// the engine's own per-group numbers (the camp layout's header), for a one-off check
		std::uint32_t nw = 0;
		sdk_map_camp_layout(nullptr, 0, &nw);
		std::vector<std::uint32_t> lay(nw);
		int bad = 0, n = 0;
		if (nw && sdk_map_camp_layout(lay.data(), nw, &nw) == 0)
			for (std::uint32_t i = 0; i + 5 <= lay.size(); i += 5 + 4 * lay[i + 4], ++n)
			{
				const auto& grp = mm->groups[lay[i]];
				bad += grp.gold != static_cast<int>(lay[i + 1]) || grp.gems != static_cast<int>(lay[i + 2]) || grp.respawn != static_cast<int>(lay[i + 3]);
			}
		if (champ >= 0) std::printf("@@VG groups %d mismatches %d\n", n, bad), std::fflush(stdout);
#endif
	}
#ifdef GENOME_PROF
	if (champ >= 0) genome::t1_mark(sdk_fuel_remaining()); // map built
#endif
	static cbs::Game game(mp);
	cbs::board_rows = mp->H;
	static cbs::Api api(game, team, champ);
	api.count_charges = false;
	static cbs::Coroutine yielder;
	api.attach(&yielder);
#ifdef GENOME_PROF
	if (champ >= 0) genome::t1_mark(sdk_fuel_remaining()); // game and Api ready
#endif
	genome::GenomePlayer player(&genome_make);
	cbs::BotBody body = player.make_bot(team, champ);
	for (;;)
	{
		try
		{
			body(api);
		}
		catch (const std::exception& e)
		{
			std::printf("bot error: %s\n", e.what());
		}
		catch (...)
		{
			std::printf("bot error: unknown exception\n");
		}
		cambc::end_turn();
	}
}
