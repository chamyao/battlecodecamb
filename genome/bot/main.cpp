// cambc bot running a compiled genome (genome/bot/sync.sh): the genome runtime's fixed loop over the
// same bot-side cbs::Api the policy bot uses (bot_api.cpp, engine imports; the engine meters fuel).
#include <cambc.h>
#include <cstdio>
#include <exception>
#include "bot_api.h"
#include "cbs/api.h"
#include "cbs/coro.h"
#include "genome_rt.h"

extern "C" genome::GenesBase* genome_make(genome::Ctx& X);

int main()
{
	using namespace cambc::detail;
	const int team = sdk_my_team();
	const int champ = cambc::is_draft() ? -1 : sdk_my_champion();
	auto mp = cbs::build_map_from_engine();
	static cbs::Game game(mp);
	cbs::board_rows = mp->H;
	static cbs::Api api(game, team, champ);
	api.count_charges = false;
	static cbs::Coroutine yielder;
	api.attach(&yielder);
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
